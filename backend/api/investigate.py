from fastapi import APIRouter, HTTPException
from loguru import logger

from ai.agent import diagnose
from models.diagnosis import Diagnosis
from models.investigation import InvestigationRequest, InvestigationResponse
from services.investigation_service import ClusterAccessError, run_investigation
from services.insforge_service import publish_progress

router = APIRouter()


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate(request: InvestigationRequest = InvestigationRequest()):
    investigation_id = request.investigation_id
    context = request.context or ""
    logger.info(
        f"Investigation requested (namespace={request.namespace}, "
        f"context={context!r}, id={investigation_id})"
    )

    try:
        async def on_progress(step: str, done: bool) -> None:
            if investigation_id:
                await publish_progress(investigation_id, step, done)

        # Step 1: Collect Kubernetes evidence
        result = await run_investigation(
            namespace=request.namespace,
            context=context,
            on_progress=on_progress,
        )
        investigation = result["investigation"]
        summary = result["summary"]

        # Step 2: AI reasoning
        if investigation_id:
            await publish_progress(investigation_id, "AI Reasoning", False)
        raw_diagnosis = await diagnose(investigation)
        diagnosis = Diagnosis(**raw_diagnosis)
        if investigation_id:
            await publish_progress(investigation_id, "AI Reasoning", True)

        return InvestigationResponse(
            status="success",
            investigation_id=investigation_id,
            investigation=investigation,
            summary=summary,
            diagnosis=diagnosis,
        )

    except ClusterAccessError as e:
        # Friendly message for cluster connectivity problems — not a 500
        logger.warning(f"Cluster access error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
