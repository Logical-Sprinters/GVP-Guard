# Changelog

## [0.4.0] — Step 4 vehicle detection code (DEMO STAGE) (2026-11-07)

Application code added for Step 4 (vehicle detection + stop timer). All Step 4 features remain DEMO STAGE — not WORKING until benchmarked on a held-out test set. No accuracy figures published.

### Added
- `assets/js/vehicle-detection.js`: YOLO11n vehicle detection via OpenCV DNN (ONNX), vehicle stop timer inside GVP polygon, stop-start/stop-end events
- `tools/benchmark_detection.py`: FPS/latency/per-class detection benchmark, outputs `benchmark_results.json`

### Changed
- `docs/15_IMPLEMENTATION_STATUS.md`: vehicle-detection.js added to code layout; Step 4 moved to DEMO STAGE table; open decision #6 updated; explicit NOT implemented list updated (removed vehicle detection/stop timer, kept ByteTrack/dumping-event/ANPR etc.)
- `docs/12_BACKLOG.md`: P2 Vehicle AI items referenced against implemented code

### Honesty notes
- Vehicle detection and stop timer are DEMO STAGE — stop time alone does NOT imply guilt
- Weights (`models/weights/yolo11n.onnx`) are NOT committed; download per `docs/STEP4_READINESS_PLAN.md`
- ByteTrack integration, dumping-event model, object-transfer cues, plate detection, multi-frame OCR/ANPR remain NOT implemented

## [0.3.2] — Step 4 readiness tooling (2026-11-07)

Concrete tools and documented sources for all three Step 4 prerequisites. No application code changed; Step 4 remains deferred.

### Added
- `tools/download_weights.py` — exact download URLs for YOLO11n/yolo11s pretrained weights (official Ultralytics CDN + Hugging Face mirrors)
- `tools/benchmark_detection.py` — runs detection benchmark, outputs `benchmark_results.json` with FPS, latency, per-class counts (metrics per docs/05)
- `tools/requirements.txt` — ultralytics, opencv-python, easyocr, numpy, Pillow
- `tools/dataset_acquisition.md` — exact dataset URLs: Indian Truck License Plates (Kaggle/HF), Indian Number Plates (HF), VisionPlate_ANPR (IEEE Dataport), Roboflow Indian Number Plate, ANPR 2, COCO val2017
- `tools/README.md` — quick start and go/no-go checklist

### Changed
- `docs/12_BACKLOG.md` — P0 Step 4 readiness item references the concrete tools
- `CHANGELOG.md` — this entry

## [0.3.1] — Step 4 readiness planning (2026-11-06)

### Added
- `docs/STEP4_READINESS_PLAN.md`: model weights acquisition plan (YOLO11n/ByteTrack/OCR), controlled dataset collection protocol (permitted site, lighting conditions, positive/negative scenarios, annotation schema, dataset split, minimum sample sizes), benchmarking plan (metrics, targets, hardware to record, go/no-go criteria)
- `docs/12_BACKLOG.md`: P0 item for Step 4 readiness (weights, dataset, benchmarking plan)
- `docs/README.md`: Step 4 readiness indexed as a working document (non-canonical)

### Changed
- `docs/15_IMPLEMENTATION_STATUS.md`: Step 4 open decision references `docs/STEP4_READINESS_PLAN.md` and backlog P0

## [0.3.0] — Evidence download & release (2026-11-06)

### Added
- `backend/app.py`: `GET /incidents/{id}/evidence` (return evidence frames) and `GET /evidence/{incident_id}/{frame}` (download individual before/during/after frame as JPEG)
- `assets/js/storage.js`: `getEvidence`, `downloadEvidence` methods
- `assets/js/app.js`: per-frame evidence download buttons (before/during/after) with offline canvas fallback
- `index.html`: Download button under each evidence canvas
- Tagged release `v0.3.0`
- `backend/test_db.py`: 10 tests (5 original + 5 cleanup-request), all pass
- `tests/core.test.js`: 11 tests, all pass

### Changed
- `docs/06_API_SPEC.md`: evidence endpoints marked implemented
- `docs/15_IMPLEMENTATION_STATUS.md`: evidence download added to "Working now" table; demonstration evidence marked complete in Definition of Done

## [0.2.3] — Cleanup-request workflow (2026-11-06)

### Added
- `backend/db.py`: `cleanup_requests` table (`id, incident_id, status, assigned_to, requested_at, completed_at`); `add_cleanup_request`, `get_cleanup_request`, `get_cleanup_requests`, `update_cleanup_request`, `delete_all_cleanup_requests`; audit rows for `CLEANUP_REQUESTED` and `UPDATE` actions; `delete_all_incidents` also clears cleanup requests
- `backend/schemas.py`: `CleanupRequestIn`, `CleanupRequestUpdate` Pydantic models
- `backend/app.py`: endpoints `POST /incidents/{id}/cleanup-request`, `GET /incidents/{id}/cleanup-request`, `GET /cleanup-requests`, `PATCH /cleanup-requests/{id}`
- `assets/js/storage.js`: `requestCleanup`, `updateCleanupRequest`, `loadCleanupRequests` methods
- `assets/js/app.js`: cleanup-request UI section (request/assign/complete/cancel), status display, `loadCleanupSection` on incident load
- `index.html`: cleanup-request panel with assignee input and action buttons
- `backend/test_db.py`: 5 cleanup-request tests (create/get, list by incident, update status, audit trail, delete all)
- `tests/core.test.js`: 11 tests (unchanged, all pass)

### Changed
- `docs/06_API_SPEC.md`: cleanup-request endpoints marked implemented
- `docs/07_DATABASE_SCHEMA.md`: `cleanup_requests` table marked implemented
- `docs/15_IMPLEMENTATION_STATUS.md`: cleanup-request added to "Working now" table
- `backend/test_db.py`: 10 tests total (5 original + 5 cleanup-request), all pass

## [0.2.2] — Status labels frozen to canonical STATUS enum (2026-11-06)

### Changed
- `assets/js/core.js`: `classify()` returns canonical `STATUS` codes (`SUSPICIOUS` / `CANDIDATE`) instead of hardcoded 'Probable dumping' / 'Ambiguous' strings
- `assets/js/app.js`: UI displays render via `STATUS_LABEL`; history table renders `STATUS_LABEL[x.status]`; decide flow shows `STATUS_LABEL[incident.statusCode]`; demo seed records use canonical codes
- `tests/core.test.js`: classify test asserts canonical STATUS codes
- `tests/ui.test.js`: demo/API fixtures use canonical `SUSPICIOUS` status
- `docs/15_IMPLEMENTATION_STATUS.md`: watchlist item 1 marked RESOLVED; UI label description updated
- `docs/README.md`: watchlist item 1 marked RESOLVED
- `docs/16_TEAM_ROSTER_AND_OWNERSHIP.md`: frontend planned work updated (label freeze done)

## [0.2.1] — Team structure & documentation update (2026-11-06)

Documentation-only release: the team structure is settled as **4 roles × 2 members**; no application code changed.

### Added
- `docs/16_TEAM_ROSTER_AND_OWNERSHIP.md`: confirmed roster (2026-11-06) with primary/co-owner per role, file & directory ownership map, deliverables per role, judge-Q&A ownership, hand-off convention, and the superseded judge-deck slide-8 layout preserved as a historical record
- `docs/14_TEAM_WORKFLOW.md`: 2-per-role rule, per-role responsibilities and deliverables, RACI matrix, backup & escalation path, expanded Definition of Ready / Definition of Done, weekly rhythm, Git workflow for the org's protected `master`, and the communication rule
- `README.md`: "Team at a glance" 4×2 table, status-at-a-glance matrix, how-it-works pipeline, full documentation map for all sixteen docs, and a Node.js 22+ note for the jsdom suite (verified: 14/14 JS tests on Node 22, 5/5 Python tests)
- `docs/hackathon/JUDGE_QA.md`: role-ownership table for the six canonical questions (answers unchanged, verbatim)
- `docs/12_BACKLOG.md`: P0 item to regenerate judge-deck slide 8 for the settled roster

### Changed
- `README.md` rebuilt: identity table with the org repository URL, problem/team/institution/challenge facts, core rule, quick start (both run modes), tests, repository layout, docs map, claim discipline and branch notes
- `docs/hackathon/SUBMISSION_BRIEF.md`: eight-row one-person-per-role roster replaced with the 4-role × 2 table; slide 8 flagged for regeneration (not silently rewritten)
- `CONTRIBUTING.md`: "one cross-pair review" → "one review from a member of **another role**"; branch guidance now names protected `master`; roster-change convention added
- `docs/README.md`: doc 16 added to the reading-order table, by-theme list and conventions; doc 14 description updated; watchlist item 5 (team roster) marked RESOLVED; item 4 (branch policy) wording updated to match the corrected docs
- `docs/15_IMPLEMENTATION_STATUS.md`: open decisions record that the team structure is settled (2026-11-06) and that step 4 (detection/ANPR) remains deferred
- `package.json` / `package-lock.json`: version metadata bumped to 0.2.1 (dev tooling only — the app has no runtime dependencies)

### Fixed
- Removed the stale "Four pairs / eight individual roles" wording and the protected-`main` assumption from `docs/14_TEAM_WORKFLOW.md`

### Known limitations
- The handbook and judge-deck PDFs are not committed; slide 8 still shows the older one-person-per-role layout until it is regenerated
- The Team Lead (Omkar Solat) now sits in the AI/Vision/Data pair while handbook/deck list him as "Team Lead & Integration" — the contradiction is flagged in `docs/14`/`docs/16`, not silently resolved
- Step 4 (YOLO/ByteTrack vehicle detection + multi-frame ANPR) remains deferred pending model weights, a controlled dataset and benchmarking
- All MVP-1 limitations from 0.2.0 still apply (see `docs/15_IMPLEMENTATION_STATUS.md`)

## [0.2.0] — MVP-1 technical proof (2026-11-05)

### Added
- Refactored the minified single-file demo into `index.html` + `assets/css/app.css` + eight ES modules under `assets/js/`; no build step, no runtime dependencies
- `core.js`: DOM-free, unit-tested geometry, zone-limited frame differencing, illustrative cue score, canonical `STATUS` enum, transparent priority score, collision-resistant incident IDs and report builder
- `camera.js`: recorded file + live webcam sources, frame capture, object-URL cleanup and a seek timeout that prevents a hung analysis
- `zone.js`: editable normalised GVP polygon (add/drag vertices, save/reset to `localStorage`)
- `evidence.js`: rolling 30-frame buffer and real before/during/after JPEG frames embedded in the JSON export
- `monitor.js`: live scene-stability heuristic with configurable stable-for threshold (explicitly **not** vehicle tracking or a dumping model)
- `app.js`: zone selection, reviewer/comment fields, status codes, decisions, dynamic GVP map counts and dual-mode storage indicator
- `backend/`: optional FastAPI service serving static files and `/api/v1` on one origin, SQLite `incidents` / `decisions` / `audit_events`, Pydantic schemas, endpoint docs and unit tests
- `tests/`: 11 pure-logic + 3 jsdom UI/API-mode tests, plus 5 SQLite tests; `package.json` dev tooling
- `docs/15_IMPLEMENTATION_STATUS.md` code ledger; implementation-status notes added to `03`, `06`, `07`, `09`

### Fixed
- Removed injected third-party Cloudflare challenge/beacon scripts and the embedded token; the page is now self-contained and offline-safe
- Escaped all history-table fields (prevents HTML injection through the plate/decision inputs); revoked video object URLs on reset/new file
- Labelled the illustrative cue score as an uncalibrated pixel-difference heuristic in the UI and JSON export; added notices that exported frames carry no chain-of-custody claim
- Flagged seeded sample records as `DEMO` data with a visible badge and history note
- Cleared stale incident fields and evidence canvases when a new analysis is started
- Map zone counts now derive from real records instead of hardcoded numbers; canonical status codes are stored on every incident
- Corrected the demo run command and made documentation links resolve to `docs/`; removed the assumption that `main` is the active development base

### Known limitations
- No real vehicle detector/tracker, vehicle stop timer, dumping-event model, plate detector/OCR/ANPR or confidence calibration
- No authentication, roles, object storage, signed URLs, retention jobs, checksums, rate limits or structured observability
- Display labels (`Probable dumping` / `Ambiguous`) still come from a fixed 8% heuristic threshold and are not yet frozen against the canonical enum
- Roadmap granularity still differs between `11_DEVELOPMENT_ROADMAP.md`, the handbook and the judge deck
- No Gandhidham field validation and no measured accuracy / false-alert figures

## [0.1.0] — Online-round workflow prototype
### Added
- Recorded-video upload
- Evidence frames and scene comparison
- Person/vehicle scenario selection
- Manual plate review
- Officer actions, history, map and JSON export
- Project documentation baseline

### Known limitations
- No real vehicle detector/tracker
- No automatic dumping model
- No automatic OCR/ANPR
- No backend persistence or authentication
- No Gandhidham field validation
