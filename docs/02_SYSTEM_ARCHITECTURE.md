# System Architecture

## Context
```text
Camera / Video -> Edge or Ingestion Service -> Event AI -> ANPR
               -> Evidence Service -> Incident API -> Officer Dashboard
               -> GVP Analytics -> Cleanup / Enforcement Workflow
```

## Components
1. **Video ingestion**: uploaded file, webcam or RTSP/CCTV stream (same-origin MJPEG proxy via backend).
2. **Zone manager**: camera metadata and GVP polygons.
3. **RTSP capture service**: OpenCV VideoCapture backend daemon that reads RTSP streams and re-encodes as MJPEG frames for same-origin consumption. Auto-reconnects with exponential backoff.
4. **Real-time alerting**: Server-Sent Events (SSE) stream for scene-stability alerts from RTSP cameras.
3. **Vehicle/activity detector**: detections and track IDs.
4. **Event engine**: stop timer, person/object cues and scene comparison.
5. **ANPR service**: plate detection, frame quality, enhancement, OCR and voting.
6. **Evidence service**: frames, clips, hashes later, metadata and storage references.
7. **Incident service**: lifecycle, assignment, decision and audit.
8. **Dashboard**: review, map, history and cleanup status.
9. **Analytics**: aggregate GVP history and transparent priority score.

## Incident state machine
```text
CANDIDATE -> SUSPICIOUS -> REVIEW_REQUIRED
                           |-> APPROVED
                           |-> REJECTED
                           |-> CLEANUP_REQUESTED -> CLEANUP_ASSIGNED -> CLOSED
```

## Edge/cloud boundary
Future edge nodes should decode video, limit processing to regions/events and upload triggered clips. Central services initially handle storage, multi-frame OCR and dashboards. Capacity must be benchmarked before camera-count claims.

## Failure paths
- Network unavailable: local queue and later sync.
- RTSP stream disconnected: auto-reconnect with exponential backoff; camera status set to offline/error.
- Camera moved/blocked: health alert via SSE.
- Plate unreadable: retain event; plate status `MANUAL_REVIEW`.
- Low event confidence: review, never automatic action.
- Duplicate incident: deduplicate by camera, track and time window.

## Observability
Track FPS, queue depth, inference time, dropped frames, storage failures, false-alert outcomes and review latency.
