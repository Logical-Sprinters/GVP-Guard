# GVP-Guard — NightEye AI

**GVP-Guard turns suspected illegal-dumping events into review-ready incident records — evidence frames, time/location context and a plate candidate when available — so an authorized municipal officer can decide what happens next.**

A human-reviewed illegal-dumping incident and evidence platform for chronic Garbage Vulnerable Points (GVPs) created by night dumping in Gandhidham, Gujarat.

## Project identity

| | |
|---|---|
| **Repository** | <https://github.com/Logical-Sprinters/GVP-Guard> — development base: `master` |
| **Problem statement** | `PS000048` (illegal dumping / GVPs, Gandhidham) |
| **Team** | `TM004162` — 8 members in 4 roles × 2 (see [Team at a glance](#team-at-a-glance)) |
| **Institution** | P. P. Savani University, Surat, Gujarat |
| **Challenge** | Seva First Innovation Challenge 2026 — Education Dept, Govt. of Gujarat / SSIP 2.0 |
| **Track** | College |
| **Current maturity** | MVP-1 technical proof + MVP-2 pilot tooling + platform hardening (auth, RTSP, Docker, monitoring) |
| **Field status** | **Not validated in Gandhidham.** No measured accuracy, false-alert or impact figures exist or may be quoted. GMC-approved footage required for pilot. |

## Core rule (non-negotiable)

> **A stopped vehicle is not automatically guilty.** A stop only creates a *suspected event*; supporting cues **plus an authorized officer's review** are required before any action.
> No automatic fines · no guilt assumption · no legal-admissibility claims · no official (GMC / registry / e-challan) integration.

## How the prototype works

Recorded clip or live webcam / RTSP camera → GVP polygon → zone-limited analysis → rolling evidence buffer → incident record → officer decision:

1. **Input** — upload a recorded video file, start the live webcam, or connect an RTSP/CCTV camera (`assets/js/camera.js`).
2. **Zone** — draw and edit a normalised GVP polygon over the vulnerable point (`assets/js/zone.js`).
3. **Analysis** — zone-limited pixel differencing plus a live scene-stability monitor flag suspected events. The monitor is **explicitly a heuristic — not vehicle detection or tracking, not a vehicle stop timer, not a dumping model** (`assets/js/core.js`, `assets/js/monitor.js`).
4. **Evidence** — a rolling 30-frame buffer produces before/during/after JPEG frames. Evidence frames are stored in object storage with SHA-256 checksums, signed time-limited URLs, and a chain-of-custody access log (`assets/js/evidence.js`, `backend/db.py`, `backend/rtsp_capture.py`).
5. **Incident record** — canonical status code, trigger reasons, reviewer and comment fields, and an editable plate candidate (demo stage — no OCR/ANPR exists yet).
6. **Officer decision** — approve / reject / request cleanup; every decision writes an audit row. Requires authentication (officer+ role).
7. **Review surfaces** — local history, GVP map with a transparent priority score, JSON export, and optional server-side persistence via FastAPI + SQLite.

## Authentication & roles

| Role | Can view | Can write (create/decide/cleanup) | Can manage users |
|------|----------|-----------------------------------|------------------|
| Viewer | All read-only views | No | No |
| Officer | All read-only views | Yes | No |
| Admin | All views | Yes | Yes |

Write operations require sign-in; read operations work offline via `localStorage`. JWT bearer tokens secure all API write operations.

## RTSP/CCTV camera support

Connect to GMC-approved CCTV streams via Camera ID. The backend runs an OpenCV VideoCapture daemon with auto-reconnect and serves frames as same-origin MJPEG — the browser never calls RTSP directly. Real-time scene-stability alerts are pushed via Server-Sent Events (`GET /alerts/stream`).

## Status at a glance

The same labels are used everywhere (docs, deck, demo, judge answers). Full matrix: [docs/README.md](docs/README.md) · exact code ledger: [docs/15_IMPLEMENTATION_STATUS.md](docs/15_IMPLEMENTATION_STATUS.md).

| Status | Capabilities |
|--------|--------------|
| **WORKING** (MVP-1 technical proof) | Recorded video **and** live webcam input; editable GVP polygon; zone-limited pixel comparison; rolling evidence buffer with real JPEG frames; live scene-stability monitor (heuristic); before/during/after evidence; incident records with canonical status codes, reviewer and comment; approve/reject/cleanup with audit rows; local history; GVP map with transparent priority score; JSON export with real frame data; optional FastAPI + SQLite persistence over relative `/api/v1` URLs |
| **WORKING** (platform hardening, v0.9.0) | Authentication & roles (JWT, bcrypt); evidence object storage (SHA-256 checksums, signed URLs, chain-of-custody log); rate limiting (sliding window per IP); security headers (CSP, nosniff, X-Frame-Options DENY); RTSP/CCTV capture (OpenCV daemon, MJPEG, SSE alerts); Docker containerization (multi-stage, non-root); CI/CD pipeline (GitHub Actions); production monitoring (structured JSON logging, Prometheus metrics, health endpoint) |
| **DEMO STAGE** (labelled heuristics / placeholders) | CSS tracking overlay; editable plate candidate; illustrative cue score and fixed 8% zone-diff threshold — **uncalibrated heuristics** |
| **PLANNED** | Real vehicle detection/tracking (YOLO + ByteTrack), vehicle stop timer, multi-cue dumping-event model, plate detection and multi-frame night ANPR/OCR — **step 4 (detection/ANPR) is deferred** pending model weights, a controlled dataset and benchmarking |
| **EXTERNAL DEPENDENCY** | GMC-approved footage and camera access; field pilot; vehicle-registry / e-challan integration; citywide deployment |
| **OUT OF SCOPE** | Automatic guilt or fines; guaranteed offender identification; legally-admissible-evidence claims; face recognition; predictive policing |

## Run the prototype

No build step, no runtime dependencies, no external scripts/fonts/network calls — the page runs fully offline.

**Mode 1 — offline static (zero dependencies):**

```bash
python3 -m http.server 8000 --bind 0.0.0.0
```

The app detects the missing API and persists everything in `localStorage`.

**Mode 2 — Docker (recommended for deployment):**

```bash
# Build and start
docker compose up -d --build

# Open the application
open http://localhost:8000

# View logs
docker compose logs -f gvp-guard

# Stop
docker compose down
```

Set `GVP_SECRET_KEY` for production signing of JWT tokens and evidence URLs.

**Mode 3 — full app + API on one origin (manual):**

```bash
python3 -m pip install -r backend/requirements.txt
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/`. The header badge changes to "API persistence (SQLite)". One server serves both the static app and `/api/v1`, and browser code only ever calls **relative** URLs — so there is no CORS configuration and no `localhost` call from the client. Endpoint reference: [backend/README.md](backend/README.md).

**Monitoring endpoints:**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | Service health, dependency status, camera count |
| `GET /api/v1/metrics` | Prometheus-compatible metrics (request counts, latency, incidents, camera FPS) |

To exercise the workflow: use a controlled, permitted 20–30 second clip (or the webcam), edit the GVP zone, then run an analysis or live monitoring, review the evidence, and record an officer decision.

## MVP-2 pilot tooling

All tooling is built but requires **GMC-approved annotated footage** to execute:

| Deliverable | File | Status |
|-------------|------|--------|
| Seven golden scenarios (GS-01 to GS-07) | `tools/video_test_harness.py` + `tools/golden_scenarios_template.json` | Built — needs annotated footage |
| KPI measurement harness (Wilson score CIs) | `tools/kpi_harness.py` | Built — needs test data |
| Test record storage (append-only log) | `tools/test_record_storage.py` | Built |
| GMC permission workflow | `docs/GMC_PERMISSION_WORKFLOW.md` | Complete |
| Officer training materials | `docs/OFFICER_TRAINING_MATERIALS.md` | Complete |

No accuracy figures are published — all metrics require documented calibration tests on held-out footage.

## Tests

```bash
npm install && npm test                      # JS tests: pure-logic + jsdom UI/API-mode
python3 -m unittest backend.test_db -v       # SQLite tests
```

> **Node version note:** the JS suite is verified on **Node.js 22+**. On Node 20 the 11 pure-logic tests pass but `tests/ui.test.js` may crash at import. The Python suite has no third-party dependencies.

## Repository layout

```text
.
├── index.html                     # semantic markup; root entry point for static hosting
├── Dockerfile                     # multi-stage Docker build, non-root user, healthcheck
├── docker-compose.yml             # full stack with persistent gvp-data volume
├── .dockerignore                  # excludes Git, cache, node_modules, data, secrets
├── assets/
│   ├── css/app.css                # all styling
│   └── js/                        # 8 ES modules, no build step:
│       ├── config.js              #   thresholds, buffer size, API base, default polygon, auth keys
│       ├── auth.js                #   login/logout/register, JWT storage, fetchWithAuth
│       ├── core.js                #   DOM-free pure logic: geometry, zone diff, scoring, STATUS enum, report
│       ├── camera.js              #   file/webcam/RTSP sources, frame capture, safe seeking
│       ├── zone.js                #   editable normalised GVP polygon overlay
│       ├── evidence.js            #   rolling buffer, object-storage upload, signed URL download
│       ├── monitor.js             #   live scene-stability heuristic (NOT tracking / stop timer / dumping model)
│       ├── storage.js             #   localStorage ⇄ /api/v1 dual-mode persistence
│       └── app.js                 #   orchestration, DOM wiring, auth guards, SSE alerts
├── backend/                       # optional FastAPI + SQLite on one origin
│   ├── app.py                     #   API + monitoring + SSE alerts + RTSP endpoints
│   ├── auth.py                    #   JWT auth, password hashing, role-based deps
│   ├── db.py                      #   SQLite: incidents, decisions, audit, users, sessions, cameras, zones, evidence
│   ├── rtsp_capture.py            #   OpenCV VideoCapture RTSP daemon with auto-reconnect
│   ├── schemas.py                 #   Pydantic request/response models
│   ├── test_db.py                 #   dependency-free unittest suite
│   ├── requirements.txt           #   fastapi, uvicorn, pydantic, opencv-python-headless
│   └── README.md                  #   run + endpoint reference
├── tools/
│   ├── video_test_harness.py      #   seven golden scenarios
│   ├── kpi_harness.py             #   KPI metrics with Wilson score CIs
│   ├── test_record_storage.py     #   append-only test record log
│   ├── track_vehicles.py          #   ByteTrack tracking (DEMO STAGE)
│   ├── anpr_pipeline.py           #   plate OCR + dumping-event cue (DEMO STAGE)
│   └── ...                        #   calibration, association, weight download, dataset URLs
├── tests/                         # core.test.js (pure logic) + ui.test.js (jsdom)
├── docs/
│   ├── README.md                  # documentation index, status matrix, conventions, watchlist
│   ├── 01…13_*.md                 # canonical numbered specs (product → demo plan)
│   ├── 14_TEAM_WORKFLOW.md        # 4 roles × 2 members: responsibilities, RACI, Git workflow, DoR/DoD
│   ├── 15_IMPLEMENTATION_STATUS.md# code ledger and claim boundaries
│   ├── 16_TEAM_ROSTER_AND_OWNERSHIP.md # confirmed roster, file ownership, judge-Q&A owners
│   ├── GMC_PERMISSION_WORKFLOW.md # GMC permission request + footage handling
│   ├── OFFICER_TRAINING_MATERIALS.md # officer training guide
│   ├── MVP2_PLAN.md               # MVP-2 pilot & field validation plan
│   └── hackathon/                 # SUBMISSION_BRIEF.md + JUDGE_QA.md
├── README.md  CONTRIBUTING.md  CHANGELOG.md  .gitignore
└── package.json  package-lock.json # dev-only test tooling (jsdom); the app itself has no dependencies
```

## Documentation map

| Start here | Documents |
|------------|-----------|
| **Product & scope** | [01 Product Requirements](docs/01_PRODUCT_REQUIREMENTS.md) · [03 MVP Scope & DoD](docs/03_MVP_SCOPE.md) |
| **Architecture & engineering** | [02 Architecture](docs/02_SYSTEM_ARCHITECTURE.md) · [04 Tech Stack](docs/04_TECH_STACK.md) · [05 Data & ML Plan](docs/05_DATA_AND_ML_PLAN.md) · [06 API Spec](docs/06_API_SPEC.md) · [07 Database Schema](docs/07_DATABASE_SCHEMA.md) |
| **Quality, security & ops** | [08 Security/Privacy/Responsible AI](docs/08_SECURITY_PRIVACY.md) · [09 Testing Strategy](docs/09_TESTING_STRATEGY.md) · [10 Deployment Runbook](docs/10_DEPLOYMENT_RUNBOOK.md) |
| **Planning & delivery** | [11 Roadmap](docs/11_DEVELOPMENT_ROADMAP.md) · [12 Backlog](docs/12_BACKLOG.md) · [13 Demo & Acceptance](docs/13_DEMO_AND_ACCEPTANCE.md) |
| **Team** | [14 Team Workflow](docs/14_TEAM_WORKFLOW.md) · [16 Roster & Ownership](docs/16_TEAM_ROSTER_AND_OWNERSHIP.md) |
| **Truth about the code** | [15 Implementation Status](docs/15_IMPLEMENTATION_STATUS.md) · [backend/README.md](backend/README.md) |
| **Pilot & field** | [GMC Permission Workflow](docs/GMC_PERMISSION_WORKFLOW.md) · [Officer Training Materials](docs/OFFICER_TRAINING_MATERIALS.md) · [MVP-2 Plan](docs/MVP2_PLAN.md) |
| **Hackathon submission** | [Submission Brief](docs/hackathon/SUBMISSION_BRIEF.md) · [Judge Q&A + terminology](docs/hackathon/JUDGE_QA.md) |

[docs/README.md](docs/README.md) is the full index with the reading order, status matrix and consistency watchlist. The two source PDFs (16-page team handbook, 8-slide judge deck) are submission artifacts and are **not committed**; their facts are mirrored in `docs/hackathon/`.

## Team at a glance

Four roles, two members each (confirmed 2026-11-06). Workflow, RACI and Git rules: [docs/14_TEAM_WORKFLOW.md](docs/14_TEAM_WORKFLOW.md). Names, file ownership, deliverables and judge-Q&A owners: [docs/16_TEAM_ROSTER_AND_OWNERSHIP.md](docs/16_TEAM_ROSTER_AND_OWNERSHIP.md).

| Role | Members |
|------|---------|
| **AI / Vision / Data** | Omkar Solat *(also Team Lead)*, Prafull Mayank Singh |
| **Backend / Database / Evidence** | Shivansh Gupta, Jay Katkar |
| **Frontend / UI / UX** | Janed Patel, Smeet Jariwala |
| **Integration / Testing** | Prince Rana, Sayantani Mandal |

> **Team Lead note:** Omkar Solat remains Team Lead per the team handbook and judge deck. The Team Lead title is a cross-cutting coordination role and is kept **separate** from the Integration/Testing pair (Prince Rana + Sayantani Mandal). The deck's slide 8 still shows the older one-person-per-role layout and must be regenerated — it has not been silently rewritten. See [docs/16](docs/16_TEAM_ROSTER_AND_OWNERSHIP.md).

## Claim discipline

Every document, slide and demo answer in this repository follows these rules (full table: [docs/hackathon/JUDGE_QA.md](docs/hackathon/JUDGE_QA.md)):

- Say **\"review-ready incident record\"** — never "legally admissible evidence".
- Label every feature **WORKING / DEMO STAGE / PLANNED / EXTERNAL DEPENDENCY**.
- The live monitor is a **scene-stability heuristic** — not vehicle detection/tracking, not a stop timer, not a dumping model. The cue score and fixed 8% threshold are **uncalibrated heuristics**.
- **No accuracy, false-alert, impact or response-time percentages** without documented tests stating hardware, footage conditions and sample size. Pilot targets are targets, not achievements.
- Human review is mandatory: no automatic guilt, no automatic fines, no GMC/registry/e-challan integration, no claimed Gandhidham field validation.

## Branches & contributing

- `master` — the protected development base: application code, backend, tests and all documentation. All PRs target `master`.
- `main` — currently GitHub's default branch but holds **only a placeholder README**. Do not develop against it; the long-term base-branch decision is tracked in the [docs/README.md watchlist](docs/README.md).
- Workflow: short-lived `feat/…` / `fix/…` / `docs/…` branches → PR with tests/screenshots and known limitations → **one reviewer from another role** → squash merge. Full rules: [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/14_TEAM_WORKFLOW.md](docs/14_TEAM_WORKFLOW.md).
- Repo hygiene: `.gitignore`, `package.json` and test harnesses exist; issue templates, coding standards and a LICENSE are still P0 items in [docs/12_BACKLOG.md](docs/12_BACKLOG.md).

---

*Current maturity: MVP-1 technical proof + MVP-2 pilot tooling + platform hardening (auth, RTSP, Docker, monitoring). Step 4 (vehicle detection + multi-frame ANPR) is deferred. Nothing in this repository has been validated in the field.*
