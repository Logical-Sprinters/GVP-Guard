"""GVP-Guard optional API + single-origin static server.

Run from the repository root:
    python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

The app then serves `index.html` and `/assets/**` plus `/api/v1/**` on the SAME
origin, so browser code only ever uses relative URLs (no CORS, no localhost).
Without this server the static page still works fully offline via localStorage.
Draft contract: docs/06_API_SPEC.md.
"""
import base64
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import db
from .schemas import CleanupRequestIn, CleanupRequestUpdate, DecisionIn, IncidentIn

ROOT = Path(__file__).resolve().parent.parent
API = '/api/v1'

app = FastAPI(
    title='GVP-Guard API',
    version='0.2.0',
    description='Draft incident/evidence API for the NightEye AI prototype. Human review required.'
)

db.init_db()
app.mount('/assets', StaticFiles(directory=ROOT / 'assets'), name='assets')


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
