"""GVP-Guard optional API + single-origin static server.

Run from the repository root:
    python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

The app then serves `index.html` and `/assets/**` plus `/api/v1/**` on the SAME
origin, so browser code only ever uses relative URLs (no CORS, no localhost).
Without this server the static page still works fully offline via localStorage.
Draft contract: docs/06_API_SPEC.md.
"""
import base64
import hashlib
from datetime import timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

from . import auth, db
from .schemas import (
    CleanupRequestIn,
    CleanupRequestUpdate,
    DecisionIn,
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
    version='0.2.0',
    description='Draft incident/evidence API for the NightEye AI prototype. Human review required.',
)

db.init_db()
app.mount('/assets', StaticFiles(directory=ROOT / 'assets'), name='assets')

# ---------------------------------------------------------------------------
# Authentication endpoints
# ---------------------------------------------------------------------------


@app.post(API + '/auth/register', response_model=UserOut, status_code=201)
def register_user(user: UserIn, _: dict = Depends(auth.require_role(["admin"]))):
    """Register a new user. Requires admin role."""
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
def login_user(login: LoginIn):
    """Authenticate user and return access token."""
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
    incident: IncidentIn,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    return db.upsert_incident(incident.model_dump())


@app.patch(API + '/incidents/{incident_id}')
def update_incident(
    incident_id: str,
    changes: dict,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    incident = db.patch_incident(incident_id, changes)
    if incident is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    return incident


@app.delete(API + '/incidents', status_code=204)
def clear_incidents(_: dict = Depends(auth.require_role(["admin"]))):
    db.delete_all_incidents()
    return Response(status_code=204)


@app.post(API + '/incidents/{incident_id}/cleanup-request')
def create_cleanup_request(
    incident_id: str,
    req: CleanupRequestIn,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    if db.get_incident(incident_id) is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    row = db.add_cleanup_request(incident_id, assigned_to=req.assigned_to)
    if row is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    return {'ok': True, 'cleanupRequestId': row['id'], 'status': row['status'],
            'assignedTo': row['assigned_to'], 'requestedAt': row['requested_at']}


@app.patch(API + '/cleanup-requests/{cleanup_id}')
def update_cleanup_request(
    cleanup_id: int,
    changes: CleanupRequestUpdate,
    current_user: auth.TokenData = Depends(auth.require_auth),
):
    row = db.update_cleanup_request(cleanup_id, changes.model_dump(exclude_unset=True))
    if row is None:
        raise HTTPException(status_code=404, detail='Cleanup request not found')
    return {'ok': True, 'cleanupRequestId': row['id'], 'status': row['status'],
            'assignedTo': row['assigned_to'], 'completedAt': row['completed_at']}


@app.get('/', include_in_schema=False)
def index():
    return FileResponse(ROOT / 'index.html')


@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get(API + '/health')
def health():
    return {'ok': True, 'service': 'gvp-guard', 'version': '0.2.0', 'storage': 'sqlite'}


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
    incident = db.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    frames = incident.get('evidenceFrames') or {}
    return {
        'incidentId': incident_id,
        'frames': {
            'before': frames.get('before'),
            'during': frames.get('during'),
            'after': frames.get('after'),
        },
        'notice': 'Evidence frames are JPEG data URLs captured from the source. No chain of custody or legal admissibility is claimed.',
    }


@app.get(API + '/evidence/{incident_id}/{frame}')
def download_evidence(incident_id: str, frame: str):
    incident = db.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    frames = incident.get('evidenceFrames') or {}
    if frame not in ('before', 'during', 'after'):
        raise HTTPException(status_code=400, detail='Frame must be one of: before, during, after')
    data_url = frames.get(frame)
    if not data_url:
        raise HTTPException(status_code=404, detail=f'{frame} frame not found for this incident')
    try:
        header, b64 = data_url.split(',', 1)
        image_bytes = base64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=500, detail='Unable to decode evidence frame')
    media_type = 'image/jpeg'
    if 'image/png' in header:
        media_type = 'image/png'
    return Response(content=image_bytes, media_type=media_type,
                    headers={'Content-Disposition': f'attachment; filename="{incident_id}-{frame}.jpg"'})


@app.get(API + '/incidents/{incident_id}/export')
def export_incident(incident_id: str):
    incident = db.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    return JSONResponse({
        'project': 'GVP-Guard: NightEye AI',
        'problemCode': 'PS000048',
        'teamId': 'TM004162',
        'prototypeNotice': 'Controlled-footage proof of concept. Human review required.',
        'evidenceNotice': 'No hashes, chain of custody or legal admissibility is claimed.',
        'incident': incident,
        'audit': db.get_audit(incident_id)
    })
