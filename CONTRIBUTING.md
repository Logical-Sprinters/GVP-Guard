# Contributing

1. Read the PRD (`docs/01_PRODUCT_REQUIREMENTS.md`) and MVP scope (`docs/03_MVP_SCOPE.md`).
2. Create an issue with acceptance criteria.
3. Branch from the current development base branch (confirm it with the lead; `master` currently holds the demo, while `main` is a placeholder). Use short-lived branches: `feat/...`, `fix/...`, `docs/...`.
4. Keep secrets, real personal data, real footage and stream credentials out of commits.
5. Add tests or a documented manual test.
6. Update relevant documentation.
7. Open a pull request with screenshots/results and known limitations.
8. Obtain one cross-pair review.

## Documentation conventions
- Canonical specifications are the numbered files in `docs/`; edit them in place and do not renumber them.
- Add an entry to `docs/README.md` when introducing a new document.
- Record user-visible changes in `CHANGELOG.md`.
- Keep the demo `index.html` at the repository root so static hosting continues to work.

## Commit examples
`feat(anpr): add frame quality scoring`
`fix(events): avoid duplicate incidents`
`docs(api): define cleanup request endpoint`

## Claim discipline
Documentation and demos must separate working, demo-stage, planned and external-dependency features. Never label a planned feature as implemented, never publish unmeasured accuracy or impact figures, and never claim legal admissibility or automatic enforcement. See `docs/hackathon/JUDGE_QA.md` for the shared terminology table.
