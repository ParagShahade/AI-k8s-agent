# Thin re-exports kept for backwards compatibility.
# Actual implementations live in the dedicated inspector modules.
from kubernetes.deployment_inspector import inspect_deployments
from kubernetes.events_analyzer import analyze_events
from kubernetes.logs_collector import collect_logs
from kubernetes.network_inspector import inspect_network
from kubernetes.pod_inspector import inspect_pods

__all__ = [
    "inspect_pods",
    "inspect_deployments",
    "analyze_events",
    "collect_logs",
    "inspect_network",
]
