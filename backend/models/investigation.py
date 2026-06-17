from typing import Optional

from pydantic import BaseModel

from models.diagnosis import Diagnosis


class InvestigationRequest(BaseModel):
    namespace: str = "all"
    context: Optional[str] = None
    investigation_id: Optional[str] = None


class InvestigationSummary(BaseModel):
    total_issues: int
    cluster_healthy: bool
    issues: list[str]
    errors: list[str] = []


class InvestigationResponse(BaseModel):
    status: str
    investigation_id: Optional[str] = None
    investigation: Optional[dict] = None
    summary: Optional[InvestigationSummary] = None
    diagnosis: Optional[Diagnosis] = None
