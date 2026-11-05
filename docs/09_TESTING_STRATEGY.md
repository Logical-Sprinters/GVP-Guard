# Testing Strategy

## Test levels
- Unit: geometry, stop timer, frame scoring, plate formatting, priority score
- Integration: video -> event -> evidence -> incident -> decision
- API: validation, authorization, pagination and idempotency
- UI: upload, review, decisions, history and failure states
- Performance: FPS, latency, memory, storage and concurrent cameras
- Field: camera angle, glare, rain/dust, network loss and operator usability

## Golden scenarios
1. Normal pass — no incident
2. Long stop, no deposit — review/reject
3. Person deposits object — probable event
4. Waste already present — do not blame arriving vehicle
5. Plate unreadable — incident retained without invented plate
6. Network fails — queue and later sync
7. Duplicate event — one incident only

## Acceptance metrics
Set thresholds only after baseline tests. Always publish hardware, footage conditions, sample size and confidence intervals where appropriate.

## Bug severity
- P0: data loss/security/false automatic action
- P1: incident/evidence workflow broken
- P2: major incorrect result with fallback
- P3: UI or minor reporting issue

## Test record
Each release stores dataset version, commit, model version, configuration, results and known limitations.

## Test harness (2026-11-05)

- `npm install && npm test` — 14 Node tests: 11 pure-logic tests for geometry, zone-limited differencing, scoring, status mapping and report notices, plus 3 jsdom tests for offline boot, XSS-safe rendering, tab behaviour and API-mode detection.
- `python3 -m unittest backend.test_db -v` — 5 SQLite tests covering CRUD, decisions/audit, filters/summary, transparent priority scoring and clearing.

The golden scenarios above are not yet automated as video tests, and field tests still require GMC-approved footage. No accuracy or false-alert figures are published.
