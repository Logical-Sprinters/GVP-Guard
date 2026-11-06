# Judge Questions & Shared Team Rules

Canonical answers from §14 of the A4 team handbook. Every member should use these wording and the same technology-status labels. Related: [SUBMISSION_BRIEF.md](SUBMISSION_BRIEF.md), [../README.md](../README.md) (status matrix), [../13_DEMO_AND_ACCEPTANCE.md](../13_DEMO_AND_ACCEPTANCE.md), [../14_TEAM_WORKFLOW.md](../14_TEAM_WORKFLOW.md) (roles), [../16_TEAM_ROSTER_AND_OWNERSHIP.md](../16_TEAM_ROSTER_AND_OWNERSHIP.md) (roster & Q&A owners).

## Question ownership (settled roster: 4 roles × 2 members)

Each question below has an owning role that rehearses and fields it; the answers are canonical and stay verbatim for everyone. The Team Lead (Omkar Solat) can field any question, and every member must know all six answers well enough to defer correctly. Full ownership rationale: [../16_TEAM_ROSTER_AND_OWNERSHIP.md](../16_TEAM_ROSTER_AND_OWNERSHIP.md).

| # | Question | Owner role | Support |
|---|----------|------------|---------|
| 1 | How do you distinguish dumping from parking? | AI / Vision / Data | Integration / Testing |
| 2 | What if the plate is unreadable? | AI / Vision / Data | Backend / Database / Evidence |
| 3 | Does the system issue fines automatically? | Backend / Database / Evidence | Team Lead |
| 4 | What is working now? | Integration / Testing | Frontend / UI / UX |
| 5 | Where is the data from? | AI / Vision / Data | Backend / Database / Evidence |
| 6 | Why use edge processing later? | Backend / Database / Evidence | AI / Vision / Data |

## Canonical answers

**How do you distinguish dumping from parking?** — *owner: AI / Vision / Data*
A stop is only a trigger. Supporting cues such as object transfer and before/after scene change are checked, and an officer makes the final decision.

**What if the plate is unreadable?** — *owner: AI / Vision / Data*
We keep the clip, vehicle details, time and partial plate, and mark the incident for manual review. We do not invent a plate number.

**Does the system issue fines automatically?** — *owner: Backend / Database / Evidence*
No. It prepares a review-ready incident. An authorized officer decides the next action under the official process.

**What is working now?** — *owner: Integration / Testing*
Video upload, evidence frames, scene comparison, incident records, officer actions, history, GVP map and structured record export. Vehicle AI and night ANPR remain demo-stage.

**Where is the data from?** — *owner: AI / Vision / Data*
Controlled permitted recordings and legally usable public footage. Gandhidham tuning requires GMC-approved footage during a pilot.

**Why use edge processing later?** — *owner: Backend / Database / Evidence*
It can reduce continuous video upload by sending only triggered clips. Camera capacity and cost will be benchmarked before deployment claims.

## Final shared statement

> GVP-Guard does not replace municipal officers. It helps them find, review and act on suspected dumping incidents faster and more consistently.

## Terminology table

| Use | Avoid |
|-----|-------|
| Review-ready evidence package | Legally admissible evidence |
| Structured incident record | Proof of guilt |
| Officer-approved action | Automatic fine |
| Pilot target | Guaranteed result |
| GVP priority score | Accurate future-event prediction |

Additional rules:
- Say "controlled-footage workflow demonstration" for the current prototype; no field accuracy is claimed.
- Say "proposed next-stage stack" unless a component is actually shown working in the prototype.
- Pilot targets must be labelled as targets, not achievements. Never publish accuracy or impact percentages without documented tests.
- Do not claim GMC camera access, registry integration, legal chain of custody or citywide readiness.
- Never use a fixed label in a demo that implies real detection.

## Before presenting

Every member should read the handbook once (`01`–`06` plus their assigned role), understand the current prototype, know their role and rehearse these answers. Each role rehearses the questions it owns in the table above with its co-owner. All eight members must quote the same status labels, the same timeline and the same one-line pitch.
