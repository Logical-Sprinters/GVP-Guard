# API Specification (Draft)

Base path: `/api/v1`

## Cameras and zones
- `GET /cameras` — list all cameras with live status
- `POST /cameras` — register a new camera (officer+)
- `GET /cameras/{id}` — get a camera
- `PATCH /cameras/{id}` — update camera metadata (officer+)
- `DELETE /cameras/{id}` — delete a camera (admin)
- `POST /cameras/{id}/start` — start RTSP capture (officer+)
- `POST /cameras/{id}/stop` — stop RTSP capture (officer+)
- `GET /cameras/{id}/health` — camera health status
- `GET /cameras/{id}/frame` — latest JPEG frame (auth required)
- `GET /cameras/{id}/stream` — MJPEG stream (auth required)
- `GET /cameras/{id}/zones` — list zones for a camera
- `POST /cameras/{id}/zones` — create a zone (officer+)
- `GET /zones/{id}` — get a zone
- `PATCH /zones/{id}` — update a zone (officer+)
- `DELETE /zones/{id}` — delete a zone (admin)

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

## Real-time alerting
- `GET /alerts/stream?camera_id=<id>` — Server-Sent Events stream for scene-stability alerts (auth required)

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
- Implemented: cameras/zones (`GET/POST/PATCH/DELETE /cameras`, `GET/POST/PATCH/DELETE /zones`, `GET /cameras/{id}/health`, `GET /cameras/{id}/frame`, `GET /cameras/{id}/stream`, `POST /cameras/{id}/start|stop`), RTSP capture via OpenCV backend daemon, MJPEG streaming, SSE alerting (`GET /alerts/stream`), rate limiting, security headers.
- Still draft: analysis jobs, events, pagination, idempotency keys and consistent error envelopes.

See [`../backend/README.md`](../backend/README.md) for run instructions.
