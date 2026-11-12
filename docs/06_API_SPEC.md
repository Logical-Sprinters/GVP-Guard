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

## Evidence (object storage)
- `POST /incidents/{id}/evidence` — upload a frame (base64 body); returns storage_key + signed URL
- `GET /incidents/{id}/evidence` — list evidence items with signed, time-limited URLs
- `GET /evidence/{storage_key}` — get a signed URL for viewing/downloading
- `GET /evidence/{storage_key}/download?token=<signed_url>` — download with signed URL token
- `GET /evidence/{storage_key}/checksum` — verify SHA-256 integrity
- `GET /evidence/{storage_key}/access-log` — chain-of-custody access log (officer+)

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

- Implemented: `GET /health`; `GET`, `POST`, `DELETE /incidents`; `GET`, `PATCH /incidents/{id}`; `POST /incidents/{id}/decision`; `POST /incidents/{id}/cleanup-request`; `GET /incidents/{id}/cleanup-request`; `GET /cleanup-requests`; `PATCH /cleanup-requests/{id}`; `GET /incidents/{id}/evidence`; `GET /evidence/{incident_id}/{frame}`; `GET /incidents/{id}/audit`; `GET /incidents/{id}/export`; `GET /gvps`; `GET /analytics/summary`.
- Implemented: evidence object storage (`POST/GET /incidents/{id}/evidence`, `GET /evidence/{storage_key}`, `GET /evidence/{storage_key}/download`, `GET /evidence/{storage_key}/checksum`, `GET /evidence/{storage_key}/access-log`), signed time-limited URLs, SHA-256 checksums, chain-of-custody access log, rate limiting, security headers.
- Still draft: cameras/zones, analysis jobs, events, pagination, idempotency keys and consistent error envelopes.

See [`../backend/README.md`](../backend/README.md) for run instructions.
