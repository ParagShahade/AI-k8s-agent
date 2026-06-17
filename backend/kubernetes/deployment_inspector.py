from loguru import logger

from kubernetes.kubectl import run


def inspect_deployments(namespace: str = "all") -> dict:
    """
    Inspect all deployments and flag ones with unavailable or mismatched replicas.
    """
    args = ["get", "deployments", "-A"] if namespace == "all" else ["get", "deployments", "-n", namespace]
    result = run(args, as_json=True)

    if not result.success:
        logger.warning(f"Deployment inspection failed: {result.stderr}")
        return {"error": result.stderr, "healthy": False, "unhealthy_deployments": [], "total_deployments": 0}

    items = result.data.get("items", [])
    unhealthy = []
    total = len(items)

    for dep in items:
        name = dep.get("metadata", {}).get("name", "unknown")
        ns = dep.get("metadata", {}).get("namespace", "unknown")
        spec = dep.get("spec", {})
        status = dep.get("status", {})

        desired = spec.get("replicas", 1)
        ready = status.get("readyReplicas", 0)
        available = status.get("availableReplicas", 0)
        unavailable = status.get("unavailableReplicas", 0)

        conditions = status.get("conditions", [])
        failed_conditions = [
            {
                "type": c.get("type"),
                "reason": c.get("reason", ""),
                "message": c.get("message", ""),
            }
            for c in conditions
            if c.get("status") == "False"
        ]

        is_unhealthy = (
            unavailable > 0
            or ready < desired
            or len(failed_conditions) > 0
        )

        if is_unhealthy:
            unhealthy.append({
                "name": name,
                "namespace": ns,
                "desired_replicas": desired,
                "ready_replicas": ready,
                "available_replicas": available,
                "unavailable_replicas": unavailable,
                "failed_conditions": failed_conditions,
            })

    healthy = len(unhealthy) == 0
    logger.info(f"Deployment inspection: {total} total, {len(unhealthy)} unhealthy")

    return {
        "healthy": healthy,
        "total_deployments": total,
        "unhealthy_count": len(unhealthy),
        "unhealthy_deployments": unhealthy,
    }
