import json
import re

from loguru import logger

from ai.llm_client import chat_complete
from ai.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from core.config import settings


async def analyze(investigation: dict) -> dict:
    """
    Send the investigation payload to the LLM and return a structured diagnosis.
    Falls back to a safe error dict if the LLM call or parsing fails.
    """
    user_prompt = build_user_prompt(investigation)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    if not settings.openrouter_model:
        return {
            "root_cause": "AI analysis unavailable — OPENROUTER_MODEL not configured",
            "explanation": "Set OPENROUTER_MODEL in backend/.env to enable AI diagnosis.",
            "suggested_fix": "Add OPENROUTER_MODEL=<model-id> to your .env file.",
            "confidence": 0,
        }

    try:
        raw = await chat_complete(
            messages=messages,
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
        )
        return _parse_response(raw)

    except ValueError as e:
        # API key not configured — return a clear notice instead of crashing
        logger.warning(f"AI analysis skipped: {e}")
        return {
            "root_cause": "AI analysis unavailable — OPENROUTER_API_KEY not configured",
            "explanation": str(e),
            "fix": "Set OPENROUTER_API_KEY in your .env file to enable AI diagnosis.",
            "kubectl_commands": [],
            "prevention": "",
            "confidence": 0,
            "ai_available": False,
        }

    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {
            "root_cause": "AI analysis failed",
            "explanation": str(e),
            "fix": "Check backend logs for details.",
            "kubectl_commands": [],
            "prevention": "",
            "confidence": 0,
            "ai_available": False,
        }


def _parse_response(raw: str) -> dict:
    """
    Extract JSON from the LLM response.
    Handles responses wrapped in ```json ... ``` fences.
    """
    text = raw.strip()

    # Strip markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fenced:
        text = fenced.group(1).strip()

    # Find the outermost JSON object
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1:
        text = text[brace_start : brace_end + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}\nRaw: {raw[:500]}")
        return {
            "root_cause": "Could not parse AI response",
            "explanation": raw[:500],
            "fix": "Review raw LLM output.",
            "kubectl_commands": [],
            "prevention": "",
            "confidence": 0,
            "ai_available": True,
        }

    # Normalise fields
    data.setdefault("kubectl_commands", [])
    data.setdefault("prevention", "")
    data.setdefault("confidence", 0)
    data["ai_available"] = True

    # Clamp confidence
    try:
        data["confidence"] = max(0, min(100, int(data["confidence"])))
    except (TypeError, ValueError):
        data["confidence"] = 0

    return data
