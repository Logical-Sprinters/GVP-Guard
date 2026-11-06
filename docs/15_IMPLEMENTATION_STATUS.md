# Implementation Status — MVP-1 Technical Proof

Last updated: **2026-11-06**. This file records **what code actually exists** in the repository. Documents `01`–`14` and `16` remain the canonical product/engineering/team specifications; this ledger only tracks implementation progress and claim boundaries.

## Code layout

```text
index.html                     # semantic markup only; root entry point for static hosting
assets/css/app.css             # all styling (extracted from the original single file)
assets/js/
  config.js                    # thresholds, buffer size, API base, default polygon
  core.js                      # DOM-free pure logic (geometry, diff, scoring, status, report)
  camera.js                    # recorded file / webcam source + frame capture + safe seeking
  zone.js                      # editable normalised GVP polygon overlay
  evidence.js                  # rolling frame buffer + canvas painting
  monitor.js                   # live scene-stability heuristic
  storage.js                   # localStorage / optional API dual-mode persistence
  app.js                       # orchestration and DOM wiring
backend/
  app.py                       # FastAPI: static files + /api/v1 on one origin
  db.py                        # SQLite: incidents, decisions, audit_events
  schemas.py                   # Pydantic request models
  test_db.py                   # dependency-free unittest suite
  README.md                    # run + endpoint reference
tests/
  core.test.js                 # node:test pure-logic tests
  ui.test.js                   # jsdom boot / offline mode / API mode / XSS tests
package.json                   # dev-only test tooling (the app has no runtime deps)
```

## Working now (verified by tests)

| Capability | Where | Notes |
|------------|-------|-------|
| Static 4-tab shell, no build step | `index.html`, `app.css` | No external scripts/fonts/network calls |
| Recorded-video upload + playback | `camera.js` | Object URLs are revoked on reset/replacement |
| Live webcam input | `camera.js` | `getUserMedia`; fails gracefully where unavailable |
| Editable GVP polygon | `zone.js`, `config.js` | Normalised `[0..1]` coords, click to add, drag vertices, saved to `localStorage` |
| Zone-limited frame differencing | `core.js` `sceneDifference` | Only sampled pixels inside the polygon count |
| Rolling evidence buffer | `evidence.js` | 30 frames at 5 fps (~6 s) |
| Live monitoring | `monitor.js` | **Scene-stability heuristic only** — not vehicle detection, tracking, a vehicle stop timer, or a dumping model |
| Before/during/after frames with real pixels | `evidence.js`, `app.js` | JPEG data URLs embedded in the JSON report |
| Incident record | `app.js`, `core.js` | Canonical `statusCode`, `triggerReasons`, `reviewer`, `comment`, `reviewedAt`, `source` |
| Officer approve / reject / cleanup | `app.js` | Writes incident + decision + audit row |
| Dual-mode persistence | `storage.js` | `localStorage` offline; FastAPI + SQLite via **relative** `/api/v1` URLs when available |
| API endpoints | `backend/app.py` | health, incidents CRUD-ish, decisions, audit, export, GVPs, summary |
| Transparent GVP priority score | `core.js`, `db.py` | Fixed published weights; capped at 100; not a prediction model |
| Test harness | `tests/`, `backend/test_db.py` | 14 JS tests + 5 Python tests |

## Explicitly NOT implemented (claim discipline)

Vehicle detection, tracking IDs, a vehicle stop timer, a dumping-event model, person/object-transfer cues, plate detection, multi-frame OCR/ANPR, confidence calibration, authentication, roles, rate limiting, object storage, signed evidence URLs, malware scanning, retention/deletion jobs, checksums or chain of custody, live CCTV/RTSP, official GMC/registry/e-challan integration, field validation, and any measured accuracy, false-alert or impact figure.

The UI now uses canonical `STATUS` codes (`SUSPICIOUS` / `CANDIDATE`) from `classify()` and renders them via `STATUS_LABEL`. Canonical enum codes are stored in `statusCode`. The fixed 8% zone-diff threshold and illustrative cue score remain uncalibrated heuristics (labelled as such).

## Definition of Done check (`03_MVP_SCOPE.md`)

| Criterion | Status |
|-----------|--------|
| Working code | ✅ for the features listed above |
| Tests or documented manual test | ✅ `npm test`, `python3 -m unittest backend.test_db -v`; manual webcam/zone demo still required |
| Error / fallback behaviour | ✅ offline fallback, seek timeout, webcam failure, API failure |
| Logging | ⚠️ browser `console` only; no structured observability yet |
| Updated docs | ✅ this file, `docs/README.md`, `06`, `07`, `09`, `backend/README.md`, `CHANGELOG.md` |
| Demonstration evidence | ⚠️ screenshots/video not yet recorded |
| No claim beyond measured results | ✅ enforced in UI text and JSON notices |

## Run and test

```bash
# Offline static mode (no dependencies)
python3 -m http.server 8000 --bind 0.0.0.0

# Full mode: same origin serves the app and /api/v1
python3 -m pip install -r backend/requirements.txt
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

# Tests
npm install
npm test
python3 -m unittest backend.test_db -v
```

## Open decisions (from `docs/README.md` watchlist)

1. **Status labels (RESOLVED 2026-11-06):** `classify()` now returns canonical `STATUS` codes (`SUSPICIOUS` / `CANDIDATE`) instead of hardcoded 'Probable dumping' / 'Ambiguous' strings. UI displays use `STATUS_LABEL` from `core.js`; the history table renders `STATUS_LABEL[x.status]`. Demo seed records use canonical codes. Display wording is consistent with the canonical enum.
2. **Roadmap granularity:** reconcile phases 0–6 (`11`), 5 handbook stages, and the 4-step judge-deck timeline.
3. **Branch policy:** `main` is still a placeholder README; `master` holds the code. Confirm the long-term base.
4. **Demo hygiene:** the fabricated cue score and fixed threshold are now labelled as heuristics; replacing them with measured cues is MVP-2 work.
5. **Repo scaffolding:** issue templates, LICENSE and environment setup are still P0 backlog items; `.gitignore`, `package.json` and tests are now present.
6. **Next build (step 4) — remains DEFERRED (team decision, 2026-11-06):** YOLO11n + ByteTrack/IoU detection, then multi-frame ANPR — do not start until model weights, a controlled dataset and a benchmarking plan are in place.
7. **Team structure — SETTLED (2026-11-06):** four roles × two members each; named roster, file/directory ownership and judge-Q&A owners in `16_TEAM_ROSTER_AND_OWNERSHIP.md`, workflow/RACI/Git rules in `14_TEAM_WORKFLOW.md`. Omkar Solat remains Team Lead while sitting in the AI/Vision/Data pair; judge-deck slide 8 still shows the older one-person-per-role layout and must be regenerated (P0 in `12_BACKLOG.md`). This ledger is maintained by the Integration/Testing pair (Prince Rana + Sayantani Mandal).
