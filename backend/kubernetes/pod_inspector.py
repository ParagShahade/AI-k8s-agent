from loguru import logger

from kubernetes.kubectl import UNHEALTHY_STATUSES, run


def inspect_pods(namespace: str = "all") -> dict:
    """
    Fetch all pods and classify them as healthy or problematic.
    Returns a structured summary with details on any unhealthy pods.
    """
    args = ["get", "pods", "-A"] if namespace == "all" else ["get", "pods", "-n", namespace]
    result = run(args, as_json=True)

    if not result.success:
        logger.warning(f"Pod inspection failed: {result.stderr}")
        return {"error": result.stderr, "healthy": False, "problematic_pods": [], "total_pods": 0}

    items = result.data.get("items", [])
    problematic_pods = []
    total_pods = len(items)

    for pod in items:
        name = pod.get("metadata", {}).get("name", "unknown")
        ns = pod.get("metadata", {}).get("namespace", "unknown")
        phase = pod.get("status", {}).get("phase", "Unknown")
        container_statuses = pod.get("status", {}).get("containerStatuses", [])
        init_statuses = pod.get("status", {}).get("initContainerStatuses", [])

        problem = _detect_problem(phase, container_statuses + init_statuses)
        if problem:
            problematic_pods.append({
                "name": name,
                "namespace": ns,
                "phase": phase,
                "status": problem["reason"],
                "message": problem.get("message", ""),
                "container": problem.get("container", ""),
                "restart_count": problem.get("restart_count", 0),
            })

    healthy = len(problematic_pods) == 0
    logger.info(f"Pod inspection: {total_pods} total, {len(problematic_pods)} problematic")

    return {
        "healthy": healthy,
        "total_pods": total_pods,
        "problematic_pod_count": len(problematic_pods),
        "problematic_pods": problematic_pods,
    }


def _detect_problem(phase: str, container_statuses: list) -> dict | None:
    for cs in container_statuses:
        container_name = cs.get("name", "")
        restart_count = cs.get("restartCount", 0)

        waiting = cs.get("state", {}).get("waiting", {})
        terminated = cs.get("state", {}).get("terminated", {})

        if waiting:
            reason = waiting.get("reason", "")
            if reason in UNHEALTHY_STATUSES:
                return {
                    "reason": reason,
                    "message": waiting.get("message", ""),
                    "container": container_name,
                    "restart_count": restart_count,
                }

        if terminated:
            reason = terminated.get("reason", "")
            if reason in UNHEALTHY_STATUSES:
                return {
                    "reason": reason,
                    "message": terminated.get("message", ""),
                    "container": container_name,
                    "restart_count": restart_count,
                }

    if phase in ("Failed", "Unknown"):
        return {"reason": phase, "message": "", "container": "", "restart_count": 0}

    return None
