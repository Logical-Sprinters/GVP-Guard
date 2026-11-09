# Development Roadmap

## Phase → Judge-Deck → Demo mapping

| Phase | Judge-deck step | Demo steps (`docs/13`) | Focus |
|-------|----------------|------------------------|-------|
| Phase 0 | Step 1 — Submission | Demo prep | Stable browser prototype, final deck, video, documentation |
| Phase 1 | Step 2 — Live MVP | Demo steps 1–8 | Webcam input, zone editor, motion/stability, backend persistence, evidence buffer |
| Phase 2–3 | Step 3 — Vehicle AI + ANPR | Recorded vehicle clip separately | Vehicle detection, ByteTrack tracking, stop timer, plate OCR, dumping-event cue |
| Phase 4–6 | Step 4 — Platform + Pilot | Pilot prep + two-site pilot | Auth, roles, object storage, audit, GMC permission, field validation |

## Phase 0 — Submission workflow
Stable browser prototype, final deck, video and documentation.

## Phase 1 — Live technical MVP
Webcam input, zone editor, motion/stability logic, backend persistence and automatic evidence buffer.

## Phase 2 — Vehicle intelligence
Vehicle detector, tracker, stop timer, track-event association and performance report. (Step 4 code present — DEMO STAGE)

## Phase 3 — Dumping and ANPR
Controlled dataset, multi-cue event engine, plate detector, multi-frame OCR and false-alert evaluation. (Step 4 code present — DEMO STAGE)

## Phase 4 — Platform hardening
Authentication, roles, object storage, audit, retention, observability, API/UI tests and deployment packaging.

## Phase 5 — Pilot preparation
GMC permission, approved footage, camera survey, privacy review, baseline and bill of materials.

## Phase 6 — Two-site pilot
Local tuning, officer feedback, cleanup workflow, KPI measurement and go/no-go review.

## Expansion gate
Expand only when false alerts, plate performance, usability, privacy, cost and response integration meet agreed pilot thresholds.

## Claim discipline per phase
- **Phase 0–1:** WORKING — verified by tests (11/11 JS, 10/10 Python)
- **Phase 2–3:** DEMO STAGE — code present, not benchmarked on held-out test set. Stop time alone does NOT imply guilt.
- **Phase 4–6:** PLANNED — not implemented. Requires GMC permission and approved footage.
