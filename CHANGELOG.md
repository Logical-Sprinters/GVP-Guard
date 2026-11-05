# Changelog

## [Unreleased] — Documentation baseline in the repository
### Added
- `docs/` with the fourteen canonical numbered specification documents
- `docs/README.md` documentation index, status matrix and conventions
- `docs/hackathon/SUBMISSION_BRIEF.md` and `docs/hackathon/JUDGE_QA.md` capturing the facts from the team handbook and judge-ready slide deck
- `.gitignore` for secrets, build output and local footage
- Repository layout and branching notes in `README.md` and `CONTRIBUTING.md`

### Fixed
- Corrected the demo run command: the prototype is the root-level `index.html`, not a `gvp_guard_demo` directory
- Made documentation links resolve to the new `docs/` paths
- Removed the assumption that `main` is the active development base

### Known documentation gaps
- Incident status labels are not yet identical across the PRD, architecture state machine, handbook and demo UI
- Roadmap granularity differs between the seven-phase roadmap, the five-stage handbook and the four-step deck timeline
- The demo still contains injected third-party Cloudflare scripts; removal is a separate code change

## [0.1.0] — Online-round workflow prototype
### Added
- Recorded-video upload
- Evidence frames and scene comparison
- Person/vehicle scenario selection
- Manual plate review
- Officer actions, history, map and JSON export
- Project documentation baseline

### Known limitations
- No real vehicle detector/tracker
- No automatic dumping model
- No automatic OCR/ANPR
- No backend persistence or authentication
- No Gandhidham field validation
