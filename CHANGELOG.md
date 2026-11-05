# Changelog

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
