# Product Requirements Document (PRD)

## 1. Problem
Night-time illegal dumping can create recurring Garbage Vulnerable Points (GVPs). Patrol coverage is limited, CCTV review is manual, plates may be unclear and operational response may be delayed.

## 2. Users
- Sanitary inspectors
- Solid-waste management officers
- Municipal enforcement officers
- Cleanup/dispatch teams
- System administrators

## 3. Product goal
Convert suspicious video activity into a structured, human-reviewed incident containing evidence, a vehicle/plate candidate when available, location/time and a decision/cleanup workflow.

## 4. Non-goals for MVP
- Automatic guilt or fines
- Legal-admissibility claims
- Guaranteed offender identification
- Prediction of future dumping
- Citywide production deployment
- Registry/e-challan integration without permission

## 5. Functional requirements
### Video and camera
- Upload recorded video (MVP)
- Configure camera and GVP region
- Support live webcam/RTSP later

### Event workflow
- Detect/track vehicle or activity
- Calculate stop time
- Evaluate object-transfer and scene-change cues
- Produce normal, suspicious, probable or low-confidence status

### ANPR
- Select best plate frames
- Run OCR across multiple frames
- Show confidence and allow correction
- Preserve incidents when plate is unavailable

### Evidence
- Incident ID, camera, location and timestamps
- Before/during/after frames
- Short event clip
- Vehicle/plate crops
- Trigger reasons and confidence

### Officer actions
- Approve
- Reject with reason
- Request cleanup
- Add comment
- View history/audit trail

### GVP monitoring
- Incident count and response status
- Repeat-location history
- Transparent priority score

## 6. Non-functional requirements
- Human decision mandatory
- Role-based access
- Auditability
- Configurable retention
- Graceful low-confidence fallback
- Network interruption tolerance
- Measurable latency and false-alert rate

## 7. Success metrics
- False alerts per camera-hour
- Dumping-event precision/recall
- Correct/partial plate-read rate
- Alert-to-review and alert-to-action time
- Evidence completeness
- Officer acceptance/rejection rate

## 8. Acceptance statement
The MVP is accepted when one controlled incident moves from video input through evidence generation to a persisted officer decision without unsupported automated enforcement.
