"""GVP-Guard optional API + single-origin static server.

Run from the repository root:
    python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

The app then serves `index.html` and `/assets/**` plus `/api/v1/**` on the SAME
origin, so browser code only ever uses relative URLs (no CORS, no localhost).
Without this server the static page still works fully offline via localStorage.
Draft contract: docs/06_API_SPEC.md.
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import db
from .schemas import DecisionIn, IncidentIn

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


@app.post(API + '/incidents/{incident_id}/decision')
def record_decision(incident_id: str, decision: DecisionIn):
    if db.get_incident(incident_id) is None:
        raise HTTPException(status_code=404, detail='Incident not found')
    db.add_decision(incident_id, decision.decision, decision.reviewer,
                    decision.comment or '', decision.reviewedPlate)
    return {'ok': True, 'incidentId': incident_id, 'decision': decision.decision}


@app.get(API + '/incidents/{incident_id}/audit')
def audit_trail(incident_id: str):
    return {'items': db.get_audit(incident_id), 'decisions': db.get_decisions(incident_id)}


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
