# MVP Scope and Definition of Done

## MVP-0: current browser workflow
- Recorded-video upload
- Evidence-frame extraction
- Pixel scene comparison
- Incident details and manual plate
- Officer decisions, history, map and JSON export

## MVP-1: technical proof
- Live webcam input
- GVP polygon editor
- Real vehicle detection
- Persistent tracking and stop timer
- Automatic evidence buffer
- Basic backend persistence

## MVP-2: event and ANPR
- Person/object cues
- Before/after object-change logic
- Plate detector and multi-frame OCR
- Confidence and manual fallback
- Evaluation dataset and metrics

## Out of scope until authorized
- Automatic fine/e-challan
- Real vehicle registry
- Production municipal deployment
- Face recognition
- Drone verification
- Predictive policing

## Definition of Done
A feature is done only when it has:
1. Working code
2. Test coverage or documented manual test
3. Error/fallback behavior
4. Logging
5. Updated docs
6. Demonstration evidence
7. No claim beyond measured results

## Implementation status (2026-11-05)

See [`15_IMPLEMENTATION_STATUS.md`](15_IMPLEMENTATION_STATUS.md) for the code ledger. MVP-1 is **partially delivered**: live webcam input, an editable GVP polygon, a rolling evidence buffer, a zone-limited scene-stability heuristic and optional API persistence are working. Real vehicle detection/tracking, a vehicle stop timer, a multi-cue dumping-event model and multi-frame ANPR remain MVP-2 / next-stage work.
