"""
Scheduled Lambda — runs every 5 minutes via EventBridge.
Detects unhealthy pods in the boutique namespace and invokes
the Jimmy Bedrock agent to classify, remediate, and report.
"""
import boto3
import json
import os
import ssl
import uuid
import urllib.request
import base64
from botocore.auth import SigV4QueryAuth
from botocore.awsrequest import AWSRequest

REGION            = os.environ.get("AWS_REGION", "us-east-1")
CLUSTER_NAME      = os.environ.get("EKS_CLUSTER_NAME", "eks-cluster")
NAMESPACE         = os.environ.get("K8S_NAMESPACE", "boutique")
BEDROCK_AGENT_ID  = os.environ.get("BEDROCK_AGENT_ID", "")
BEDROCK_ALIAS_ID  = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "TSTALIASID")

UNHEALTHY_REASONS = {"CrashLoopBackOff", "OOMKilled", "Error", "ImagePullBackOff", "ErrImagePull", "OOMKill"}


def get_eks_token(cluster_name, region):
    session = boto3.session.Session()
    creds = session.get_credentials().get_frozen_credentials()
    url = f"https://sts.{region}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15"
    req = AWSRequest(method="GET", url=url, headers={"x-k8s-aws-id": cluster_name})
    SigV4QueryAuth(creds, "sts", region, expires=60).add_auth(req)
    return "k8s-aws-v1." + base64.urlsafe_b64encode(req.url.encode()).decode().rstrip("=")


def get_cluster_endpoint(cluster_name, region):
    eks = boto3.client("eks", region_name=region)
    return eks.describe_cluster(name=cluster_name)["cluster"]["endpoint"]


def list_pods(endpoint, token, namespace):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        f"{endpoint}/api/v1/namespaces/{namespace}/pods",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        return json.loads(resp.read())


def detect_incidents():
    try:
        endpoint = get_cluster_endpoint(CLUSTER_NAME, REGION)
        token    = get_eks_token(CLUSTER_NAME, REGION)
        pods     = list_pods(endpoint, token, NAMESPACE)
    except Exception as e:
        return [{"type": "api-error", "message": str(e), "namespace": NAMESPACE}]

    incidents = []
    for pod in pods.get("items", []):
        pod_name = pod["metadata"]["name"]
        all_statuses = (
            pod["status"].get("containerStatuses", []) +
            pod["status"].get("initContainerStatuses", [])
        )
        for cs in all_statuses:
            waiting    = cs.get("state", {}).get("waiting", {})
            terminated = cs.get("state", {}).get("terminated", {})
            reason     = waiting.get("reason") or terminated.get("reason", "")
            restarts   = cs.get("restartCount", 0)

            if reason in UNHEALTHY_REASONS:
                itype = (
                    "pod-crashloop" if reason == "CrashLoopBackOff" else
                    "oom-killed"    if "OOM" in reason else
                    "image-pull-error"
                )
                incidents.append({
                    "type":      itype,
                    "pod":       pod_name,
                    "container": cs["name"],
                    "reason":    reason,
                    "restarts":  restarts,
                    "namespace": NAMESPACE,
                })
    return incidents


def invoke_jimmy(incidents):
    lines = "\n".join(
        f"- Pod '{i['pod']}' (container: {i.get('container','n/a')}) → {i['reason']} "
        f"({i.get('restarts',0)} restarts)"
        for i in incidents
    )
    prompt = (
        f"AUTOMATED INCIDENT ALERT — {len(incidents)} incident(s) detected in "
        f"cluster '{CLUSTER_NAME}', namespace '{NAMESPACE}':\n\n{lines}\n\n"
        "Please: (1) fetch_service_health to confirm, (2) fetch_runbook for each incident type, "
        "(3) execute restart_pod or scale_deployment per the runbook, "
        "(4) verify health again, (5) send_incident_report with full summary."
    )
    client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    resp   = client.invoke_agent(
        agentId=BEDROCK_AGENT_ID,
        agentAliasId=BEDROCK_ALIAS_ID,
        sessionId=str(uuid.uuid4()),
        inputText=prompt,
    )
    output = ""
    for event in resp["completion"]:
        if "chunk" in event and "bytes" in event["chunk"]:
            output += event["chunk"]["bytes"].decode("utf-8")
    return output


def lambda_handler(event, context):
    incidents = detect_incidents()

    if not incidents:
        return {"statusCode": 200, "body": json.dumps({"status": "healthy"})}

    agent_response = "Agent not configured — set BEDROCK_AGENT_ID env var"
    if BEDROCK_AGENT_ID:
        try:
            agent_response = invoke_jimmy(incidents)
        except Exception as e:
            agent_response = f"Error invoking Jimmy: {e}"

    return {
        "statusCode": 200,
        "body": json.dumps({
            "status":    "incidents_detected",
            "count":     len(incidents),
            "incidents": incidents,
            "jimmy_response": agent_response[:1000],
        }),
    }
