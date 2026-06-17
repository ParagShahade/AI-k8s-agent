import json
import subprocess
from contextvars import ContextVar
from dataclasses import dataclass, field

from loguru import logger

from core.config import settings

UNHEALTHY_STATUSES = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "Error",
    "OOMKilled",
    "Pending",
    "ContainerCreating",
    "Failed",
    "Terminating",
}

WARNING_REASONS = {
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "Unhealthy",
    "Failed",
    "OOMKilling",
    "NetworkNotReady",
}

# Per-asyncio-task context — inherited by asyncio.to_thread() calls
_context: ContextVar[str] = ContextVar("kubectl_context", default="")


def set_context(ctx: str) -> None:
    """Set the kubectl --context for the current async task and its spawned threads."""
    _context.set(ctx or "")


@dataclass
class KubectlResult:
    success: bool
    stdout: str
    stderr: str
    command: str
    data: dict = field(default_factory=dict)


def run(args: list[str], as_json: bool = False, ignore_context: bool = False) -> KubectlResult:
    cmd = ["kubectl"]

    if settings.kubeconfig_path:
        cmd += [f"--kubeconfig={settings.kubeconfig_path}"]

    if not ignore_context:
        ctx = _context.get()
        if ctx:
            cmd += [f"--context={ctx}"]

    cmd += args

    if as_json:
        cmd += ["-o", "json"]

    logger.debug(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        success = result.returncode == 0

        if not success:
            logger.warning(f"kubectl failed [{result.returncode}]: {result.stderr.strip()}")

        data = {}
        if as_json and success and result.stdout:
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.warning("Could not parse kubectl JSON output")

        return KubectlResult(
            success=success,
            stdout=result.stdout,
            stderr=result.stderr,
            command=" ".join(cmd),
            data=data,
        )

    except subprocess.TimeoutExpired:
        logger.error(f"kubectl timed out: {' '.join(cmd)}")
        return KubectlResult(success=False, stdout="", stderr="Command timed out after 30s", command=" ".join(cmd))

    except FileNotFoundError:
        logger.error("kubectl not found in PATH")
        return KubectlResult(success=False, stdout="", stderr="kubectl not found in PATH", command=" ".join(cmd))

    except Exception as e:
        logger.error(f"Unexpected error running kubectl: {e}")
        return KubectlResult(success=False, stdout="", stderr=str(e), command=" ".join(cmd))
