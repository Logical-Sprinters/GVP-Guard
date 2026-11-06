# Contributing

1. Read the PRD (`docs/01_PRODUCT_REQUIREMENTS.md`) and MVP scope (`docs/03_MVP_SCOPE.md`).
2. Create an issue with acceptance criteria.
3. Branch from `master` — the protected development base of the org repository (`main` currently holds only a placeholder README; the long-term base-branch decision is tracked in the `docs/README.md` watchlist). Use short-lived branches: `feat/...`, `fix/...`, `docs/...`.
4. Keep secrets, real personal data, real footage and stream credentials out of commits.
5. Add tests or a documented manual test.
6. Update relevant documentation (including the `docs/15_IMPLEMENTATION_STATUS.md` ledger for code changes).
7. Open a pull request with screenshots/results and known limitations.
8. Obtain one review from a member of **another role** (roles: AI/Vision/Data · Backend/Database/Evidence · Frontend/UI/UX · Integration/Testing — see `docs/14_TEAM_WORKFLOW.md`; named owners in `docs/16_TEAM_ROSTER_AND_OWNERSHIP.md`). Merge by squash; keep `master` green.

## Documentation conventions
- Canonical specifications are the numbered files in `docs/`; edit them in place and do not renumber them.
- Add an entry to `docs/README.md` when introducing a new document.
- Record user-visible changes in `CHANGELOG.md`.
- Keep the demo `index.html` at the repository root so static hosting continues to work.
- Record team, roster or ownership changes in `docs/16_TEAM_ROSTER_AND_OWNERSHIP.md` via a PR approved by the Team Lead, and keep the judge-facing docs (`docs/14`, `docs/16`, `docs/hackathon/*`) in sync with each other.

## Commit examples
`feat(anpr): add frame quality scoring`
`fix(events): avoid duplicate incidents`
`docs(api): define cleanup request endpoint`

## Claim discipline
Documentation and demos must separate working, demo-stage, planned and external-dependency features. Never label a planned feature as implemented, never publish unmeasured accuracy or impact figures, and never claim legal admissibility or automatic enforcement. See `docs/hackathon/JUDGE_QA.md` for the shared terminology table.
