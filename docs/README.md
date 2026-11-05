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
| 14 | [Team Workflow & Ownership](14_TEAM_WORKFLOW.md) | Four pairs, eight roles, Git workflow, definitions |

## By theme

- **Product & scope:** 01, 03
- **Architecture & engineering:** 02, 04, 05, 06, 07
- **Quality, security & operations:** 08, 09, 10
- **Planning & delivery:** 11, 12, 13, 14
- **Hackathon submission:** [SUBMISSION_BRIEF.md](hackathon/SUBMISSION_BRIEF.md), [JUDGE_QA.md](hackathon/JUDGE_QA.md)
- **Repository governance:** root [README.md](../README.md), [CONTRIBUTING.md](../CONTRIBUTING.md), [CHANGELOG.md](../CHANGELOG.md)

## Current status matrix

The same distinction must be used in the docs, the deck, the demo and judge answers. Source of truth: the "Current Prototype Status" table in the team handbook and the "Pipeline Readiness" panel in `index.html`.

| Status | Capabilities |
|--------|--------------|
| **WORKING** (MVP-0 browser demo) | Video upload/playback; before/during/after frame extraction; pixel-based scene comparison; incident ID, timestamp and editable plate field; approve/reject/cleanup actions; local incident history; illustrative GVP map; JSON incident export |
| **DEMO STAGE** | Vehicle tracking overlay; suspicious-stop workflow; editable plate candidate |
| **PLANNED / NEXT STAGE** | Live webcam/RTSP input; real vehicle detection and tracking; multi-cue dumping-event model; GVP polygon editor; multi-frame night ANPR and OCR; backend persistence, authentication, roles, audit, object storage |
| **FUTURE / EXTERNAL DEPENDENCY** | GMC-approved footage and camera access; vehicle-registry or e-challan integration; field pilot; citywide deployment |
| **EXPLICITLY OUT OF SCOPE** | Automatic guilt or fines, guaranteed offender identification, legally admissible evidence claims, face recognition, predictive policing, drone verification |

## Claim discipline

1. A stopped vehicle is only a suspected event. Never imply automatic guilt.
2. Label every feature as working, demo-stage, planned or externally dependent.
3. Do not publish accuracy, false-alert, impact or response-time percentages unless they come from documented tests with hardware, footage conditions and sample size recorded. Pilot targets are targets, not achievements.
4. Use `docs/hackathon/JUDGE_QA.md` for shared terminology; "review-ready incident record", never "legally admissible evidence".

## Consistency watchlist (open work, not yet resolved)

These are mismatches found while consolidating the attachments. They are recorded here so they are not silently changed.

1. **Status labels:** `02_SYSTEM_ARCHITECTURE.md` uses `CANDIDATE → SUSPICIOUS → REVIEW_REQUIRED → APPROVED/REJECTED/CLEANUP_REQUESTED → CLOSED`; the handbook uses Normal / Suspicious halt / Probable event / Low confidence; the demo UI uses "Probable dumping", "Ambiguous", "REVIEW REQUIRED", "Cleanup requested". `12_BACKLOG.md` P0 already calls for freezing these labels.
2. **Roadmaps:** `11_DEVELOPMENT_ROADMAP.md` (phases 0–6), the handbook (5 stages) and the judge deck (NOW / 0–3 / 3–6 / 6–12 months) describe the same plan at different granularity. Reconcile before the final-round presentation so all eight members quote one timeline.
3. **PRD vs reality:** `01_PRODUCT_REQUIREMENTS.md` lists requirements without a status column; readers must cross-check the status matrix above before assuming anything is implemented.
4. **Branch policy:** the original `CONTRIBUTING.md` and `14_TEAM_WORKFLOW.md` assume a protected `main`, but `main` currently contains only a placeholder README while `master` holds the demo. Confirm the long-term base branch with the team.
5. **Team roster:** `14_TEAM_WORKFLOW.md` lists eight roles (four pairs) without names; the judge deck names all eight members. Names are captured in `hackathon/SUBMISSION_BRIEF.md`.
6. **Demo hygiene:** `index.html` contains injected Cloudflare challenge/beacon script tags and a `seedHistory()` function that fabricates sample records. Remove the third-party scripts and clearly label seeded data before any submission or offline demo.
7. **Binary artifacts:** the 16-page A4 handbook and the 8-slide judge-ready PDF are not committed; their canonical facts are mirrored in `hackathon/*.md`.
8. **Repo scaffolding:** issue templates, coding standards, LICENSE and environment setup are still P0 items in `12_BACKLOG.md`.

## Conventions

- Numbered `docs/NN_*.md` files are canonical; edit in place, never renumber, and keep the numeric order meaningful.
- Draft documents are labelled "Draft" in their own title (06, 07, 10); proposed stacks are labelled "Proposed" (04).
- Add new documents to the tables above and record user-visible changes in `CHANGELOG.md`.
- Treat real-world claims (GMC permissions, field accuracy, legal admissibility) as requiring explicit evidence and authorization.
