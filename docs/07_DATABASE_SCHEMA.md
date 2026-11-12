# Database Schema (Draft)

## Core tables
### users
`id, name, email, role, organization_id, active, created_at`

### cameras
`id, name, location_text, lat, lon, stream_ref, status, created_at`

### gvp_zones
`id, camera_id, name, polygon_json, stop_threshold_seconds, active`

### analysis_jobs
`id, camera_id, source_type, source_ref, status, started_at, completed_at, error`

### tracks
`id, job_id, external_track_id, object_type, first_seen, last_seen, stop_seconds`

### incidents
`id, camera_id, zone_id, track_id, status, event_score, trigger_reasons_json, occurred_at, created_at`

### vehicles
`id, incident_id, type, color, plate_candidate, plate_confidence, review_status`

### evidence_items
`id, incident_id, kind, storage_key, mime_type, size_bytes, checksum_sha256, captured_at, created_at`

### evidence_access_log
`id, storage_key, actor_id, action, accessed_at, ip_address`

### decisions
`id, incident_id, reviewer_id, decision, comment, reviewed_plate, created_at`

### cleanup_requests
`id, incident_id, status, assigned_to, requested_at, completed_at`

### audit_events
`id, actor_id, entity_type, entity_id, action, old_json, new_json, created_at`

## Constraints
- Immutable audit rows
- Unique camera/track/time deduplication key
- Foreign keys and status enums
- Soft delete only where policy permits
- Evidence expiration date for retention

## Storage
Database stores metadata and opaque object keys. Clips/images remain in controlled object storage with signed access URLs.

## Implementation status (2026-11-06)

`incidents`, `decisions`, `audit_events`, `cleanup_requests`, `evidence_items`, `evidence_access_log`, `cameras` and `gvp_zones` exist in the SQLite prototype (`backend/db.py`). Camera CRUD, zone CRUD, RTSP capture (`backend/rtsp_capture.py`), MJPEG streaming, SSE alerting and camera health endpoints are implemented in `backend/app.py`. Evidence frames are stored as individual files under `data/evidence/` with opaque storage keys and SHA-256 checksums. Signed, time-limited URLs gate all evidence access. Chain-of-custody access log records every view/download/verify action. `analysis_jobs`, `tracks`, `vehicles` remain draft. Retention/expiration jobs (`delete_expired_evidence`) are implemented but not scheduled.
