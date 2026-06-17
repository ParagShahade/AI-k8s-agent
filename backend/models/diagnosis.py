from pydantic import BaseModel


class Diagnosis(BaseModel):
    root_cause: str
    explanation: str
    fix: str
    kubectl_commands: list[str] = []
    prevention: str = ""
    confidence: int = 0
    ai_available: bool = True
