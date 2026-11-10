# MVP-2 Plan — Pilot & Field Validation

**Version:** 0.1  
**Date:** 2026-11-07  
**Owner:** Integration / Testing (Prince Rana + Sayantani Mandal) with all roles

## Scope

MVP-2 moves GVP-Guard from a controlled-technical-prototype (MVP-1) to a **pilot-ready system** with measurable KPIs, automated golden-scenario video tests, and a field validation framework. All Step 4 vehicle AI remains DEMO STAGE until benchmarked.

**Not in scope:** authentication, roles, object storage, GMC camera integration, automatic fines, e-challan, registry lookup.

## Deliverables

| # | Deliverable | Owner | Status |
|---|-------------|-------|--------|
| 1 | Seven golden scenarios automated as video tests | Integration / Testing | Planned |
| 2 | KPI measurement harness (plate-read rate, false alerts, alert-to-action time, evidence completeness, dumping-event precision) | Integration / Testing | Planned |
| 3 | Field validation framework (camera angle, night plate reading, false alerts per camera-hour, response time, cost) | All roles | Planned |
| 4 | GMC permission & approved footage workflow | Team Lead | Planned |
| 5 | Officer training materials | Frontend / UI / UX | Planned |
| 6 | Test record storage (dataset version, commit, model version, config, results, limitations) | Integration / Testing | Planned |

## Golden Scenarios (from docs/09)

1. **Normal pass** — no incident
2. **Long stop, no deposit** — review/reject
3. **Person deposits object** — probable event
4. **Waste already present** — do not blame arriving vehicle
5. **Plate unreadable** — incident retained without invented plate
6. **Network fails** — queue and later sync
7. **Duplicate event** — one incident only

## KPI Metrics (targets to measure, never publish without documented tests)

- Correct plate-read rate
- False alerts per camera-hour
- Alert-to-action time
- Evidence completeness (% incidents with before/during/after frames)
- Dumping-event precision
- Detection FPS and latency (Step 4 baseline: 5.2 FPS detection, 7.4 FPS tracking)

## Field Validation Conditions

- Camera angle (varied mounting heights and angles)
- Lighting (day, night, low light)
- Weather (rain, dust, glare)
- Vehicle types (car, bus, truck, motorcycle)
- Plate types (Indian state formats)
- Network loss (queue and later sync)

## Claim Discipline (Mandatory)

- No accuracy/false-alert/impact figures without documented tests
- Hardware, footage conditions, sample size recorded with every result
- Human review mandatory — no automatic fines
- Stop time alone does NOT imply guilt
- No GMC/registry/e-challan integration

## Acceptance Criteria

- [ ] All 7 golden scenarios pass as automated video tests
- [ ] KPI harness produces calibrated metrics with confidence intervals
- [ ] Field validation framework tested on ≥2 camera angles and ≥2 lighting conditions
- [ ] GMC permission workflow documented (who requests, who approves, footage retention)
- [ ] Officer training materials created (how to review, approve, reject, cleanup)
- [ ] Test record stored for every release (dataset version, commit, model version, config, results, limitations)
