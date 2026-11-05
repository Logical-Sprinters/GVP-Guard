# GVP-Guard: NightEye AI

Human-reviewed illegal-dumping incident and evidence platform for PS000048.

## Project identity
- Team: TM004162
- Institution: P. P. Savani University, Surat, Gujarat
- Challenge: Seva First Innovation Challenge 2026 (Education Dept, Govt. of Gujarat / SSIP 2.0), College track
- Current maturity: MVP-1 technical proof (browser-based, human-reviewed)
- Field status: not validated in Gandhidham

## Core rule
A stopped vehicle is not automatically guilty. Stop time only creates a suspected event; supporting cues and an authorized officer's review are required before action.

## Current prototype

**Working now:** recorded-video upload **and live webcam**, an editable GVP polygon, zone-limited pixel comparison, a rolling evidence buffer with real JPEG frames, a live scene-stability heuristic, before/during/after evidence, incident records with canonical status codes / reviewer / comment, approve-reject-cleanup with audit rows, local history, a GVP map with a transparent priority score, JSON export containing real frame data, and optional FastAPI + SQLite persistence.

**Demo-stage / heuristics (explicitly labelled):** the CSS tracking overlay, the editable plate candidate, the illustrative cue score and the fixed 8% zone-diff threshold. The live monitor is a **scene-stability heuristic, not vehicle detection, tracking, a vehicle stop timer or a dumping model**.

**Still not implemented:** real vehicle detection/tracking, dumping-event model, plate detection/OCR/ANPR, RTSP input, auth/roles, object storage, signed URLs, retention, measured accuracy or official integrations.

See [docs/15_IMPLEMENTATION_STATUS.md](docs/15_IMPLEMENTATION_STATUS.md) for the exact code ledger and claim boundaries.

## Run the prototype

**Mode 1 — offline static (no dependencies, no build step):**
```bash
cd /path/to/GVP-Guard
python3 -m http.server 8000 --bind 0.0.0.0
```

**Mode 2 — full app + API on one origin:**
```bash
python3 -m pip install -r backend/requirements.txt
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/`. In mode 2 the header badge changes to "API persistence (SQLite)"; browser code only ever calls relative `/api/v1` URLs, so there is no CORS and no `localhost` call from the client. In mode 1 the app detects the missing API and keeps working entirely from `localStorage`. The page has no external scripts, fonts or network calls and runs fully offline.

Use a controlled, permitted 20–30 second clip, or start the webcam, edit the GVP zone, then run an analysis or live monitoring. See [backend/README.md](backend/README.md) for the endpoint list.

## Tests

```bash
npm install            # dev-only: jsdom for UI tests
npm test               # 14 Node tests (pure logic + jsdom UI/API modes)
python3 -m unittest backend.test_db -v   # 5 SQLite tests
```

## Repository layout
```text
.
├── index.html                  # semantic markup; root entry point for static hosting
├── assets/css/app.css          # all styling
├── assets/js/                  # config, core, camera, zone, evidence, monitor, storage, app
├── backend/                    # optional FastAPI + SQLite (app.py, db.py, schemas.py, tests)
├── tests/                      # node:test + jsdom suites
├── docs/
│   ├── README.md               # documentation index, status matrix, conventions
│   ├── 01..15_*.md             # canonical numbered specs + implementation ledger
│   └── hackathon/              # submission brief and judge Q&A
├── README.md  CONTRIBUTING.md  CHANGELOG.md  .gitignore  package.json
```

## Documentation map
Start with [docs/01_PRODUCT_REQUIREMENTS.md](docs/01_PRODUCT_REQUIREMENTS.md), then architecture, MVP scope, stack, data/ML, API, database, security, testing, deployment and roadmap. [docs/README.md](docs/README.md) lists all fifteen documents by theme; [docs/15_IMPLEMENTATION_STATUS.md](docs/15_IMPLEMENTATION_STATUS.md) records what code exists today.

Submission-specific material derived from the team handbook and the judge-ready slide deck lives in [docs/hackathon/](docs/hackathon/). The source PDFs are submission artifacts and are not committed by default.

## Branches
`main` currently holds only a placeholder README; `master` holds the demo `index.html` and documentation. This development line is based on `master`. See [CONTRIBUTING.md](CONTRIBUTING.md) before branching.

## Terminology
Use "review-ready incident record." Do not claim legal admissibility, automatic guilt, automatic fines, field accuracy or official integration without proof and permission.
