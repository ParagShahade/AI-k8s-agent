from loguru import logger

from kubernetes.kubectl import WARNING_REASONS, run


def analyze_events(namespace: str = "all") -> dict:
    """
    Fetch Kubernetes events and surface Warning-level events with known problem reasons.
    """
    args = ["get", "events", "-A"] if namespace == "all" else ["get", "events", "-n", namespace]
    result = run(args, as_json=True)

    if not result.success:
        logger.warning(f"Events fetch failed: {result.stderr}")
        return {"error": result.stderr, "warning_count": 0, "warnings": []}

    items = result.data.get("items", [])
    warnings = []

    for event in items:
        event_type = event.get("type", "Normal")
        reason = event.get("reason", "")

        if event_type != "Warning" and reason not in WARNING_REASONS:
            continue

        involved = event.get("involvedObject", {})
        warnings.append({
            "namespace": event.get("metadata", {}).get("namespace", "unknown"),
            "reason": reason,
            "message": event.get("message", ""),
            "object_kind": involved.get("kind", ""),
            "object_name": involved.get("name", ""),
            "count": event.get("count", 1),
            "last_seen": event.get("lastTimestamp") or event.get("eventTime", ""),
        })

    warnings.sort(key=lambda e: e.get("count", 1), reverse=True)

    logger.info(f"Events analysis: {len(warnings)} warning events found")

    return {
        "total_events": len(items),
        "warning_count": len(warnings),
        "warnings": warnings,
    }
