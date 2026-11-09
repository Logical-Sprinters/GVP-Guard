# Contributing to GVP-Guard

Team TM004162, P. P. Savani University, Surat

## Team Structure

| Role | Primary Owner | Co-owner |
|------|---------------|----------|
| AI / Vision / Data (Team Lead) | Omkar Solat | Prafull Mayank Singh |
| Backend / Database / Evidence | Shivansh Gupta | Jay Katkar |
| Frontend / UI / UX | Janed Patel | Smeet Jariwala |
| Integration / Testing | Prince Rana | Sayantani Mandal |

See `docs/16_TEAM_ROSTER_AND_OWNERSHIP.md` for full roster, file ownership, and hand-off conventions.

## How to Contribute

1. **Create an issue** using the templates in `.github/ISSUE_TEMPLATE/`
   - Every issue needs: problem, user value, acceptance criteria, owner, dependencies, estimate, test evidence
2. **Create a branch** from `master`
   - Naming: `feat/<description>` or `fix/<description>` or `docs/<description>`
3. **Implement** your changes
   - Follow file ownership from `docs/16_TEAM_ROSTER_AND_OWNERSHIP.md`
   - Shared contracts (API shape, STATUS enum, evidence schema, threshold semantics) are never changed unilaterally
4. **Update `docs/15_IMPLEMENTATION_STATUS.md`** in the same PR
5. **Update `CHANGELOG.md`** in the same PR
6. **Run tests** before submitting
   - `npm test` (11/11 JS tests)
   - `python3 -m unittest backend.test_db -v` (10/10 Python tests)
7. **Open a PR** against `master`
   - PR author updates CHANGELOG in the same PR
   - Team Lead reviews and merges

## Claim Discipline (Mandatory)

- "Review-ready incident record" — never "legally admissible evidence"
- Label as WORKING / DEMO STAGE / PLANNED / EXTERNAL DEPENDENCY
- Live monitor is scene-stability heuristic, NOT vehicle detection/tracking/stop timer/dumping model
- No accuracy/impact percentages without documented tests
- Human review mandatory — no automatic fines
- No GMC/registry/e-challan integration

## Branch Policy

- `master` holds all code (default branch)
- `main` is a placeholder README
- All PRs merge to `master` via merge commits
- No force-push to `master`
