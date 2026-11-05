# API Specification (Draft)

Base path: `/api/v1`

## Cameras and zones
- `GET /cameras`
- `POST /cameras`
- `GET /cameras/{id}/zones`
- `POST /cameras/{id}/zones`
- `PATCH /zones/{id}`

## Video/events
- `POST /analysis/jobs` — upload/reference video and zone
- `GET /analysis/jobs/{id}` — state and progress
- `GET /events/{id}` — event cues and confidence

## Incidents
- `GET /incidents?status=&camera=&from=&to=`
- `POST /incidents`
- `GET /incidents/{id}`
- `PATCH /incidents/{id}`
- `POST /incidents/{id}/decision`
- `POST /incidents/{id}/cleanup-request`
- `GET /incidents/{id}/audit`
- `GET /incidents/{id}/export`

## Evidence
- `POST /incidents/{id}/evidence`
- `GET /incidents/{id}/evidence`
- `GET /evidence/{id}/download`

## GVP analytics
- `GET /gvps`
- `GET /gvps/{id}`
- `GET /gvps/{id}/history`
- `GET /analytics/summary`

## Decision request example
```json
{
  "decision": "CLEANUP_REQUESTED",
  "reviewed_plate": "GJ05XX0001",
  "comment": "Object remains after subject leaves"
}
```

## API rules
Use UUIDs, ISO-8601 UTC timestamps, pagination, role checks, validation, idempotency for actions and consistent error envelopes. Never expose raw storage paths.

## Implementation status (2026-11-05)

`backend/app.py` now serves this API on the same origin as the static app:

- Implemented: `GET /health`; `GET`, `POST`, `DELETE /incidents`; `GET`, `PATCH /incidents/{id}`; `POST /incidents/{id}/decision`; `GET /incidents/{id}/audit`; `GET /incidents/{id}/export`; `GET /gvps`; `GET /analytics/summary`.
- Still draft: cameras/zones, analysis jobs, events, evidence upload/download, cleanup assignment, authentication and role checks, pagination, idempotency keys and consistent error envelopes.

See [`../backend/README.md`](../backend/README.md) for run instructions.
