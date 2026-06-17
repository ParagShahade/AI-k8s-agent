import httpx
from loguru import logger

from core.config import settings


async def publish_progress(investigation_id: str, step: str, done: bool) -> None:
    if not settings.insforge_url or not settings.insforge_anon_key:
        return

    url = f"{settings.insforge_url}/api/database/rpc/publish_progress"
    headers = {
        "Authorization": f"Bearer {settings.insforge_anon_key}",
        "Content-Type": "application/json",
    }
    body = {
        "p_channel": f"investigation:{investigation_id}",
        "p_event": "progress",
        "p_payload": {"step": step, "done": done},
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, headers=headers, json=body)
    except Exception as e:
        logger.warning(f"Failed to publish progress event: {e}")
