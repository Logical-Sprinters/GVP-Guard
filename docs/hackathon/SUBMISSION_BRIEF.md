# Hackathon Submission Brief

Facts consolidated from the two attached submission artifacts. This file is the markdown mirror of the PDF-only information so the team can work from the repository alone.

## Source artifacts (not committed by default)

| Artifact | Pages | Content |
|----------|-------|---------|
| `GVP Plan.pdf` — "GVP-Guard: NightEye AI — Complete A4 Team Handbook" | 16 | 14-section team handbook: project overview, problem, scope, incident flow, architecture, prototype status, stack, dumping detection, night ANPR, data/testing/KPIs, impact/privacy, roadmap, eight roles, judge Q&A |
| `GVP_Guard_Judge_Ready_v2 (1).pdf` — "Judge-Ready Final" (exported from PowerPoint) | 8 | Official 8-slide synopsis for the Seva First Innovation Challenge 2026 |

Both are authored by Team TM004162. Binary PDFs stay outside Git unless the team explicitly decides to version them.

## Competition facts

- **Challenge:** Seva First Innovation Challenge 2026 — Education Dept, Govt. of Gujarat / SSIP 2.0
- **Track category:** College
- **Problem statement code:** PS000048
- **Team ID:** TM004162
- **Institution:** P. P. Savani University, Surat, Gujarat
- **Team leader / project lead:** Omkar Solat
- **Current round:** Online round — PPT plus demonstration video
- **Current status:** Human-reviewed workflow proof of concept using controlled recorded footage

**One-line pitch:** GVP-Guard turns suspected night-time dumping events into review-ready evidence and faster municipal action.

## Ground context

Gandhidham is a logistics, timber-transit and warehousing hub. Timber scrap, commercial packaging and mixed waste are dumped at night on open plots, service lanes and bypass roads, creating chronic Garbage Vulnerable Points (GVPs). Patrol coverage is thin, CCTV review is manual, low-light footage often hides plates, and cleanup is frequently triggered only by a later complaint or inspection. Waste may already exist before a vehicle arrives, so vehicle presence alone cannot prove dumping.

**Citizen friction:** blocked drains and monsoon overflow, rodent/stray-cattle health risk, clearance long after dumping. **Blind-spot loop:** night dumping → unreadable plate → weak evidence → waste piles up → the GVP refills.

Primary users: GMC chief sanitary inspectors, solid-waste management officers, municipal enforcement squads, cleanup/dispatch teams. Beneficiaries: nearby residents, pedestrians and road users, commercial establishments, drainage and public-health services.

## Eight-slide synopsis (judge deck)

| Slide | Section | Core message |
|-------|---------|--------------|
| 1 | Cover | Problem code, team ID, institution, team leader, one-line positioning |
| 2 | Challenge definition | Root cause and citizen friction; the blind-spot loop; "a stopped vehicle is not automatically guilty" |
| 3 | Solution approach | Convert recorded night footage into a review-ready incident; stop = suspected event, officer decides |
| 4 | System architecture | Five-step on-site/command-centre pipeline, alert logic, trust and fallback rules |
| 5 | Engineering stack | Four readiness blocks: video & evidence (working), AI pipeline (demo-stage), incident records (working), officer dashboard (working); dependencies |
| 6 | Impact assessment | Cleaner locations, safer surroundings, faster review, better resource use; pilot KPIs to be measured |
| 7 | Execution timeline | NOW → months 0–3 → 3–6 → 6–12 → validated expansion |
| 8 | Squad capabilities | Eight named members, each with a visible deliverable — *slide to be regenerated for the settled 4-role × 2 roster; see the roster note below* |

## Component readiness and dependencies

- **Working:** video upload/playback, before/during/after frames, pixel-based scene comparison, downloadable incident report, incident ID and timestamp, local history, officer decision audit, evidence review, approve/reject, cleanup request, GVP map.
- **Demo stage:** vehicle tracking overlay, suspicious-stop workflow, editable plate candidate.
- **Planned:** dumping cues, multi-frame ANPR, live CCTV feed.
- **Dependencies:** GMC-approved footage, camera access, field power/network and official workflow permissions. Scale only after measuring false alerts, plate reading, camera capacity and officer usability.

## Pilot KPIs (targets to measure, not achievements)

| KPI | What it measures |
|-----|------------------|
| Correct plate-read rate | Validated full or partial plate results |
| False alerts per camera-hour | Incorrect incidents generated during monitoring |
| Alert-to-action time | Time from incident creation to officer/cleanup action |
| Evidence completeness | Incidents containing all required evidence |
| Dumping-event precision / repeat incidents per GVP | Valid flagged events and recurring activity by location |

No accuracy or impact percentages may be published without documented tests that state hardware, footage conditions and sample size.

## Team roster (settled 2026-11-06 — 4 roles × 2 members)

The same eight members named on judge-deck slide 8, reassigned into four role streams of two:

| Role | Members |
|------|---------|
| AI / Vision / Data | Omkar Solat *(also Team Lead)*, Prafull Mayank Singh |
| Backend / Database / Evidence | Shivansh Gupta, Jay Katkar |
| Frontend / UI / UX | Janed Patel, Smeet Jariwala |
| Integration / Testing | Prince Rana, Sayantani Mandal |

Omkar Solat remains **Team Lead** per the team handbook and deck cover. The Team Lead title is kept separate from the Integration/Testing pair: his working pair is AI / Vision / Data, while Integration / Testing is Prince Rana + Sayantani Mandal.

> **Deck note (flagged, not silently rewritten):** slide 8 of `GVP_Guard_Judge_Ready_v2 (1).pdf` still shows the older one-person-per-role layout ("Team Lead & Integration", "Vehicle Detection & Tracking", …). It must be regenerated to show **4 streams with 2 names each** before the final round (P0 item in [../12_BACKLOG.md](../12_BACKLOG.md)). The historical slide-8 mapping is preserved in [../16_TEAM_ROSTER_AND_OWNERSHIP.md](../16_TEAM_ROSTER_AND_OWNERSHIP.md).

Full roster detail, file/directory ownership, deliverables and judge-Q&A owners: [../16_TEAM_ROSTER_AND_OWNERSHIP.md](../16_TEAM_ROSTER_AND_OWNERSHIP.md). Workflow, RACI, Git rules and definitions: [../14_TEAM_WORKFLOW.md](../14_TEAM_WORKFLOW.md).

## Timeline reconciliation note

Three granularities of the same plan are in circulation:

- `11_DEVELOPMENT_ROADMAP.md`: Phase 0 submission → 1 live MVP → 2 vehicle intelligence → 3 dumping/ANPR → 4 hardening → 5 pilot prep → 6 two-site pilot → expansion gate.
- Team handbook §12: Online round → next prototype → pilot preparation → two-site GMC pilot → validated expansion.
- Judge deck slide 7: NOW → months 0–3 model integration → 3–6 GMC pilot → 6–12 validated expansion.

The roadmap document is the engineering source of truth; the deck is the condensed presentation. Agree on one spoken version before judge Q&A. Expansion is always gated on false alerts, plate performance, usability, privacy, cost and response integration.

## Safeguards repeated in both artifacts

Human approval before enforcement; role-based access; audit log; policy-approved retention; only triggered clips uploaded where practical; uncertainty and confidence shown; manual review for unreadable plates and ambiguous events; official permission before registry/e-challan integration; no automatic fines, no face recognition, no prediction of future dumping.

See [JUDGE_QA.md](JUDGE_QA.md) for the canonical answers and terminology table.
