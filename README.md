# GVP-Guard: NightEye AI

Human-reviewed illegal-dumping incident and evidence platform for PS000048.

## Project identity
- Team: TM004162
- Institution: P. P. Savani University, Surat, Gujarat
- Challenge: Seva First Innovation Challenge 2026 (Education Dept, Govt. of Gujarat / SSIP 2.0), College track
- Current maturity: browser-based workflow proof of concept
- Field status: not validated in Gandhidham

## Core rule
A stopped vehicle is not automatically guilty. Stop time only creates a suspected event; supporting cues and an authorized officer's review are required before action.

## Current prototype
Working: video upload, evidence-frame extraction, pixel-based scene comparison, incident ID/time, manual plate review, approve/reject/cleanup, local history, illustrative GVP map and JSON export.

Demo-stage/planned: real vehicle detection/tracking, dumping-event model, automatic multi-frame ANPR, backend/database, authentication, live CCTV and official integrations.

See [docs/README.md](docs/README.md) for the full working / demo-stage / planned status matrix.

## Run current prototype
The demo is the root-level `index.html`. It is a static page with no build step; incident history is stored only in the browser's `localStorage`.

```bash
cd /path/to/GVP-Guard
python3 -m http.server 8000 --bind 0.0.0.0
```

Open `http://localhost:8000/`. Use a controlled, permitted 20–30 second clip; choose the person/object or vehicle scenario and run the analysis.

## Repository layout
```text
.
├── index.html                  # MVP-0 browser demo (static, no dependencies)
├── README.md                   # project entry point
├── CONTRIBUTING.md             # contribution and claim-discipline rules
├── CHANGELOG.md                # release / change record
└── docs/
    ├── README.md               # documentation index, status matrix, conventions
    ├── 01..14_*.md             # canonical numbered specification documents
    └── hackathon/
        ├── SUBMISSION_BRIEF.md # competition facts, deck map, team roster, KPIs
        └── JUDGE_QA.md         # canonical judge answers and terminology
```

## Documentation map
Start with [docs/01_PRODUCT_REQUIREMENTS.md](docs/01_PRODUCT_REQUIREMENTS.md), then architecture, MVP scope, stack, data/ML, API, database, security, testing, deployment and roadmap. [docs/README.md](docs/README.md) lists all fourteen documents by theme.

Submission-specific material derived from the team handbook and the judge-ready slide deck lives in [docs/hackathon/](docs/hackathon/). The source PDFs are submission artifacts and are not committed by default.

## Branches
`main` currently holds only a placeholder README; `master` holds the demo `index.html`. This development line is based on `master`. See [CONTRIBUTING.md](CONTRIBUTING.md) before branching.

## Terminology
Use "review-ready incident record." Do not claim legal admissibility, automatic guilt, automatic fines, field accuracy or official integration without proof and permission.
