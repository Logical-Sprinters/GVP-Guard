"""GVP-Guard optional API + single-origin static server.

Run from the repository root:
    python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

The app then serves `index.html` and `/assets/**` plus `/api/v1/**` on the SAME
origin, so browser code only ever uses relative URLs (no CORS, no localhost).
Without this server the static page still works fully offline via localStorage.
Draft contract: docs/06_API_SPEC.md.

Security: rate limiting, signed evidence URLs, security headers, chain-of-custody
audit logging for evidence access.
"""
import base64
import hashlib
import time
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from . import auth, db
from .schemas import (
    ChecksumVerifyOut,
    CleanupRequestIn,
    CleanupRequestUpdate,
    DecisionIn,
    EvidenceAccessLogOut,
    EvidenceItemOut,
    EvidenceUploadIn,
    IncidentIn,
    LoginIn,
    Token,
    UserIn,
    UserOut,
)

ROOT = Path(__file__).resolve().parent.parent
API = '/api/v1'

app = FastAPI(
    title='GVP-Guard API',
    version='0.3.0',
    description='Draft incident/evidence API for the NightEye AI prototype. Human review required.',
)

db.init_db()
app.mount('/assets', StaticFiles(directory=ROOT / 'assets'), name='assets')


# ---------------------------------------------------------------------------
# Rate limiting (simple in-memory sliding window per client IP)
# ---------------------------------------------------------------------------

_RATE_LIMITS = {
    'default': (60, 60),        # 60 requests per 60s window
    'auth': (10, 60),           # 10 auth requests per 60s window
    'evidence_write': (30, 60), # 30 evidence writes per 60s window
}
_clients: dict[str, list[float]] = defaultdict(list)


def _client_key(request: Request) -> str:
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.client.host if request.client else 'unknown'


def _check_rate_limit(request: Request, limit_name: str) -> None:
    max_req, window = _RATE_LIMITS.get(limit_name, _RATE_LIMITS['default'])
    key = _client_key(request)
    now = time.time()
    window_start = now - window
    timestamps = [t for t in _clients[key] if t > window_start]
    if len(timestamps) >= max_req:
        raise HTTPException(
            status_code=429,
            detail=f'Rate limit exceeded: {max_req} requests per {window}s',
            headers={'Retry-After': str(window)},
        )
    timestamps.append(now)
    _clients[key] = timestamps


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------

_SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    'Content-Security-Policy': (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self';"
    ),
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        for name, value in _SECURITY_HEADERS.items():
            response.headers[name] = value
        return response


app.add_middleware(SecurityHeadersMiddleware)

# ---------------------------------------------------------------------------
# Authentication endpoints
# ---------------------------------------------------------------------------


@app.post(API + '/auth/register', response_model=UserOut, status_code=201)
def register_user(
    request: Request,
    user: UserIn,
    _: dict = Depends(auth.require_role(["admin"])),
):
    """Register a new user. Requires admin role."""
    _check_rate_limit(request, 'auth')
    if user.role not in ["viewer", "officer", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    password_hash = auth.hash_password(user.password)
    user_id = db.create_user(user.username, password_hash, user.role)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Username already exists")
    created = db.get_user_by_id(user_id)
    return UserOut(
        id=created["id"],
        username=created["username"],
        role=created["role"],
        created_at=created.get("created_at"),
    )


@app.post(API + '/auth/login', response_model=Token)
def login_user(
    request: Request,
    login: LoginIn,
):
    """Authenticate user and return access token."""
    _check_rate_limit(request, 'auth')
    user = auth.authenticate_user(login.username, login.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_in = auth.create_user_session(user)
    return Token(
        access_token=token,
        expires_in=expires_in,
        user=user,
    )


@app.post(API + '/auth/logout')
def logout_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(auth.security),
    current_user: auth.TokenData | None = Depends(auth.get_current_user),
):
    """Logout current user (invalidate session)."""
    if credentials and current_user:
        auth.logout_user(credentials.credentials)
    return {"ok": True}


@app.get(API + '/auth/me', response_model=UserOut)
def get_current_user_info(current_user: auth.TokenData = Depends(auth.require_auth)):
    """Get current authenticated user info."""
    user = db.get_user_by_username(current_user.username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
        id=user["id"],
        username=user["username"],
        role=user["role"],
        created_at=user.get("created_at"),
    )


@app.get(API + '/auth/users', response_model=list[UserOut])
def list_users(_: dict = Depends(auth.require_role(["admin"]))):
    """List all users. Requires admin role."""
    users = db.list_users()
    return [
        UserOut(
            id=u["id"],
            username=u["username"],
            role=u["role"],
            created_at=u.get("created_at"),
        )
        for u in users
    ]


@app.patch(API + '/auth/users/{user_id}/role', response_model=UserOut)
def update_user_role(
    user_id: int,
    role: str,
    _: dict = Depends(auth.require_role(["admin"])),
):
    """Update a user's role. Requires admin role."""
    if role not in ["viewer", "officer", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    updated = db.update_user_role(user_id, role)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
        id=updated["id"],
        username=updated["username"],
        role=updated["role"],
        created_at=updated.get("created_at"),
    )


@app.delete(API + '/auth/users/{user_id}')
def deactivate_user_endpoint(
    user_id: int,
    _: dict = Depends(auth.require_role(["admin"])),
):
    """Deactivate a user. Requires admin role."""
    if not db.deactivate_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Protected write endpoints (require authentication)
# ---------------------------------------------------------------------------


@app.post(API + '/incidents', status_code=201)
def create_incident(
    request: Request,
    incident: IncidentIn,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    _check_rate_limit(request, 'evidence_write')
    return db.upsert_incident(incident.model_dump())


@app.patch(API + '/incidents/{incident_id}')
def update_incident(
    request: Request,
    incident_id: str,
    changes: dict,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    _check_rate_limit(request, 'evidence_write')
    incident = db.patch_incident(incident_id, changes)
    if incident is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    return incident


@app.delete(API + '/incidents', status_code=204)
def clear_incidents(
    request: Request,
    _: dict = Depends(auth.require_role(["admin"])),
):
    _check_rate_limit(request, 'evidence_write')
    db.delete_all_incidents()
    return Response(status_code=204)


@app.post(API + '/incidents/{incident_id}/cleanup-request')
def create_cleanup_request(
    request: Request,
    incident_id: str,
    req: CleanupRequestIn,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    _check_rate_limit(request, 'evidence_write')
    if db.get_incident(incident_id) is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    row = db.add_cleanup_request(incident_id, assigned_to=req.assigned_to)
    if row is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    return {'ok': True, 'cleanupRequestId': row['id'], 'status': row['status'],
            'assignedTo': row['assigned_to'], 'requestedAt': row['requested_at']}


@app.patch(API + '/cleanup-requests/{cleanup_id}')
def update_cleanup_request(
    request: Request,
    cleanup_id: int,
    changes: CleanupRequestUpdate,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    _check_rate_limit(request, 'evidence_write')
    row = db.update_cleanup_request(cleanup_id, changes.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(status_code=404, detail='Cleanup request not found')
    return {'ok': True, 'cleanupRequestId': row['id'], 'status': row['status'],
            'assignedTo': row['assigned_to'], 'completedAt': row['completed_at']}


# ---------------------------------------------------------------------------
# Evidence object storage endpoints
# ---------------------------------------------------------------------------

@app.post(API + '/incidents/{incident_id}/evidence', response_model=EvidenceItemOut, status_code=201)
def upload_evidence(
    request: Request,
    incident_id: str,
    evidence: EvidenceUploadIn,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    """Store an evidence frame as an object with checksum + chain-of-custody."""
    _check_rate_limit(request, 'evidence_write')
    if db.get_incident(incident_id) is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    if evidence.kind not in ('before', 'during', 'after'):
        raise HTTPException(status_code=400, detail="kind must be 'before', 'during' or 'after'")
    try:
        file_data = base64.b64decode(evidence.storage_key)
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid base64 file data')
    mime_type = getattr(evidence, 'mime_type', None) or 'image/jpeg'
    item = db.store_evidence(
        incident_id=incident_id,
        kind=evidence.kind,
        data=file_data,
        mime_type=mime_type,
        captured_at=evidence.captured_at,
    )
    db.log_evidence_access(item['storage_key'], current_user.username, 'view')
    signed_url = db.generate_signed_url(item['storage_key'])
    return {**item, 'signed_url': signed_url}


@app.get(API + '/incidents/{incident_id}/evidence', response_model=list[EvidenceItemOut])
def list_evidence(
    incident_id: str,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    """List evidence items for an incident with signed, time-limited URLs."""
    if db.get_incident(incident_id) is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    items = db.list_evidence_for_incident(incident_id)
    result = []
    for item in items:
        signed_url = db.generate_signed_url(item['storage_key'])
        result.append({**item, 'signed_url': signed_url})
    return result


@app.get(API + '/evidence/{storage_key}')
def get_evidence_signed_url(
    storage_key: str,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    """Return a signed, time-limited URL for viewing/downloading an evidence item."""
    item = db.get_evidence_item(storage_key)
    if item is None:
        raise HTTPException(status_code=404, detail='Evidence not found')
    db.log_evidence_access(storage_key, current_user.username, 'view')
    signed_url = db.generate_signed_url(storage_key)
    return {'storage_key': storage_key, 'signed_url': signed_url, 'ttl_seconds': db.EVIDENCE_URL_TTL_SECONDS}


@app.get(API + '/evidence/{storage_key}/download')
def download_evidence_signed(
    storage_key: str,
    token: str | None = None,
    current_user: auth.TokenData = Depends(auth.get_current_user),
):
    """Download evidence file. Requires a valid signed URL token."""
    verified = db.verify_signed_url(token) if token else None
    if not verified or verified.get('storage_key') != storage_key:
        raise HTTPException(status_code=401, detail='Invalid or missing signed URL token')
    item = db.get_evidence_item(storage_key)
    if item is None:
        raise HTTPException(status_code=404, detail='Evidence not found')
    data = db.read_evidence_file(storage_key)
    if data is None:
        raise HTTPException(status_code=404, detail='Evidence file missing on disk')
    actor = current_user.username if current_user else None
    db.log_evidence_access(storage_key, actor, 'download')
    return Response(
        content=data,
        media_type=item['mime_type'],
        headers={'Content-Disposition': f'attachment; filename="{storage_key}.jpg"'},
    )


@app.get(API + '/evidence/{storage_key}/checksum', response_model=ChecksumVerifyOut)
def verify_evidence_checksum(
    storage_key: str,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    """Verify an evidence file's integrity against its recorded SHA-256 checksum."""
    result = db.verify_checksum(storage_key)
    if not result['ok'] and result.get('error') == 'evidence not found':
        raise HTTPException(status_code=404, detail='Evidence not found')
    return result


@app.get(API + '/evidence/{storage_key}/access-log', response_model=list[EvidenceAccessLogOut])
def get_evidence_access_log(
    storage_key: str,
    current_user: auth.TokenData = Depends(auth.require_role(["admin", "officer"])),
):
    """Chain-of-custody access log for an evidence item (officer+)."""
    item = db.get_evidence_item(storage_key)
    if item is None:
        raise HTTPException(status_code=404, detail='Evidence not found')
    return db.get_evidence_access_log(storage_key)


@app.get('/', include_in_schema=False)
def index():
    return FileResponse(ROOT / 'index.html')


@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get(API + '/health')
def health():
    return {'ok': True, 'service': 'gvp-guard', 'version': '0.3.0', 'storage': 'sqlite+object-storage'}


@app.get(API + '/incidents')
def list_incidents(status: str | None = None, camera: str | None = None):
    items = db.list_incidents(status=status, location=camera)
    return {'items': items, 'count': len(items)}


@app.post(API + '/incidents', status_code=201)
def create_incident(incident: IncidentIn):
    return db.upsert_incident(incident.model_dump())


@app.delete(API + '/incidents', status_code=204)
def clear_incidents():
    db.delete_all_incidents()
    return Response(status_code=204)


@app.get(API + '/gvps')
def list_gvps():
    return {'items': db.gvps()}


@app.get(API + '/analytics/summary')
def analytics_summary():
    return db.summary()


@app.get(API + '/incidents/{incident_id}')
def read_incident(incident_id: str):
    incident = db.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    return incident


@app.patch(API + '/incidents/{incident_id}')
def update_incident(incident_id: str, changes: dict):
    incident = db.patch_incident(incident_id, changes)
    if incident is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    return incident


@app.post(API + '/incidents/{incident_id}/cleanup-request')
def create_cleanup_request(incident_id: str, req: CleanupRequestIn):
    if db.get_incident(incident_id) is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    row = db.add_cleanup_request(incident_id, assigned_to=req.assigned_to)
    if row is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    return {'ok': True, 'cleanupRequestId': row['id'], 'status': row['status'],
            'assignedTo': row['assigned_to'], 'requestedAt': row['requested_at']}


@app.get(API + '/incidents/{incident_id}/cleanup-request')
def read_cleanup_requests(incident_id: str):
    if db.get_incident(incident_id) is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    return {'items': db.get_cleanup_requests(incident_id)}


@app.get(API + '/cleanup-requests')
def list_cleanup_requests():
    return {'items': db.get_cleanup_requests()}


@app.patch(API + '/cleanup-requests/{cleanup_id}')
def update_cleanup_request(cleanup_id: int, changes: CleanupRequestUpdate):
    row = db.update_cleanup_request(cleanup_id, changes.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(status_code=404, detail='Cleanup request not found')
    return {'ok': True, 'cleanupRequestId': row['id'], 'status': row['status'],
            'assignedTo': row['assigned_to'], 'completedAt': row['completed_at']}


@app.get(API + '/incidents/{incident_id}/evidence')
def read_evidence(incident_id: str):
    """List evidence items for an incident with signed, time-limited URLs."""
    incident = db.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    items = db.list_evidence_for_incident(incident_id)
    result = []
    for item in items:
        signed_url = db.generate_signed_url(item['storage_key'])
        result.append({
            'id': item['id'],
            'kind': item['kind'],
            'storage_key': item['storage_key'],
            'mime_type': item['mime_type'],
            'size_bytes': item['size_bytes'],
            'checksum_sha256': item['checksum_sha256'],
            'captured_at': item['captured_at'],
            'created_at': item['created_at'],
            'signed_url': signed_url,
        })
    return {
        'incidentId': incident_id,
        'items': result,
        'notice': 'Evidence frames are stored in object storage with SHA-256 checksums. '
                  'Signed URLs are time-limited. Chain-of-custody access log is maintained. '
                  'Not a legal chain of custody until formally reviewed.',
    }


# Old /evidence/{incident_id}/{frame} endpoint replaced by
# /evidence/{storage_key}/download with signed URL tokens.
# Kept for backward compatibility with offline/localStorage mode only.


@app.get(API + '/incidents/{incident_id}/export')
def export_incident(incident_id: str):
    incident = db.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    items = db.list_evidence_for_incident(incident_id)
    evidence_items = []
    for item in items:
        evidence_items.append({
            'id': item['id'],
            'kind': item['kind'],
            'storage_key': item['storage_key'],
            'mime_type': item['mime_type'],
            'size_bytes': item['size_bytes'],
            'checksum_sha256': item['checksum_sha256'],
            'captured_at': item['captured_at'],
            'created_at': item['created_at'],
        })
    return JSONResponse({
        'project': 'GVP-Guard: NightEye AI',
        'problemCode': 'PS000048',
        'teamId': 'TM004162',
        'prototypeNotice': 'Controlled-footage proof of concept. Human review required.',
        'evidenceNotice': 'Evidence frames stored in object storage with SHA-256 checksums. '
                          'Chain-of-custody access log maintained. Not legal chain of custody.',
        'incident': incident,
        'evidence': evidence_items,
        'audit': db.get_audit(incident_id),
    })
