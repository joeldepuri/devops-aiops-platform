# Claude Code + MCP Server Setup

This guide walks through installing **Claude Code** and wiring up the **MCP (Model Context Protocol) servers** used throughout this project. The goal is to let Claude help you read files, fetch GitHub issues/PRs, work with AWS, Terraform, and Kubernetes — all from inside your editor.

> If you already have Claude Code installed and configured, you only need the **MCP Servers** section below.

---

## 1. Install Claude Code

Claude Code is the CLI tool that lets you delegate coding tasks to Claude from your terminal.

```bash
# macOS / Linux
curl -fsSL https://claude.ai/install.sh | bash

# or via npm
npm install -g @anthropic-ai/claude-code
```

Then authenticate:

```bash
claude login
```

Verify it's working:

```bash
claude --version
```

---

## 2. Open the project

From this folder, launch Claude Code:

```bash
claude
```

Claude will automatically pick up:

- `CLAUDE.md` — project-wide instructions for the assistant
- `.claude/settings.json` — permissions, allowed tools, model preferences
- `.mcp.json` — MCP servers loaded at startup

---

## 3. MCP Servers

This project ships with `.mcp.json` preconfigured. The servers below are used across Parts 1–4.

### Filesystem MCP

Lets Claude read and write files in this directory. Configured by default.

```json
"filesystem": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
}
```

No setup needed — just works on first launch.

---

### GitHub MCP

Lets Claude read repos, issues, PRs, and Actions runs.

1. Create a fine-grained personal access token at <https://github.com/settings/tokens>
   - Scopes: `repo`, `read:org`, `workflow`
2. Export it before launching Claude:

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxxxxxxxxx"
```

Or add it to a local `.env` file (which is already in `.gitignore`).

---

### AWS MCP

Used in Parts 3 & 4 for EKS, Bedrock, CloudWatch, and Fluent Bit log inspection.

1. Install the AWS CLI and configure credentials:

```bash
aws configure
```

2. Make sure your IAM user / role has permissions for:
   - `eks:*` (read-only at minimum)
   - `bedrock:*`
   - `logs:Describe*`, `logs:Get*`, `logs:Filter*`
   - `s3:Get*`, `s3:List*`
3. Set the region you'll be working in:

```bash
export AWS_REGION="us-east-1"
```

---

### Terraform MCP

Helps Claude read your `.tf` files and explain plan output.

No credentials needed — but make sure Terraform itself is installed:

```bash
terraform --version    # should be >= 1.5
```

---

### Kubernetes MCP

Used in Part 3 once your EKS cluster is up.

1. Configure `kubectl` to point at your EKS cluster:

```bash
aws eks update-kubeconfig --region us-east-1 --name <your-cluster-name>
```

2. Verify access:

```bash
kubectl get nodes
```

The MCP server will use the **current kubeconfig context**, so always check `kubectl config current-context` before running cluster-level prompts through Claude.

---

## 4. Sanity check

Inside Claude Code, run:

```
/mcp
```

You should see all configured MCP servers listed as `connected`. If any show `error`, scroll up — Claude prints the failure reason (most often a missing env var or auth issue).

---

## 5. Safety note

The root `CLAUDE.md` puts Claude into **safe execution mode**. That means before running any command, Claude will briefly explain *what* it's about to do and *why* — read those messages, especially before approving anything that touches AWS, Kubernetes, or your filesystem.

You can always interrupt with `Esc` and ask for a different approach.

---

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| `mcp server failed to start` | Missing `npx` / Node.js — install Node 20+ |
| `github MCP: 401 Unauthorized` | Token expired or wrong scopes |
| `aws MCP: NoCredentialsError` | Run `aws configure` or export `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` |
| `kubernetes MCP: connection refused` | Kubeconfig not pointing at a running cluster |

---

Next: open [`docs/part1-system-design.md`](./part1-system-design.md) to start Part 1.
