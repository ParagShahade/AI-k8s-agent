import json

SYSTEM_PROMPT = """You are a Senior Kubernetes SRE with deep expertise in Kubernetes operations, \
debugging, and production incident response.

You will receive structured evidence collected from a Kubernetes cluster investigation.
Your job is to analyze the evidence, identify the root cause of any failures, and provide \
a clear, actionable diagnosis.

Always respond with a valid JSON object — no markdown, no code fences, just raw JSON.
Use exactly this structure:
{
  "root_cause": "concise one-sentence root cause",
  "explanation": "2-4 sentences explaining what is failing and why",
  "fix": "step-by-step human-readable fix",
  "kubectl_commands": ["kubectl command 1", "kubectl command 2"],
  "prevention": "one or two sentences on how to prevent this in the future",
  "confidence": 85
}

Rules:
- confidence is an integer 0–100 based on how much evidence supports your conclusion
- kubectl_commands is an array of specific, runnable commands — never placeholders
- If the cluster appears healthy or evidence is insufficient, say so clearly in root_cause
- Focus on the primary root cause — do not list every minor warning
- Be specific to the failing workloads, not generic Kubernetes advice
"""


def build_user_prompt(investigation: dict) -> str:
    pods = investigation.get("pods", {})
    logs = investigation.get("logs", {})
    events = investigation.get("events", {})
    deployments = investigation.get("deployments", {})
    network = investigation.get("network", {})

    sections = []

    # Pods
    sections.append("=== POD STATUS ===")
    if "error" in pods:
        sections.append(f"kubectl unavailable: {pods['error']}")
    else:
        sections.append(f"Total pods: {pods.get('total_pods', 0)}")
        sections.append(f"Problematic pods: {pods.get('problematic_pod_count', 0)}")
        for p in pods.get("problematic_pods", []):
            sections.append(
                f"  - {p['namespace']}/{p['name']}: {p['status']}"
                + (f" (restarts: {p['restart_count']})" if p.get("restart_count") else "")
                + (f" — {p['message']}" if p.get("message") else "")
            )

    # Logs
    sections.append("\n=== LOGS (relevant lines) ===")
    if not logs:
        sections.append("No logs collected.")
    for pod_key, log_data in logs.items():
        sections.append(f"[{pod_key}]")
        if not log_data.get("available"):
            sections.append("  No logs available.")
        else:
            relevant = log_data.get("relevant_lines", [])
            if relevant:
                for line in relevant[-20:]:
                    sections.append(f"  {line}")
            else:
                for line in log_data.get("lines", [])[-10:]:
                    sections.append(f"  {line}")

    # Events
    sections.append("\n=== KUBERNETES EVENTS (warnings) ===")
    if "error" in events:
        sections.append(f"kubectl unavailable: {events['error']}")
    elif not events.get("warnings"):
        sections.append("No warning events.")
    else:
        for e in events.get("warnings", [])[:15]:
            sections.append(
                f"  [{e['namespace']}] {e['reason']} on {e['object_kind']}/{e['object_name']}"
                f" (x{e.get('count', 1)}): {e['message']}"
            )

    # Deployments
    sections.append("\n=== DEPLOYMENT HEALTH ===")
    if "error" in deployments:
        sections.append(f"kubectl unavailable: {deployments['error']}")
    else:
        sections.append(f"Total deployments: {deployments.get('total_deployments', 0)}")
        for d in deployments.get("unhealthy_deployments", []):
            sections.append(
                f"  - {d['namespace']}/{d['name']}: "
                f"desired={d['desired_replicas']} ready={d['ready_replicas']} "
                f"unavailable={d['unavailable_replicas']}"
            )
            for c in d.get("failed_conditions", []):
                sections.append(f"    Condition {c['type']} failed: {c['message']}")

    # Network
    sections.append("\n=== NETWORK / SERVICES ===")
    if not network.get("issues"):
        sections.append("No networking issues detected.")
    else:
        for issue in network.get("issues", []):
            sections.append(
                f"  - {issue['namespace']}/{issue['service']} ({issue['type']}): {issue['issue']}"
            )

    return "\n".join(sections)
