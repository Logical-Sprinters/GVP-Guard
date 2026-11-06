# Team Workflow and Ownership

Team structure **settled 2026-11-06**: four roles, two members each. This file supersedes the earlier "four pairs / eight individual roles" wording and the protected-`main` assumption. The named roster, file/directory ownership and judge-Q&A owners live in [16_TEAM_ROSTER_AND_OWNERSHIP.md](16_TEAM_ROSTER_AND_OWNERSHIP.md); this file defines **how the team works**.

## The 2-per-role rule

- The team is organised as **exactly 4 roles × exactly 2 members** — not eight individual roles, not a different role list.
- Every role has a **primary owner** (first-listed) and a **co-owner** (second-listed). Each is the other's first backup.
- Every deliverable, file and directory has two named owners through its role ([docs/16](16_TEAM_ROSTER_AND_OWNERSHIP.md)). No work item is single-person-owned.
- Role changes, swaps or ownership transfers happen only via a PR that updates `docs/16_TEAM_ROSTER_AND_OWNERSHIP.md`, approved by the Team Lead.

## Roles

| Role | Primary owner | Co-owner | Scope |
|------|---------------|----------|-------|
| **AI / Vision / Data** | Omkar Solat *(also Team Lead)* | Prafull Mayank Singh | Detection/cue logic, scene analysis, evidence-frame pipeline, data & ML plan, future detection + ANPR (deferred step 4) |
| **Backend / Database / Evidence** | Shivansh Gupta | Jay Katkar | FastAPI + SQLite service, `/api/v1` contract, incident/decision/audit persistence, evidence storage and export, future auth/storage/retention |
| **Frontend / UI / UX** | Janed Patel | Smeet Jariwala | `index.html`, styling, zone editor, camera input, dashboard/history/map UX, status-label display, demo UI flow |
| **Integration / Testing** | Prince Rana | Sayantani Mandal | Test harnesses, golden scenarios, cross-module integration checks, demo script + recorded fallback, release acceptance, `docs/15` ledger maintenance, judge-Q&A rehearsal |

> **Team Lead note (documented honestly):** Omkar Solat remains **Team Lead** per the team handbook and judge-deck cover. Under the settled roster his working pair is **AI / Vision / Data**, while **Integration / Testing is Prince Rana + Sayantani Mandal**. The Team Lead title is a cross-cutting coordination role, kept **separate** from the Integration/Testing pair. Judge-deck slide 8 still shows the older one-person-per-role layout (Omkar as "Team Lead & Integration"); it has **not** been silently rewritten and must be regenerated before the final round (tracked in [12_BACKLOG.md](12_BACKLOG.md) P0 and [hackathon/SUBMISSION_BRIEF.md](hackathon/SUBMISSION_BRIEF.md)).

## Responsibilities and deliverables per role

### AI / Vision / Data — Omkar Solat (Team Lead), Prafull Mayank Singh
- **Owns:** `assets/js/core.js` (geometry, zone-limited differencing, illustrative cue score, canonical `STATUS` enum, priority score, report builder), `monitor.js` (scene-stability heuristic), `evidence.js` (rolling frame buffer), analysis parameters in `config.js`, [05_DATA_AND_ML_PLAN.md](05_DATA_AND_ML_PLAN.md).
- **Delivers now:** unit-tested pure-logic modules; honest heuristic labelling (no detection/tracking/stop-timer/dumping-model claims); dataset & annotation plan upkeep.
- **Delivers next (PLANNED / deferred):** step 4 — YOLO-class detection + ByteTrack/IoU tracking, vehicle stop timer, multi-cue dumping-event model, multi-frame night ANPR/OCR with frame-quality scoring. **Deferred by team decision**: requires model weights, a controlled dataset and a benchmarking plan before any code.

### Backend / Database / Evidence — Shivansh Gupta, Jay Katkar
- **Owns:** `backend/` (FastAPI `app.py`, SQLite `db.py`, Pydantic `schemas.py`, `test_db.py`, endpoint docs), `assets/js/storage.js` (dual-mode persistence client), [06_API_SPEC.md](06_API_SPEC.md), [07_DATABASE_SCHEMA.md](07_DATABASE_SCHEMA.md), evidence export bundle contract.
- **Delivers now:** one-origin static + `/api/v1` service (relative URLs, no CORS, no `localhost` calls from the client); incidents/decisions/audit_events persistence; transparent priority scoring; offline-safe fallback.
- **Delivers next (PLANNED):** authentication and roles, object storage with signed evidence URLs, retention/deletion jobs, checksums, rate limiting, structured observability ([12_BACKLOG.md](12_BACKLOG.md) P4).

### Frontend / UI / UX — Janed Patel, Smeet Jariwala
- **Owns:** `index.html`, `assets/css/app.css`, `zone.js` (polygon editor UX), `camera.js` (source selection), `app.js` (orchestration, tabs, history, map, reviewer/comment fields, decision UI), XSS-safe rendering.
- **Delivers now:** 4-tab dashboard; editable normalised GVP polygon; recorded-file + webcam input; dynamic map counts; demo-stage overlays clearly labelled as such.
- **Delivers next (PLANNED):** freeze display labels against the canonical `STATUS` enum (with AI/Vision/Data and Backend — watchlist item 1), officer-dashboard hardening, accessibility pass, live CCTV view once RTSP input exists.

### Integration / Testing — Prince Rana, Sayantani Mandal
- **Owns:** `tests/` (11 pure-logic + 3 jsdom tests), the release acceptance checklist and demo script ([13_DEMO_AND_ACCEPTANCE.md](13_DEMO_AND_ACCEPTANCE.md)), [09_TESTING_STRATEGY.md](09_TESTING_STRATEGY.md), maintenance of [15_IMPLEMENTATION_STATUS.md](15_IMPLEMENTATION_STATUS.md).
- **Delivers now:** green test suites (`npm test` 14/14 on Node 22+, `python3 -m unittest backend.test_db -v` 5/5); cross-module integration checks; recorded fallback for every live demo step; the code ledger that keeps claims honest.
- **Delivers next (PLANNED):** automate the golden scenarios as video tests; KPI measurement harness for the pilot (targets only — no figures may be published without documented tests); judge-Q&A rehearsal loop.

## RACI

R = does the work · A = accountable (one per row) · C = consulted · I = informed. The Team Lead (Omkar Solat) holds A on cross-role conflicts and can field any judge question.

| Activity | AI/Vision/Data | Backend/DB/Evidence | Frontend/UI/UX | Integration/Testing | Team Lead |
|----------|:---:|:---:|:---:|:---:|:---:|
| Product scope, PRD & MVP-boundary changes (`01`, `03`) | C | C | C | C | **R/A** |
| Detection/cue/evidence-frame logic (`core.js`, `monitor.js`, `evidence.js`, `05`) | **R/A** | C | I | C (tests) | I |
| API, schema, persistence (`backend/`, `storage.js`, `06`, `07`, `10`) | C | **R/A** | I | C (tests) | I |
| UI/UX, status-label display, dashboard (`index.html`, `assets/`, `zone.js`, `app.js`) | C | C | **R/A** | C | I |
| Security & privacy controls (`08`) | C | **R** | C | C | **A** |
| Tests, demo script, release checklist (`tests/`, `09`, `13`) | C | C | C | **R/A** | I |
| Implementation ledger & claim boundaries (`15`) | C | C | C | **R** | **A** |
| Judge deck, submission artifacts, demo video | C | C | **R** (build/design) | C (rehearsal) | **A** (approval) |
| Roadmap & backlog grooming (`11`, `12`) | C | C | C | C | **R/A** |

## Backup and escalation

1. **First backup:** a member's co-owner in the same role absorbs their work when they are unavailable; the PR description notes the substitution.
2. **Role backup:** if a whole role is blocked or unavailable, the Team Lead reassigns a temporary owner from another role and records it in `docs/16` via PR.
3. **Escalation path:** member → co-owner → Team Lead. Anything blocking for more than one working day is escalated to the Team Lead.
4. **Cross-role contract disputes** (API shape, `STATUS` enum wording, evidence schema, threshold semantics) are escalated to the Team Lead immediately — these are shared contracts; neither role changes them unilaterally.
5. **Claim-disipline violations** (an unlabelled feature claim, an unmeasured percentage, admissibility wording) are stop-the-line issues: any member may raise them; the Team Lead resolves before the material is shown externally.

## Definition of Ready

A work item may enter a sprint only when:

- Problem and user value are clear, and acceptance criteria are written (issue-template fields per [12_BACKLOG.md](12_BACKLOG.md): problem, user value, acceptance criteria, owner, dependencies, estimate, test evidence).
- Dependencies and data are available or explicitly marked EXTERNAL DEPENDENCY.
- A **named owner pair** (role primary + co-owner) is assigned per `docs/16`.
- Claim labels for the expected outcome are agreed up front (WORKING / DEMO STAGE / PLANNED / EXTERNAL DEPENDENCY).

## Definition of Done

A work item is done only when **all** of the following hold (mirrors [03_MVP_SCOPE.md](03_MVP_SCOPE.md) and the [15_IMPLEMENTATION_STATUS.md](15_IMPLEMENTATION_STATUS.md) check):

- Working code merged to `master` through a PR with one reviewer from **another role**.
- Tests pass (`npm test`, `python3 -m unittest backend.test_db -v`) or a documented manual test is attached; new behaviour adds or updates tests.
- Error/fallback behaviour exists (offline mode, API failure, camera failure, seek timeout).
- Documentation updated in the same PR: `docs/15_IMPLEMENTATION_STATUS.md` ledger, `CHANGELOG.md` for user-visible changes, and any affected spec.
- Demonstration evidence attached (screenshot, recording or live demo) — **no member claims a feature is implemented without a working demonstration or merged code**.
- No claim beyond measured results: heuristics stay labelled as heuristics; no accuracy/impact figures without documented tests.

## Weekly rhythm

| When | What | Who |
|------|------|-----|
| Start of week | Planning: pick backlog items, confirm owner pairs, agree claim labels | All (Team Lead facilitates) |
| Continuous | Pair implementation inside each role; co-owner reviews first | Each role |
| Mid-week | Integration check: cross-module run-through of video → event → evidence → incident → decision, both run modes | Integration / Testing |
| Weekly | Status review: update the `docs/15` ledger, watchlist and backlog; metrics review (test counts, open P0s — never invented field figures) | Integration / Testing + Team Lead |
| End of week | Demo/rehearsal: run the `docs/13` demo script with recorded fallback; rehearse owned judge Q&A | All |

## Git workflow (org repository, protected `master`)

- **Base:** `master` is the protected development base of <https://github.com/Logical-Sprinters/GVP-Guard>. `main` holds only a placeholder README and is not developed against; the long-term base-branch decision is tracked in the [docs/README.md watchlist](README.md).
- **Branches:** short-lived branches from `master`, named `feat/…`, `fix/…`, `docs/…`. No long-running divergent branches; rebase or merge `master` in frequently.
- **Pull requests:** every change goes through a PR to `master` containing: what changed and why, test results or screenshots, and known limitations. Secrets, real personal data, real footage and stream credentials never enter commits.
- **Review:** **one reviewer from another role** than the author's (the author's co-owner may review first inside the role, but the merge-blocking review is cross-role). Docs-only PRs follow the same rule.
- **Merge:** squash-merge; keep `master` linear and green (tests pass) at all times.
- **Releases:** user-visible changes are recorded in [../CHANGELOG.md](../CHANGELOG.md) in the same PR.

## Communication rule

> **No member claims a feature is implemented without a working demonstration or merged code.**

- All members use the same terminology and the same technology-status labels — the Use/Avoid table in [hackathon/JUDGE_QA.md](hackathon/JUDGE_QA.md) is binding for docs, deck, demo and judge answers.
- Status vocabulary everywhere: **WORKING · DEMO STAGE · PLANNED · EXTERNAL DEPENDENCY · OUT OF SCOPE**.
- The live monitor is always described as a *scene-stability heuristic*, never as vehicle detection, tracking, a stop timer or a dumping model.
- Pilot KPIs are quoted as *targets to measure*, never as achievements; no percentage is published without documented tests (hardware, footage conditions, sample size).
- When documents disagree, nobody silently rewrites the other side: the contradiction is recorded in the [docs/README.md watchlist](README.md) and escalated to the Team Lead.
