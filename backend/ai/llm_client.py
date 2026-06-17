import asyncio

import httpx
from loguru import logger

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_MAX_RETRIES = 3
_RETRY_DELAY = 2  # seconds


async def chat_complete(
    messages: list[dict],
    api_key: str,
    model: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> str:
    """
    Send a chat completion request to OpenRouter.
    Retries up to _MAX_RETRIES times on transient failures.
    Returns the assistant message content as a string.
    """
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-k8s-agent",
        "X-Title": "AI Kubernetes Agent",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    last_error: Exception | None = None

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                logger.debug(f"LLM request attempt {attempt}/{_MAX_RETRIES} model={model}")
                response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                logger.info(f"LLM responded ({len(content)} chars)")
                return content

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                body = e.response.text[:300]
                logger.error(f"OpenRouter HTTP {status} (attempt {attempt}): {body}")
                last_error = e
                # 4xx errors are not retryable (bad request / auth)
                if status < 500:
                    break

            except httpx.TimeoutException as e:
                logger.warning(f"OpenRouter timeout (attempt {attempt})")
                last_error = e

            except Exception as e:
                logger.error(f"Unexpected LLM error (attempt {attempt}): {e}")
                last_error = e

            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_RETRY_DELAY * attempt)

    raise RuntimeError(f"LLM request failed after {_MAX_RETRIES} attempts: {last_error}")
