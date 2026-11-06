"""Request models for the optional GVP-Guard API.

The schema mirrors `docs/07_DATABASE_SCHEMA.md` in a deliberately small form:
incidents, decisions and audit events. Extra fields are allowed so the browser
prototype can evolve without breaking the API contract.
"""
from pydantic import BaseModel, ConfigDict, Field


class IncidentIn(BaseModel):
    model_config = ConfigDict(extra='allow')

    id: str
    time: str | None = None
    file: str | None = None
    sceneChange: str | None = None
    illustrativeCueScore: str | None = None
    plate: str | None = None
    decision: str | None = None
    location: str | None = None
    status: str | None = None
    statusCode: str = 'REVIEW_REQUIRED'
    demo: bool = False
    triggerReasons: list[str] = Field(default_factory=list)
    evidenceFrames: dict[str, str | None] | None = None
    source: str | None = None
    reviewer: str | None = None
    comment: str | None = None


class DecisionIn(BaseModel):
    decision: str
    reviewer: str | None = 'Demo officer'
    comment: str | None = ''
    reviewedPlate: str | None = None


class CleanupRequestIn(BaseModel):
    assigned_to: str | None = None


class CleanupRequestUpdate(BaseModel):
    status: str | None = None
    assigned_to: str | None = None
