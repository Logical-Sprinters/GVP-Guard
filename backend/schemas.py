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


# ============================================================================
# Evidence object storage schemas
# ============================================================================

class EvidenceItemOut(BaseModel):
    id: int
    incident_id: str
    kind: str
    storage_key: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str
    captured_at: str | None = None
    created_at: str
    signed_url: str | None = None


class EvidenceUploadIn(BaseModel):
    incident_id: str
    kind: str
    storage_key: str  # base64-encoded file data
    mime_type: str = 'image/jpeg'
    captured_at: str | None = None


class EvidenceAccessLogOut(BaseModel):
    id: int
    storage_key: str
    actor_id: str | None = None
    action: str
    accessed_at: str
    ip_address: str | None = None


class ChecksumVerifyOut(BaseModel):
    ok: bool
    storage_key: str
    expected_checksum: str | None = None
    actual_checksum: str | None = None
    error: str | None = None


# ============================================================================
# Camera & GVP zone schemas
# ============================================================================

class CameraIn(BaseModel):
    id: str
    name: str
    location_text: str | None = None
    lat: float | None = None
    lon: float | None = None
    stream_ref: str | None = None  # RTSP URL or other stream reference


class CameraOut(BaseModel):
    id: str
    name: str
    location_text: str | None = None
    lat: float | None = None
    lon: float | None = None
    stream_ref: str | None = None
    status: str
    created_at: str
    updated_at: str


class CameraUpdate(BaseModel):
    name: str | None = None
    location_text: str | None = None
    lat: float | None = None
    lon: float | None = None
    stream_ref: str | None = None
    status: str | None = None


class ZoneIn(BaseModel):
    id: str
    camera_id: str
    name: str
    polygon_json: str  # JSON string of normalised [0..1] points
    stop_threshold_seconds: float = 2.0


class ZoneOut(BaseModel):
    id: str
    camera_id: str
    name: str
    polygon_json: str
    stop_threshold_seconds: float
    active: bool
    created_at: str
    updated_at: str


class ZoneUpdate(BaseModel):
    camera_id: str | None = None
    name: str | None = None
    polygon_json: str | None = None
    stop_threshold_seconds: float | None = None
    active: bool | None = None
