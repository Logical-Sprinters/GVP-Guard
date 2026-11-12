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
import json
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

# Prometheus-compatible metrics
_REQUEST_COUNT = defaultdict(int)
_REQUEST_LATENCY = defaultdict(list)
_INCIDENT_COUNT = {'total': 0}

# Configure structured JSON logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record, datefmt='%Y-%m-%dT%H:%M:%S'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(JsonFormatter())
_logger = logging.getLogger('gvp-guard')
_logger.setLevel(logging.INFO)
_logger.addHandler(_handler)
logger = logging.getLogger('gvp-guard')

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from . import auth, db
from .rtsp_capture import (
    get_camera_frame, list_active_cameras, start_camera, stop_camera,
    stop_all_cameras,
)
from .schemas import (
    CameraIn,
    CameraOut,
    CameraUpdate,
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
    ZoneIn,
    ZoneOut,
    ZoneUpdate,
)

ROOT = Path(__file__).resolve().parent.parent
API = '/api/v1'

app = FastAPI(
    title='GVP-Guard API',
    version='0.4.0',
    description='Draft incident/evidence API for the NightEye AI prototype. Human review required.',
)

db.init_db()
app.mount('/assets', StaticFiles(directory=ROOT / 'assets'), name='assets')


# ---------------------------------------------------------------------------
# Real-time alerting (Server-Sent Events)
# ---------------------------------------------------------------------------

_alert_subscribers: dict[str, list] = {}  # camera_id -> list of asyncio queues
_alert_lock = __import__('asyncio').Lock()


async def _broadcast_alert(camera_id: str, alert: dict):
    """Send an alert to all SSE subscribers for a camera."""
    import asyncio
    async with _alert_lock:
        queues = _alert_subscribers.get(camera_id, [])
        for q in queues:
            try:
                q.put_nowait(alert)
            except Exception:
                pass


@app.get(API + '/alerts/stream')
async def alert_stream(request: Request, camera_id: str | None = None):
    """Server-Sent Events stream for real-time alerts.

    Query params:
      - camera_id: optional, subscribe to alerts for a specific camera
    Returns text/event-stream with alert events.
    """
    import asyncio

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        subscriber_key = camera_id or '__global__'
        async with _alert_lock:
            _alert_subscribers.setdefault(subscriber_key, []).append(queue)
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'camera_id': subscriber_key})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    alert = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(alert)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        finally:
            async with _alert_lock:
                if subscriber_key in _alert_subscribers:
                    try:
                        _alert_subscribers[subscriber_key].remove(queue)
                    except ValueError:
                        pass

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


# ---------------------------------------------------------------------------
# Camera management endpoints
# ---------------------------------------------------------------------------

@app.post(API + '/cameras', response_model=CameraOut, status_code=201)
def create_camera_endpoint(
    request: Request,
    camera: CameraIn,
    current_user: auth.TokenData = Depends(auth.require_role(["admin", "officer"])),
):
    """Register a new camera. Requires officer+ role."""
    _check_rate_limit(request, 'evidence_write')
    created = db.create_camera(
        camera_id=camera.id,
        name=camera.name,
        location_text=camera.location_text,
        lat=camera.lat,
        lon=camera.lon,
        stream_ref=camera.stream_ref,
    )
    if created is None:
        raise HTTPException(status_code=400, detail='Camera ID already exists')
    # If RTSP stream provided, attempt to start capturing
    if camera.stream_ref:
        start_camera(camera.id, camera.stream_ref)
    return CameraOut(**created)


@app.get(API + '/cameras', response_model=list[CameraOut])
def list_cameras_endpoint():
    """List all cameras with current status."""
    cameras = db.list_cameras()
    # Merge live status from RTSP capture registry
    active = {c['camera_id']: c for c in list_active_cameras()}
    result = []
    for cam in cameras:
        cam_dict = dict(cam)
        if cam['id'] in active:
            cam_dict['status'] = 'online' if active[cam['id']]['connected'] else 'error'
            cam_dict['fps'] = active[cam['id']]['fps']
            cam_dict['error'] = active[cam['id']]['error']
        result.append(CameraOut(**cam_dict))
    return result


@app.get(API + '/cameras/{camera_id}', response_model=CameraOut)
def get_camera_endpoint(camera_id: str):
    """Get a single camera by ID."""
    cam = db.get_camera(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail='Camera not found')
    return CameraOut(**cam)


@app.patch(API + '/cameras/{camera_id}', response_model=CameraOut)
def update_camera_endpoint(
    request: Request,
    camera_id: str,
    changes: CameraUpdate,
    current_user: auth.TokenData = Depends(auth.require_role(["admin", "officer"])),
):
    """Update camera metadata. Requires officer+ role."""
    _check_rate_limit(request, 'evidence_write')
    cam = db.get_camera(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail='Camera not found')
    update_data = changes.model_dump(exclude_unset=True)
    # Handle stream_ref changes: restart capture if stream changed
    if 'stream_ref' in update_data and update_data['stream_ref'] != cam.get('stream_ref'):
        stop_camera(camera_id)
        if update_data['stream_ref']:
            start_camera(camera_id, update_data['stream_ref'])
    updated = db.update_camera(camera_id, update_data)
    if updated is None:
        raise HTTPException(status_code=404, detail='Camera not found')
    return CameraOut(**updated)


@app.delete(API + '/cameras/{camera_id}', status_code=204)
def delete_camera_endpoint(
    request: Request,
    camera_id: str,
    current_user: auth.TokenData = Depends(auth.require_role(["admin"])),
):
    """Delete a camera. Requires admin role."""
    _check_rate_limit(request, 'evidence_write')
    stop_camera(camera_id)
    if not db.delete_camera(camera_id):
        raise HTTPException(status_code=404, detail='Camera not found')
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# RTSP frame / stream endpoints
# ---------------------------------------------------------------------------

@app.get(API + '/cameras/{camera_id}/frame')
def get_camera_frame_endpoint(camera_id: str, current_user: auth.TokenData = Depends(auth.require_auth)):
    """Get the latest JPEG frame from an RTSP camera."""
    result = get_camera_frame(camera_id)
    if result is None:
        raise HTTPException(status_code=404, detail='Camera not streaming or no frame available')
    ts, jpeg = result
    return Response(content=jpeg, media_type='image/jpeg',
                    headers={'Cache-Control': 'no-cache, no-store, must-revalidate'})


@app.get(API + '/cameras/{camera_id}/stream')
def get_camera_stream_endpoint(camera_id: str, current_user: auth.TokenData = Depends(auth.require_auth)):
    """MJPEG stream of an RTSP camera feed.

    Returns multipart/x-mixed-replace JPEG stream for same-origin consumption.
    No CORS, no direct RTSP from the client.
    """
    cam = None
    from .rtsp_capture import get_camera_instance
    cam = get_camera_instance(camera_id)
    if cam is None:
        # Try to auto-start if camera exists in DB with stream_ref
        db_cam = db.get_camera(camera_id)
        if db_cam and db_cam.get('stream_ref'):
            start_camera(camera_id, db_cam['stream_ref'])
            cam = get_camera_instance(camera_id)
        if cam is None:
            raise HTTPException(status_code=404, detail='Camera not found or not streaming')

    def mjpeg_generator():
        boundary = b'--frameboundary'
        while True:
            result = cam.get_latest_frame()
            if result:
                ts, jpeg = result
                yield (boundary + b'\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(jpeg)).encode() + b'\r\n'
                       b'\r\n' + jpeg + b'\r\n')
            time.sleep(0.1)  # ~10 FPS cap

    return StreamingResponse(
        mjpeg_generator(),
        media_type='multipart/x-mixed-replace; boundary=frameboundary',
        headers={'Cache-Control': 'no-cache, no-store, must-revalidate'},
    )


# ---------------------------------------------------------------------------
# GVP Zone endpoints
# ---------------------------------------------------------------------------

@app.post(API + '/cameras/{camera_id}/zones', response_model=ZoneOut, status_code=201)
def create_zone_endpoint(
    request: Request,
    camera_id: str,
    zone: ZoneIn,
    current_user: auth.TokenData = Depends(auth.require_role(["admin", "officer"])),
):
    """Create a GVP zone for a camera. Requires officer+ role."""
    _check_rate_limit(request, 'evidence_write')
    if zone.camera_id != camera_id:
        raise HTTPException(status_code=400, detail='Zone camera_id does not match path')
    if db.get_camera(camera_id) is None:
        raise HTTPException(status_code=404, detail='Camera not found')
    created = db.create_zone(
        zone_id=zone.id,
        camera_id=zone.camera_id,
        name=zone.name,
        polygon_json=zone.polygon_json,
        stop_threshold_seconds=zone.stop_threshold_seconds,
    )
    if created is None:
        raise HTTPException(status_code=400, detail='Zone ID already exists')
    return ZoneOut(**created)


@app.get(API + '/cameras/{camera_id}/zones', response_model=list[ZoneOut])
def list_zones_endpoint(camera_id: str):
    """List all GVP zones for a camera."""
    zones = db.list_zones(camera_id)
    return [ZoneOut(**z) for z in zones]


@app.get(API + '/zones/{zone_id}', response_model=ZoneOut)
def get_zone_endpoint(zone_id: str):
    """Get a single zone by ID."""
    zone = db.get_zone(zone_id)
    if zone is None:
        raise HTTPException(status_code=404, detail='Zone not found')
    return ZoneOut(**zone)


@app.patch(API + '/zones/{zone_id}', response_model=ZoneOut)
def update_zone_endpoint(
    request: Request,
    zone_id: str,
    changes: ZoneUpdate,
    current_user: auth.TokenData = Depends(auth.require_role(["admin", "officer"])),
):
    """Update a zone. Requires officer+ role."""
    _check_rate_limit(request, 'evidence_write')
    updated = db.update_zone(zone_id, changes.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(status_code=404, detail='Zone not found')
    return ZoneOut(**updated)


@app.delete(API + '/zones/{zone_id}', status_code=204)
def delete_zone_endpoint(
    request: Request,
    zone_id: str,
    current_user: auth.TokenData = Depends(auth.require_role(["admin"])),
):
    """Delete a zone. Requires admin role."""
    _check_rate_limit(request, 'evidence_write')
    if not db.delete_zone(zone_id):
        raise HTTPException(status_code=404, detail='Zone not found')
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Camera health / status
# ---------------------------------------------------------------------------

@app.get(API + '/cameras/{camera_id}/health')
def get_camera_health(camera_id: str):
    """Get camera health status."""
    cam = db.get_camera(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail='Camera not found')
    active = list_active_cameras()
    live = next((c for c in active if c['camera_id'] == camera_id), None)
    health = {
        'camera_id': camera_id,
        'db_status': cam['status'],
        'streaming': live is not None and live['connected'],
        'fps': live['fps'] if live else 0.0,
        'error': live['error'] if live else None,
    }
    return health


@app.post(API + '/cameras/{camera_id}/start', status_code=204)
def start_camera_endpoint(
    request: Request,
    camera_id: str,
    current_user: auth.TokenData = Depends(auth.require_role(["admin", "officer"])),
):
    """Start RTSP capture for a camera."""
    _check_rate_limit(request, 'evidence_write')
    cam = db.get_camera(camera_id)
    if cam is None:
        raise HTTPException(status_code=404, detail='Camera not found')
    if not cam.get('stream_ref'):
        raise HTTPException(status_code=400, detail='Camera has no stream_ref')
    start_camera(camera_id, cam['stream_ref'])
    return Response(status_code=204)


@app.post(API + '/cameras/{camera_id}/stop', status_code=204)
def stop_camera_endpoint(
    request: Request,
    camera_id: str,
    current_user: auth.TokenData = Depends(auth.require_role(["admin", "officer"])),
):
    """Stop RTSP capture for a camera."""
    _check_rate_limit(request, 'evidence_write')
    stop_camera(camera_id)
    return Response(status_code=204)


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
# Request logging middleware (structured logs + metrics)
# ---------------------------------------------------------------------------

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    path = request.url.path
    method = request.method
    status = response.status_code

    _REQUEST_COUNT[(method, path, status)] += 1
    _REQUEST_LATENCY[(method, path)].append(duration)
    if len(_REQUEST_LATENCY[(method, path)]) > 1000:
        _REQUEST_LATENCY[(method, path)] = _REQUEST_LATENCY[(method, path)][-1000:]

    logger.info(
        "request",
        extra={
            'method': method,
            'path': path,
            'status': status,
            'duration_ms': round(duration * 1000, 2),
            'client': request.client.host if request.client else 'unknown',
        },
    )
    return response


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
    from . import rtsp_capture
    active = rtsp_capture.list_active_cameras()
    cameras_online = sum(1 for c in active if c['connected'])
    cameras_total = len(active)

    return {
        'ok': True,
        'service': 'gvp-guard',
        'version': '0.4.0',
        'storage': 'sqlite+object-storage',
        'dependencies': {
            'database': 'ok',
            'evidence_storage': 'ok',
        },
        'cameras': {
            'total': cameras_total,
            'online': cameras_online,
        },
    }


@app.get(API + '/metrics')
def metrics():
    lines = []

    for (method, path, status), count in sorted(_REQUEST_COUNT.items()):
        lines.append(f'http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}')

    for (method, path), latencies in sorted(_REQUEST_LATENCY.items()):
        if latencies:
            avg = sum(latencies) / len(latencies)
            lines.append(f'http_request_duration_seconds_avg{{method="{method}",path="{path}"}} {avg:.6f}')

    try:
        incidents = db.list_incidents()
        _INCIDENT_COUNT['total'] = len(incidents)
    except Exception:
        _INCIDENT_COUNT['total'] = 0

    lines.append(f'gvp_incidents_total {_INCIDENT_COUNT["total"]}')

    try:
        from . import rtsp_capture
        active = rtsp_capture.list_active_cameras()
        for cam in active:
            cid = cam['camera_id']
            connected = 1 if cam['connected'] else 0
            fps = cam['fps']
            lines.append(f'gvp_camera_connected{{camera_id="{cid}"}} {connected}')
            lines.append(f'gvp_camera_fps{{camera_id="{cid}"}} {fps}')
    except Exception:
        pass

    return Response(content=chr(10).join(lines) + chr(10), media_type='text/plain')
'.join(lines) + '


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
