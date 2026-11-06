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
`id, incident_id, kind, storage_key, mime_type, captured_at, checksum_nullable`

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

## Implementation status (2026-11-05)

`incidents`, `decisions`, `audit_events` and `cleanup_requests` exist in the SQLite prototype (`backend/db.py`). Evidence frames are stored as JPEG data URLs inside the incident payload — there is no object storage, signed URL, checksum or chain-of-custody implementation. `cameras`, `gvp_zones`, `analysis_jobs`, `tracks`, `vehicles` and `evidence_items` remain draft. Immutable audit enforcement and retention/expiration jobs are not implemented.
