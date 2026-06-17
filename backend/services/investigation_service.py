import asyncio
from typing import Callable, Optional

from loguru import logger

from kubernetes.kubectl import run, set_context
from kubernetes.kubeconfig import classify_kubectl_error
from kubernetes.deployment_inspector import inspect_deployments
from kubernetes.events_analyzer import analyze_events
from kubernetes.logs_collector import collect_logs
from kubernetes.network_inspector import inspect_network
from kubernetes.pod_inspector import inspect_pods


class ClusterAccessError(Exception):
    """Raised when the cluster cannot be reached before investigation starts."""


async def run_investigation(
    namespace: str = "all",
    context: str = "",
    on_progress: Optional[Callable[[str, bool], None]] = None,
) -> dict:
    logger.info(f"Starting investigation (namespace={namespace}, context={context!r})")

    # Apply context for this async task — inherited by every asyncio.to_thread() call below
    set_context(context)

    # Preflight: fail fast with a friendly message if the cluster is unreachable
    preflight = await asyncio.to_thread(run, ["cluster-info"])
    if not preflight.success:
        raise ClusterAccessError(classify_kubectl_error(preflight.stderr))

    async def emit(step: str, done: bool) -> None:
        if on_progress:
            await on_progress(step, done)

    # Step 1: Pod health
    await emit("Checking Pods", False)
    pods = await asyncio.to_thread(inspect_pods, namespace)
    await emit("Checking Pods", True)
    logger.info("Step 1/5 complete: pod inspection")

    # Step 2: Logs for problematic pods only
    await emit("Reading Logs", False)
    problematic_pods = pods.get("problematic_pods", [])
    logs = await asyncio.to_thread(collect_logs, problematic_pods)
    await emit("Reading Logs", True)
    logger.info(f"Step 2/5 complete: collected logs for {len(logs)} pods")

    # Step 3: Kubernetes events
    await emit("Analyzing Events", False)
    events = await asyncio.to_thread(analyze_events, namespace)
    await emit("Analyzing Events", True)
    logger.info("Step 3/5 complete: event analysis")

    # Step 4: Deployment health
    await emit("Inspecting Deployments", False)
    deployments = await asyncio.to_thread(inspect_deployments, namespace)
    await emit("Inspecting Deployments", True)
    logger.info("Step 4/5 complete: deployment inspection")

    # Step 5: Network / services
    await emit("Checking Networking", False)
    network = await asyncio.to_thread(inspect_network, namespace)
    await emit("Checking Networking", True)
    logger.info("Step 5/5 complete: network inspection")

    investigation = {
        "pods": pods,
        "logs": logs,
        "events": events,
        "deployments": deployments,
        "network": network,
    }

    summary = _build_summary(investigation)
    logger.info(f"Investigation complete. Issues found: {summary['total_issues']}")

    return {"investigation": investigation, "summary": summary}


def _build_summary(investigation: dict) -> dict:
    issues = []
    errors = []

    pods = investigation["pods"]
    if "error" in pods:
        errors.append(f"Pod inspection failed: {pods['error']}")
    elif not pods.get("healthy", True):
        count = pods.get("problematic_pod_count", 0)
        if count > 0:
            issues.append(f"{count} problematic pod(s) detected")

    deployments = investigation["deployments"]
    if "error" in deployments:
        errors.append(f"Deployment inspection failed: {deployments['error']}")
    elif not deployments.get("healthy", True):
        count = deployments.get("unhealthy_count", 0)
        if count > 0:
            issues.append(f"{count} unhealthy deployment(s)")

    events = investigation["events"]
    if "error" not in events:
        warning_count = events.get("warning_count", 0)
        if warning_count > 0:
            issues.append(f"{warning_count} warning event(s) in the cluster")

    net_issues = investigation["network"].get("issue_count", 0)
    if net_issues > 0:
        issues.append(f"{net_issues} service/endpoint issue(s)")

    return {
        "total_issues": len(issues),
        "cluster_healthy": len(issues) == 0 and len(errors) == 0,
        "issues": issues,
        "errors": errors,
    }
