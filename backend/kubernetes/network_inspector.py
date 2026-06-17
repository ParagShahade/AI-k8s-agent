from loguru import logger

from kubernetes.kubectl import run


def inspect_network(namespace: str = "all") -> dict:
    """
    Inspect services and endpoints to detect selector mismatches and missing endpoints.
    """
    svc_result = _get_services(namespace)
    ep_result = _get_endpoints(namespace)

    services = svc_result.get("services", [])
    endpoints_map = ep_result.get("endpoints_map", {})
    issues = []

    for svc in services:
        ns = svc["namespace"]
        name = svc["name"]
        svc_type = svc["type"]

        # ExternalName and headless services don't need endpoints
        if svc_type == "ExternalName":
            continue

        ep_key = f"{ns}/{name}"
        ep = endpoints_map.get(ep_key, {})
        addresses = ep.get("addresses", [])

        if not addresses and name != "kubernetes":
            issues.append({
                "namespace": ns,
                "service": name,
                "type": svc_type,
                "issue": "No endpoints found — possible selector mismatch or no matching pods",
                "selector": svc.get("selector", {}),
            })

    logger.info(f"Network inspection: {len(services)} services, {len(issues)} issues found")

    return {
        "total_services": len(services),
        "issue_count": len(issues),
        "issues": issues,
        "services": services,
    }


def _get_services(namespace: str) -> dict:
    args = ["get", "svc", "-A"] if namespace == "all" else ["get", "svc", "-n", namespace]
    result = run(args, as_json=True)

    if not result.success:
        logger.warning(f"Service fetch failed: {result.stderr}")
        return {"services": []}

    services = []
    for svc in result.data.get("items", []):
        spec = svc.get("spec", {})
        services.append({
            "name": svc.get("metadata", {}).get("name", "unknown"),
            "namespace": svc.get("metadata", {}).get("namespace", "unknown"),
            "type": spec.get("type", "ClusterIP"),
            "cluster_ip": spec.get("clusterIP", ""),
            "ports": [
                {"port": p.get("port"), "protocol": p.get("protocol"), "target_port": p.get("targetPort")}
                for p in spec.get("ports", [])
            ],
            "selector": spec.get("selector", {}),
        })

    return {"services": services}


def _get_endpoints(namespace: str) -> dict:
    args = ["get", "endpoints", "-A"] if namespace == "all" else ["get", "endpoints", "-n", namespace]
    result = run(args, as_json=True)

    if not result.success:
        return {"endpoints_map": {}}

    endpoints_map = {}
    for ep in result.data.get("items", []):
        ns = ep.get("metadata", {}).get("namespace", "unknown")
        name = ep.get("metadata", {}).get("name", "unknown")
        subsets = ep.get("subsets", [])

        addresses = []
        for subset in subsets:
            addresses.extend(subset.get("addresses", []))

        endpoints_map[f"{ns}/{name}"] = {"addresses": addresses}

    return {"endpoints_map": endpoints_map}
