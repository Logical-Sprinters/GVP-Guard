# Changelog

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
