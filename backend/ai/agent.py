from loguru import logger

from ai.root_cause_analyzer import analyze


async def diagnose(investigation: dict) -> dict:
    """
    Entry point for AI reasoning.
    Takes a full investigation payload and returns a structured diagnosis.
    """
    logger.info("Starting AI diagnosis")
    diagnosis = await analyze(investigation)
    logger.info(
        f"AI diagnosis complete — root_cause='{diagnosis.get('root_cause', '')[:80]}' "
        f"confidence={diagnosis.get('confidence', 0)}"
    )
    return diagnosis
