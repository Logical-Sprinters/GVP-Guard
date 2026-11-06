# Team Roster and Ownership

**Confirmed by the team on 2026-11-06.** This roster is the single source of truth for who is on the team, which role each member holds, and who owns which file, directory, deliverable and judge question. It **supersedes the one-person-per-role layout on judge-deck slide 8** (kept below as a historical record) and the earlier unnamed "four pairs / eight individual roles" list that `14_TEAM_WORKFLOW.md` used to contain.

Related: [14_TEAM_WORKFLOW.md](14_TEAM_WORKFLOW.md) (how the team works: RACI, Git workflow, DoR/DoD) · [hackathon/SUBMISSION_BRIEF.md](hackathon/SUBMISSION_BRIEF.md) (competition facts) · [hackathon/JUDGE_QA.md](hackathon/JUDGE_QA.md) (canonical answers).

## Confirmed roster — 4 roles × 2 members

Team TM004162, P. P. Savani University, Surat — the same eight members named on judge-deck slide 8, reassigned into four role streams of two.

| # | Role | Primary owner | Co-owner (first backup) |
|---|------|---------------|-------------------------|
| 1 | **AI / Vision / Data** | **Omkar Solat** *(also Team Lead)* | **Prafull Mayank Singh** |
| 2 | **Backend / Database / Evidence** | **Shivansh Gupta** | **Jay Katkar** |
| 3 | **Frontend / UI / UX** | **Janed Patel** | **Smeet Jariwala** |
| 4 | **Integration / Testing** | **Prince Rana** | **Sayantani Mandal** |

Ordering convention: within each role, the first-listed member is the **primary owner** and the second is the **co-owner**; each is the other's first backup ([14_TEAM_WORKFLOW.md](14_TEAM_WORKFLOW.md) — backup and escalation).

### Team Lead

- **Omkar Solat remains Team Lead** per the team handbook and the judge-deck cover. The Team Lead title is a cross-cutting coordination role (scope decisions, cross-role contract disputes, claim-discipline enforcement, deck approval) and is kept **separate** from the Integration/Testing pair.
- His working pair under the settled roster is **AI / Vision / Data** with Prafull Mayank Singh; **Integration / Testing is Prince Rana + Sayantani Mandal**.
- **Flagged contradiction (not silently rewritten):** the handbook and deck slide 8 previously listed Omkar Solat as "Team Lead & Integration". The deck still shows that older layout and must be regenerated before the final round (P0 item in [12_BACKLOG.md](12_BACKLOG.md)). No new lead has been invented; if this contradiction must be resolved differently, it is escalated to the team, not edited unilaterally.

## File and directory ownership

Primary = role accountable for the path; co-owner = role consulted on changes and second reviewer source. Ownership transfers happen only via a PR that updates this file, approved by the Team Lead.

| Path | Primary owner | Co-owner | Notes |
|------|---------------|----------|-------|
| `index.html` | Frontend / UI / UX | Integration / Testing | Semantic markup; demo-script touchpoints |
| `assets/css/app.css` | Frontend / UI / UX | — | All styling |
| `assets/js/core.js` | AI / Vision / Data | Integration / Testing | Pure logic; every change keeps `tests/core.test.js` green |
| `assets/js/config.js` | AI / Vision / Data | Frontend / UI / UX | Thresholds & buffer (AI); default polygon UX (Frontend) |
| `assets/js/camera.js` | Frontend / UI / UX | AI / Vision / Data | Source selection UX; frame-capture contract |
| `assets/js/zone.js` | Frontend / UI / UX | AI / Vision / Data | Editor UX; normalised-coordinate contract |
| `assets/js/evidence.js` | AI / Vision / Data | Backend / Database / Evidence | Frame buffer; export-bundle contract |
| `assets/js/monitor.js` | AI / Vision / Data | Frontend / UI / UX | Scene-stability heuristic; status display |
| `assets/js/storage.js` | Backend / Database / Evidence | Frontend / UI / UX | Dual-mode persistence client |
| `assets/js/app.js` | Frontend / UI / UX | all roles | Orchestration; every role's wiring touches it |
| `backend/` (incl. `test_db.py`, `backend/README.md`) | Backend / Database / Evidence | Integration / Testing | API, SQLite, schemas, endpoint docs |
| `tests/` | Integration / Testing | author's role | Harness owned by Integration; feature authors add cases |
| `docs/01`, `03`, `11`, `12` | Team Lead (Omkar Solat) | all roles | Scope, MVP boundaries, roadmap, backlog |
| `docs/02` | Backend / Database / Evidence | AI / Vision / Data | Architecture; edge/cloud boundary |
| `docs/04` | each role for its stack section | Team Lead (consolidation) | Proposed stack |
| `docs/05` | AI / Vision / Data | Backend / Database / Evidence | Data & ML plan, ANPR strategy |
| `docs/06`, `07` | Backend / Database / Evidence | Integration / Testing | API spec, DB schema |
| `docs/08` | Backend / Database / Evidence | Team Lead | Security, privacy, responsible AI |
| `docs/09` | Integration / Testing | all roles | Testing strategy |
| `docs/10` | Backend / Database / Evidence | Integration / Testing | Deployment runbook |
| `docs/13` | Integration / Testing | Frontend / UI / UX | Demo & acceptance plan |
| `docs/14`, `docs/16` (this file) | Team Lead (Omkar Solat) | all roles | Workflow & roster changes need Team Lead approval |
| `docs/15` | Integration / Testing | all roles | Implementation ledger; every merged PR updates it |
| `docs/hackathon/` | Team Lead (Omkar Solat) | Frontend / UI / UX, Integration / Testing | Submission facts; Q&A rehearsal |
| Root `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md` | Team Lead (Omkar Solat) | PR author | Author updates CHANGELOG in the same PR |
| Judge deck (PPT/PDF) + demo video — **not committed** | Frontend / UI / UX (build & design) | Integration / Testing (demo script & rehearsal); Team Lead (approval) | Slide 8 regeneration pending — see below |

## Deliverables per role

### AI / Vision / Data — Omkar Solat (Team Lead) + Prafull Mayank Singh
- **Merged / working:** zone-limited frame differencing, illustrative cue score (labelled uncalibrated heuristic), canonical `STATUS` enum mapping, transparent GVP priority score, collision-resistant incident IDs, report builder with honesty notices, rolling 30-frame evidence buffer, live scene-stability monitor; 11 pure-logic unit tests over this code.
- **Documentation:** `docs/05_DATA_AND_ML_PLAN.md` (event taxonomy, annotation, dataset split, ANPR strategy, metrics discipline).
- **Planned / deferred:** **step 4 — YOLO-class vehicle detection + ByteTrack/IoU tracking, vehicle stop timer, multi-cue dumping-event model, plate detection and multi-frame night ANPR/OCR.** Deferred by team decision: requires model weights, a controlled dataset and a benchmarking plan. No detection/tracking/ANPR capability may be claimed until it is merged and demonstrated.

### Backend / Database / Evidence — Shivansh Gupta + Jay Katkar
- **Merged / working:** FastAPI service serving static app **and** `/api/v1` on one origin (relative URLs — no CORS, no `localhost` calls from the client); SQLite `incidents` / `decisions` / `audit_events`; Pydantic request schemas; endpoints per `docs/06_API_SPEC.md` (health, incidents CRUD-ish, decision, audit, export, GVPs, summary); `storage.js` dual-mode client with offline `localStorage` fallback; `backend/test_db.py` (5 tests); endpoint reference in `backend/README.md`.
- **Documentation:** `docs/06`, `docs/07`, `docs/02` (shared), `docs/10` (shared).
- **Planned:** authentication and roles, object storage with signed evidence URLs, retention/deletion jobs, checksums/chain-of-custody tooling, rate limiting, structured observability (backlog P4). Nothing here may be described as working today.

### Frontend / UI / UX — Janed Patel + Smeet Jariwala
- **Merged / working:** 4-tab semantic shell with no external scripts/fonts/network calls; recorded-file **and** live-webcam input with object-URL cleanup and seek timeout; editable normalised GVP polygon (add/drag vertices, save/reset); history with DOM-escaped fields (XSS fix); reviewer/comment fields; approve/reject/cleanup decision UI; dynamic GVP map counts; JSON export view; demo-stage overlays (CSS tracking box, editable plate candidate) clearly labelled as demo-stage.
- **Documentation:** demo UI flow inside `docs/13` (shared with Integration / Testing).
- **Planned:** freeze display labels ("Probable dumping" / "Ambiguous" / "REVIEW REQUIRED") against the canonical `STATUS` enum — watchlist item 1, owned jointly with AI/Vision/Data and Backend; officer-dashboard hardening; accessibility; live CCTV view once RTSP input exists.

### Integration / Testing — Prince Rana + Sayantani Mandal
- **Merged / working:** `tests/core.test.js` + `tests/ui.test.js` (14 JS tests total: pure logic, offline boot, XSS-safe rendering, API-mode detection); green-run discipline for `python3 -m unittest backend.test_db -v` (5 tests); dual run-mode verification (offline static + full API); `docs/15_IMPLEMENTATION_STATUS.md` code ledger; release acceptance checklist and demo script with recorded fallback for every live step (`docs/13`).
- **Documentation:** `docs/09`, `docs/13`, `docs/15`.
- **Planned:** automate the seven golden scenarios as video tests; pilot KPI measurement harness (correct plate-read rate, false alerts per camera-hour, alert-to-action time, evidence completeness, dumping-event precision — **targets to measure, never published figures without documented tests**); weekly judge-Q&A rehearsal.

## Judge Q&A ownership

Each canonical question in [hackathon/JUDGE_QA.md](hackathon/JUDGE_QA.md) has an owning role that rehearses and fields it (answers stay verbatim in that file). The Team Lead can field any question; every member must know all six answers well enough to defer correctly.

| # | Question | Owner role | Support |
|---|----------|------------|---------|
| 1 | How do you distinguish dumping from parking? | AI / Vision / Data | Integration / Testing (event→decision flow) |
| 2 | What if the plate is unreadable? | AI / Vision / Data (ANPR honesty) | Backend / Database / Evidence (record retention) |
| 3 | Does the system issue fines automatically? | Backend / Database / Evidence (decision + audit enforcement) | Team Lead |
| 4 | What is working now? | Integration / Testing (nothing is "working" without a demo or merged code) | Frontend / UI / UX |
| 5 | Where is the data from? | AI / Vision / Data (`docs/05` data plan) | Backend / Database / Evidence |
| 6 | Why use edge processing later? | Backend / Database / Evidence (`docs/02` edge/cloud boundary) | AI / Vision / Data |

## Hand-off convention

1. **Inside a role:** the co-owner is the first backup. When work moves between the two members, the receiving member is named in the PR description; no roster edit is needed.
2. **Absence:** the co-owner absorbs the primary's in-flight items; if both members of a role are unavailable, the Team Lead assigns a temporary owner from another role and records it in this file via PR.
3. **Cross-role hand-off** (e.g., AI/Vision/Data hands an evidence-schema change to Backend): the change travels as a PR touching the affected files **plus** the `docs/15` ledger entry, reviewed by the receiving role. Shared contracts (API shape, `STATUS` enum, evidence schema, threshold semantics) are never changed unilaterally.
4. **Ownership transfer** of any path in the table above: only via a PR editing this file, approved by the Team Lead, noted in `CHANGELOG.md`.
5. **Hand-offs keep claim discipline:** the receiving member inherits the labels (WORKING / DEMO STAGE / PLANNED / EXTERNAL DEPENDENCY) as documented — never upgraded in transit.
6. **Deck/demo hand-off:** Frontend / UI / UX builds the deck; Integration / Testing supplies the demo script, rehearsal and recorded fallback; the Team Lead approves anything shown externally.

## Superseded layout — historical record (do NOT use)

Judge-deck slide 8 (`GVP_Guard_Judge_Ready_v2 (1).pdf`, not committed) still shows the older one-person-per-role layout. It is recorded here for traceability only; the confirmed 4×2 roster above supersedes it, and slide 8 must be regenerated to show **4 streams with 2 names each** before the final round.

| Old slide-8 line | Old responsibility | Now part of |
|------------------|--------------------|-------------|
| Omkar Solat (TL) | Team Lead & Integration | Team Lead (title kept) + AI / Vision / Data pair |
| Prince Rana | Vehicle Detection & Tracking | Integration / Testing pair |
| Sayantani Mandal | Event Logic & Data | Integration / Testing pair |
| Smeet Jariwala | Dashboard & User Experience | Frontend / UI / UX pair |
| Shivansh Gupta | Backend & Evidence Records | Backend / Database / Evidence pair |
| Jay Katkar | ANPR & Image Processing | Backend / Database / Evidence pair |
| Janed Patel | Testing & Evaluation | Frontend / UI / UX pair |
| Prafull Mayank Singh | Video, Design & Documentation | AI / Vision / Data pair |

## Change record

| Date | Change | Approved by |
|------|--------|-------------|
| 2026-11-06 | Roster settled as 4 roles × 2 members with the assignments above; this file created; `docs/14` rewritten; deck slide 8 regeneration flagged (not performed). | Team (Team Lead: Omkar Solat) |
