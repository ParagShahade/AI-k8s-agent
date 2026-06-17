import re

from loguru import logger

from kubernetes.kubectl import run

# Patterns that indicate meaningful errors in logs
_ERROR_PATTERNS = re.compile(
    r"(exception|error|fatal|traceback|failed|connection refused|"
    r"no such file|permission denied|env.*not.*set|missing.*env|"
    r"oomkilled|killed|panic|crash)",
    re.IGNORECASE,
)

MAX_LOG_LINES = 100
MAX_RELEVANT_LINES = 30


def collect_logs(problematic_pods: list[dict]) -> dict:
    """
    Collect and filter logs for each problematic pod.
    Tries --previous first (crashed container) then current container.
    """
    collected: dict[str, dict] = {}

    for pod in problematic_pods:
        name = pod["name"]
        namespace = pod["namespace"]
        key = f"{namespace}/{name}"

        logger.info(f"Collecting logs for pod {key}")
        log_entry = _fetch_pod_logs(name, namespace)
        collected[key] = log_entry

    return collected


def _fetch_pod_logs(name: str, namespace: str) -> dict:
    # Try previous (crashed) container first
    result = run(["logs", name, "-n", namespace, "--tail", str(MAX_LOG_LINES), "--previous"])

    source = "previous"
    if not result.success or not result.stdout.strip():
        result = run(["logs", name, "-n", namespace, "--tail", str(MAX_LOG_LINES)])
        source = "current"

    if not result.success or not result.stdout.strip():
        return {"available": False, "source": source, "lines": [], "relevant_lines": []}

    all_lines = result.stdout.strip().splitlines()
    relevant = [line for line in all_lines if _ERROR_PATTERNS.search(line)]

    return {
        "available": True,
        "source": source,
        "total_lines": len(all_lines),
        "lines": all_lines[-MAX_LOG_LINES:],
        "relevant_lines": relevant[-MAX_RELEVANT_LINES:],
    }
