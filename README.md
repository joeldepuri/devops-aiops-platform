# DevOps + AIOps Series

> A full end-to-end DevOps project with AIOps integration — so you can connect the dots between how AI is helping automate DevOps tasks today.

---

## Welcome

Hey everyone!

Welcome to my DevOps + AI series where we build an end-to-end DevOps project with an AIOps integration.

A lot of you have been asking: *"when are you going to share a full DevOps project?"*

Well — here we are.

In this series we will:

- Build microservices locally
- Use Claude and AI tools to assist development
- Deploy everything step by step
- Migrate the system to the cloud on AWS EKS
- Set up a full CI/CD pipeline with GitHub Actions
- Implement GitOps workflows with ArgoCD + ArgoCD Image Updater
- Integrate AIOps capabilities with AWS Bedrock (Jimmy — Runbook Automation Agent)

By the end of this series, you won't just know tools — you'll understand how real DevOps systems are designed and deployed.

---

## What's New

### ArgoCD Image Updater (Automated GitOps Loop)

The GitOps workflow has been upgraded with **ArgoCD Image Updater**. Previously, CI pushed new images to ECR and then manually committed updated image tags back to Git. Now:

1. CI builds and pushes images to ECR as before
2. **ArgoCD Image Updater** polls ECR every 2 minutes per service, detects the newest image digest using the `newest-build` strategy
3. When a new image is found, it **automatically writes the updated image reference back to the `project-demo` branch** in Git
4. ArgoCD detects the Git change and syncs the cluster — no human interaction needed

This closes the full GitOps loop:

```
Code Push → GitHub Actions CI → ECR (new image)
                                      │
                               ArgoCD Image Updater
                               polls ECR every 2 min
                                      │
                               Writes image digest → Git (project-demo)
                                      │
                               ArgoCD detects Git change
                                      │
                               Syncs EKS cluster automatically
```

### Jimmy — AIOps Runbook Automation Agent

The AIOps layer has been rebuilt from the ground up. The original reference agent **Kira** (by Vishakha Sadhwani) was a diagnostic assistant: it queried logs, metrics, and cluster health on demand to help identify root causes.

**Jimmy** goes further — from diagnosis to autonomous remediation:

| Capability | Kira (original reference) | Jimmy (this project) |
|---|---|---|
| Log analysis | ✅ fetch_logs | ✅ fetch_logs |
| Metrics query | ✅ fetch_metrics | ✅ fetch_metrics |
| Cluster health | ✅ fetch_health | ✅ fetch_service_health |
| Runbook lookup | ❌ | ✅ fetch_runbook (S3) |
| Pod restart | ❌ | ✅ restart_pod |
| Scale deployment | ❌ | ✅ scale_deployment |
| Email notification | ❌ | ✅ send_incident_report (SNS) |
| Automated detection | ❌ | ✅ EventBridge every 5 min |

Jimmy's 7-step runbook automation workflow:

```
1. ASSESS    → fetch_service_health (identify unhealthy pods/nodes)
2. DIAGNOSE  → fetch_logs + fetch_metrics (error pattern + spike)
3. CLASSIFY  → determine incident type
4. RUNBOOK   → fetch_runbook from S3 (read before acting)
5. REMEDIATE → restart_pod or scale_deployment per runbook
6. VERIFY    → fetch_service_health again (confirm fix)
7. REPORT    → send_incident_report via SNS → Gmail
```

Jimmy detects 7 incident types automatically:

1. **CrashLoopBackOff** — container crash-restarting
2. **OOMKilled** — container killed by memory limit
3. **ImagePullBackOff** — cannot pull container image
4. **Readiness Probe Failure** — pod Running but 0/1 Ready
5. **High Restart Count** — pod recovered but restarted > 5 times
6. **Pending Too Long** — pod stuck Pending > 5 minutes
7. **Service No Endpoints** — deployment has 0 available replicas

---

## Repository Structure

```
DevOps-AIOps-Platform/
├── docs/
│   ├── part1-system-design.md     # System design foundations (Part 1)
│   ├── part2-workflow.md          # Full workflow with AIOps (Part 2)
│   └── claude-setup.md            # Claude Code + MCP server setup
├── projects/
│   ├── README.md                  # EKS deployment guide (Part 3)
│   ├── boutique-microservices/    # The application (7 services)
│   ├── Infrastructure/            # Terraform for AWS provisioning
│   └── aiops-assistant/           # Jimmy — Runbook Automation Agent (Part 4)
│       ├── app.py                 # Streamlit chat UI
│       ├── deploy.sh              # Full agent deployment (8 Lambdas + Bedrock)
│       ├── setup-iam.sh           # IAM roles setup
│       ├── lambda/
│       │   ├── fetch_logs/        # CloudWatch Logs query
│       │   ├── fetch_metrics/     # Prometheus metrics query
│       │   ├── fetch_health/      # EKS cluster/pod health
│       │   ├── fetch_runbook/     # S3 runbook retrieval
│       │   ├── restart_pod/       # Kubernetes pod restart
│       │   ├── scale_deployment/  # Kubernetes replica scaling
│       │   ├── send_incident_report/ # SNS email notification
│       │   └── incident_detector/ # EventBridge automated scanner
│       ├── runbooks/              # 8 runbooks (Markdown → S3)
│       └── schemas/               # OpenAPI schemas for all 7 action groups
├── gitops/
│   ├── argo-cd.yml                # ArgoCD Application + Image Updater annotations
│   ├── kustomization.yml          # Kustomize entry point
│   └── k8s/                       # All Kubernetes manifests
└── .github/
    └── workflows/ci.yml           # GitHub Actions CI pipeline
```

---

## Series Structure

### Part 1 — System Design Foundations

`docs/part1-system-design.md`

We start with system design concepts specifically for cloud and DevOps. This is important whether you're a beginner, intermediate, or senior engineer — because companies don't choose tools randomly. They think about architecture patterns, deployment strategies, scalability, reliability, and cost tradeoffs.

We cover 12 core system design pillars used in modern DevOps architectures, and connect each one directly to something running in this project.

---

### Part 2 — Understanding the Workflow

`docs/part2-workflow.md`

Before writing any code or deployment configs, you need to understand how the entire system flows:

- What services we're building and how they communicate
- How the pipeline works
- How code moves from developer → CI → deployment → production → AIOps

This is where the full picture comes together — including how AI fits into the workflow.

---

### Part 3 — DevOps Project Implementation

`projects/README.md`

Then we actually build the project. You'll see:

- Docker containers and Docker Compose
- Kubernetes deployments on EKS
- CI/CD pipelines with GitHub Actions
- GitOps automation with ArgoCD + ArgoCD Image Updater
- Infrastructure provisioning with Terraform
- Observability with Prometheus and Grafana

---

### Part 4 — AIOps Integration: Jimmy

`projects/aiops-assistant/README.md`

The AIOps layer is built with **Jimmy**, a Bedrock Agent that automates incident response end-to-end. Jimmy goes beyond analysis — it looks up the right runbook for each incident type, executes the remediation steps, and sends a structured email report with root cause, actions taken, and resolution status.

What Jimmy does:

- **Automated detection** — an EventBridge-triggered Lambda scans the EKS cluster every 5 minutes for 7 incident types
- **Runbook lookup** — retrieves the correct Markdown runbook from S3 before taking any action
- **Autonomous remediation** — restarts pods or scales deployments as directed by the runbook
- **Email reporting** — publishes a structured incident report via SNS → Gmail on every incident
- **Open-ended Q&A** — because Jimmy is powered by **Claude 3.5 Haiku via AWS Bedrock**, you can ask him anything through the Streamlit UI. The 7 incident types are what the automated scanner watches for — they are not a ceiling on what you can ask. Jimmy answers any Kubernetes or DevOps question about the platform (PromQL, debugging, architecture), and since Claude is the model underneath, it can answer general questions outside DevOps as well — it will just respond in its SRE persona

Because modern DevOps is no longer just automation — it's **automation + intelligence + self-healing**.

---

## Bonus Challenge

You'll get access to this entire repository.

But there's a catch.

The repository includes **intentional issues and troubleshooting tasks**.

Why? Because AI has made things easier. But if you want to grow as an engineer, you must learn how to break systems, debug systems, and fix systems.

Once you implement the project:

1. Fork the repository
2. Deploy the system
3. Troubleshoot the issues
4. Share what you learned — and tag me so I know you're building along

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Application | React, Node.js, PostgreSQL |
| Containers | Docker, Docker Compose |
| Orchestration | Kubernetes (AWS EKS) |
| Infrastructure | Terraform |
| CI/CD | GitHub Actions |
| GitOps | ArgoCD + Kustomize |
| Image Automation | ArgoCD Image Updater (ECR → Git → EKS) |
| Monitoring | Prometheus + Grafana |
| Log Forwarding | AWS Fluent Bit → CloudWatch |
| AIOps | Jimmy — AWS Bedrock Agent (Runbook Automation) |
| AI Assistant | Claude Code + MCP Servers |

---

## Full Automation Flow

```
Developer pushes code
        │
        ▼
GitHub Actions CI
  - Builds 7 Docker images in parallel
  - Pushes to ECR
        │
        ▼
ArgoCD Image Updater
  - Polls ECR every 2 min (newest-build strategy)
  - Commits updated image digests to project-demo branch
        │
        ▼
ArgoCD (GitOps)
  - Detects Git change → syncs EKS cluster
  - selfHeal: true — reverts manual drift
  - prune: true — removes deleted resources
        │
        ▼
EKS Cluster (boutique namespace)
  - Prometheus scrapes /metrics every 15s
  - Grafana dashboards show live state
        │
        ▼
EventBridge (every 5 min)
  - Triggers Jimmy's incident_detector Lambda
  - Scans all pods for 7 incident types
        │
   Incident found?
        │
        ▼
Jimmy (AWS Bedrock Agent)
  - Fetch runbook from S3
  - Restart pod or scale deployment
  - Verify fix
  - Send email via SNS → Gmail
```

---

## Reference

Based on the tutorial repository by **Vishakha Sadhwani**: <https://github.com/vishakhasadhwani/devops-ai-playbook>
