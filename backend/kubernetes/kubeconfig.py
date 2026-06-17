from loguru import logger

from kubernetes.kubectl import run


def list_contexts() -> dict:
    """
    Return all contexts from the active kubeconfig using kubectl config view.
    Uses ignore_context=True so --context is never appended to a config command.
    """
    result = run(["config", "view"], as_json=True, ignore_context=True)

    if not result.success:
        stderr = result.stderr.lower()
        if "not found in path" in stderr:
            return {
                "error": "kubectl is not installed or not in PATH.",
                "contexts": [],
                "current_context": None,
            }
        return {
            "error": f"Failed to read kubeconfig: {result.stderr.strip()}",
            "contexts": [],
            "current_context": None,
        }

    data = result.data
    current_context = data.get("current-context", "")

    # Build a server lookup map from clusters list
    clusters_by_name: dict[str, dict] = {
        c["name"]: c.get("cluster", {})
        for c in data.get("clusters", [])
        if isinstance(c, dict)
    }

    contexts = []
    for ctx in data.get("contexts", []):
        if not isinstance(ctx, dict):
            continue
        name = ctx.get("name", "")
        ctx_detail = ctx.get("context", {})
        cluster_name = ctx_detail.get("cluster", "")
        cluster_info = clusters_by_name.get(cluster_name, {})
        server = cluster_info.get("server", "")

        contexts.append(
            {
                "name": name,
                "cluster": cluster_name,
                "server": server,
                "is_current": name == current_context,
            }
        )

    logger.info(f"Found {len(contexts)} kubeconfig context(s). Current: {current_context!r}")
    return {
        "contexts": contexts,
        "current_context": current_context,
    }


def classify_kubectl_error(stderr: str) -> str:
    """Return a beginner-friendly error message for common kubectl failures."""
    s = stderr.lower()

    if "not found in path" in s or "executable file not found" in s:
        return (
            "kubectl is not installed or not in your PATH.\n"
            "Install kubectl: https://kubernetes.io/docs/tasks/tools/"
        )
    if "no configuration has been provided" in s or "no config" in s:
        return (
            "No kubeconfig found.\n"
            "Run 'kubectl config view' to verify your config,\n"
            "or set KUBECONFIG_PATH in the backend .env file."
        )
    if "context" in s and ("not found" in s or "does not exist" in s):
        return (
            "The selected Kubernetes context was not found in your kubeconfig.\n"
            "Choose a different context from the cluster list."
        )
    if any(x in s for x in ("unable to connect", "connection refused", "deadline exceeded", "no route to host", "i/o timeout")):
        return (
            "Cannot reach the Kubernetes cluster.\n"
            "Verify:\n"
            "  • The cluster is running\n"
            "  • Your VPN / network access is active\n"
            "  • The kubeconfig server address is correct"
        )
    if "unauthorized" in s or "forbidden" in s:
        return (
            "Kubernetes access denied.\n"
            "Check that your kubeconfig credentials are valid and\n"
            "you have the required RBAC permissions."
        )
    if "timed out" in s:
        return (
            "kubectl command timed out.\n"
            "The cluster may be overloaded or unreachable."
        )

    return f"kubectl error: {stderr.strip()[:300]}"
