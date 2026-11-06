# Documentation Index

Canonical project documentation for GVP-Guard: NightEye AI. The numbered files are the source of truth for the specification; this file is the navigation and status map.

## Read in this order

| # | Document | What it answers |
|---|----------|-----------------|
| 01 | [Product Requirements](01_PRODUCT_REQUIREMENTS.md) | Problem, users, goal, functional/non-functional requirements, success metrics |
| 02 | [System Architecture](02_SYSTEM_ARCHITECTURE.md) | Components, incident state machine, edge/cloud boundary, failure paths |
| 03 | [MVP Scope & Definition of Done](03_MVP_SCOPE.md) | MVP-0/1/2 boundaries, exclusions, done criteria |
| 04 | [Proposed Technology Stack](04_TECH_STACK.md) | Proposed vision, backend, data, frontend and quality tooling |
| 05 | [Data & ML Plan](05_DATA_AND_ML_PLAN.md) | Event taxonomy, annotation, dataset split, ANPR strategy, metrics |
| 06 | [API Specification](06_API_SPEC.md) | Draft `/api/v1` endpoints and API rules |
| 07 | [Database Schema](07_DATABASE_SCHEMA.md) | Draft tables, constraints, storage model |
| 08 | [Security, Privacy & Responsible AI](08_SECURITY_PRIVACY.md) | Threats, controls, evidence-integrity limits |
| 09 | [Testing Strategy](09_TESTING_STRATEGY.md) | Test levels, golden scenarios, severity, test records |
| 10 | [Deployment Runbook](10_DEPLOYMENT_RUNBOOK.md) | Environments, checks, rollback, pilot checklist |
| 11 | [Development Roadmap](11_DEVELOPMENT_ROADMAP.md) | Phases 0–6 and expansion gate |
| 12 | [Prioritized Backlog](12_BACKLOG.md) | P0–P5 work items and issue template rule |
| 13 | [Demo & Acceptance Plan](13_DEMO_AND_ACCEPTANCE.md) | Controlled/live demo script, honesty rules, release checklist |
| 14 | [Team Workflow & Ownership](14_TEAM_WORKFLOW.md) | Four roles × two members, responsibilities, RACI, backup/escalation, DoR/DoD, weekly rhythm, Git workflow for protected `master` |
| 15 | [Implementation Status](15_IMPLEMENTATION_STATUS.md) | What code exists today, test commands, open decisions |
| 16 | [Team Roster & Ownership](16_TEAM_ROSTER_AND_OWNERSHIP.md) | Confirmed roster (2026-11-06), primary/co-owner per role, file & directory ownership, deliverables, judge-Q&A owners, hand-off convention |

## By theme

- **Product & scope:** 01, 03
- **Architecture & engineering:** 02, 04, 05, 06, 07
- **Quality, security & operations:** 08, 09, 10
- **Planning & delivery:** 11, 12, 13
- **Team & governance:** 14, 16
- **Implementation ledger:** 15, [backend/README.md](../backend/README.md)
- **Step 4 readiness:** [STEP4_READINESS_PLAN.md](STEP4_READINESS_PLAN.md) — model weights, controlled dataset, benchmarking plan, go/no-go criteria (working document, not a canonical spec)
- **Hackathon submission:** [SUBMISSION_BRIEF.md](hackathon/SUBMISSION_BRIEF.md), [JUDGE_QA.md](hackathon/JUDGE_QA.md)
- **Repository governance:** root [README.md](../README.md), [CONTRIBUTING.md](../CONTRIBUTING.md), [CHANGELOG.md](../CHANGELOG.md)

## Current status matrix

The same distinction must be used in the docs, the deck, the demo and judge answers. **Current code status lives in [15_IMPLEMENTATION_STATUS.md](15_IMPLEMENTATION_STATUS.md)** — check it before quoting a feature in a presentation. Baseline from the team handbook is kept below for traceability.

| Status | Capabilities |
|--------|--------------|
| **WORKING** (MVP-0 + MVP-1 technical proof) | Recorded video **and live webcam**; editable GVP polygon; zone-limited pixel comparison; rolling evidence buffer with real JPEG frames; live scene-stability monitor (heuristic, **not** vehicle tracking); before/during/after evidence; incident record with canonical status codes, reviewer and comment; approve/reject/cleanup with audit rows; local history; GVP map with transparent priority score; JSON export containing real frame data; optional FastAPI + SQLite persistence via relative `/api/v1` URLs |
| **DEMO STAGE** | Tracking overlay (CSS box); editable plate candidate; the illustrative cue score and fixed 8% threshold, now explicitly labelled as uncalibrated heuristics |
| **PLANNED / NEXT STAGE** | Real vehicle detection and tracking; multi-cue dumping-event model; plate detector and multi-frame night ANPR/OCR; RTSP/CCTV input; authentication, roles, object storage, signed URLs, retention, observability |
| **FUTURE / EXTERNAL DEPENDENCY** | GMC-approved footage and camera access; vehicle-registry or e-challan integration; field pilot; citywide deployment |
| **EXPLICITLY OUT OF SCOPE** | Automatic guilt or fines, guaranteed offender identification, legally admissible evidence claims, face recognition, predictive policing, drone verification |

## Claim discipline

1. A stopped vehicle is only a suspected event. Never imply automatic guilt.
2. Label every feature as working, demo-stage, planned or externally dependent.
3. Do not publish accuracy, false-alert, impact or response-time percentages unless they come from documented tests with hardware, footage conditions and sample size recorded. Pilot targets are targets, not achievements.
4. Use `docs/hackathon/JUDGE_QA.md` for shared terminology; "review-ready incident record", never "legally admissible evidence".

## Consistency watchlist (status after the demo review)

These are mismatches found while consolidating the attachments. They are recorded here so they are not silently changed.

1. **Status labels (RESOLVED 2026-11-06):** `classify()` returns canonical `STATUS` codes (`SUSPICIOUS` / `CANDIDATE`); UI displays use `STATUS_LABEL` from `core.js`; the history table renders `STATUS_LABEL[x.status]`. Watchlist item resolved — UI and deck wording now aligned with the canonical enum.
2. **Roadmaps:** `11_DEVELOPMENT_ROADMAP.md` (phases 0–6), the handbook (5 stages) and the judge deck (NOW / 0–3 / 3–6 / 6–12 months) describe the same plan at different granularity. Reconcile before the final-round presentation so all eight members quote one timeline.
3. **PRD vs reality:** `01_PRODUCT_REQUIREMENTS.md` lists requirements without a status column; readers must cross-check the status matrix above before assuming anything is implemented.
4. **Branch policy (docs corrected, decision open):** `CONTRIBUTING.md` and `14_TEAM_WORKFLOW.md` now name protected `master` as the development base (updated 2026-11-06), but `main` is still GitHub's default branch and holds only a placeholder README. Confirm the long-term base branch with the team, then either switch the default branch or fold `master` into `main`.
5. **Team roster (RESOLVED 2026-11-06):** the team structure is settled as **4 roles × 2 members**; named assignments, file ownership and judge-Q&A owners live in `16_TEAM_ROSTER_AND_OWNERSHIP.md`, the workflow in `14_TEAM_WORKFLOW.md`, and the same roster table is mirrored in `hackathon/SUBMISSION_BRIEF.md`. Remaining follow-up: judge-deck slide 8 and the handbook still show the older one-person-per-role layout and must be regenerated (P0 in `12_BACKLOG.md`) — flagged, not silently rewritten. Omkar Solat keeps the Team Lead title (per handbook/deck) while sitting in the AI/Vision/Data pair; the title is kept separate from the Integration/Testing pair (Prince Rana + Sayantani Mandal).
6. **Demo hygiene (resolved for code):** injected Cloudflare scripts removed, history rows DOM-escaped, seeded records flagged `DEMO`, object URLs revoked, seek timeout added, heuristic score labelled as uncalibrated, and map counts now derive from real records. The fixed 8% threshold remains a labelled heuristic (MVP-2 replaces it); display wording is tracked in item 1.
7. **Binary artifacts:** the 16-page A4 handbook and the 8-slide judge-ready PDF are not committed; their canonical facts are mirrored in `hackathon/*.md`.
8. **Repo scaffolding (partly resolved):** `.gitignore`, `package.json`, a JS + Python test harness and `backend/requirements.txt` now exist. Issue templates, coding standards and LICENSE are still P0 items in `12_BACKLOG.md`.

## Conventions

- Numbered `docs/NN_*.md` files are canonical; edit in place, never renumber, and keep the numeric order meaningful.
- Draft documents are labelled "Draft" in their own title (06, 07, 10); proposed stacks are labelled "Proposed" (04).
- Add new documents to the tables above and record user-visible changes in `CHANGELOG.md`.
- Team, roster and ownership changes are recorded in `16_TEAM_ROSTER_AND_OWNERSHIP.md` via a PR approved by the Team Lead; the judge-facing docs (`14`, `16`, `hackathon/*`) must stay in sync with each other.
- Treat real-world claims (GMC permissions, field accuracy, legal admissibility) as requiring explicit evidence and authorization.
