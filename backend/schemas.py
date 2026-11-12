"""Request models for the optional GVP-Guard API.

The schema mirrors `docs/07_DATABASE_SCHEMA.md` in a deliberately small form:
incidents, decisions and audit events. Extra fields are allowed so the browser
prototype can evolve without breaking the API contract.
"""
from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, Field, EmailStr


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
    detectionMethod: str | None = None
    vehicleData: dict | None = None


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


# ============================================================================
# Authentication & Authorization Schemas
# ============================================================================

ROLES = ["viewer", "officer", "admin"]


class UserRole(BaseModel):
    role: str


class UserIn(BaseModel):
    username: str
    password: str
    role: str = "officer"


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: str | None = None


class LoginIn(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None
