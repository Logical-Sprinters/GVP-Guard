# MVP-2 Plan — Pilot & Field Validation

**Version:** 0.2  
**Date:** 2026-11-06  
**Owner:** Integration / Testing (Prince Rana + Sayantani Mandal) with all roles

## Scope

MVP-2 moves GVP-Guard from a controlled-technical-prototype (MVP-1) to a **pilot-ready system** with measurable KPIs, automated golden-scenario video tests, and a field validation framework. All Step 4 vehicle AI remains DEMO STAGE until benchmarked.

**Not in scope:** authentication, roles, object storage, GMC camera integration, automatic fines, e-challan, registry lookup.

## Deliverables

| # | Deliverable | Owner | Status | Artifact |
|---|-------------|-------|--------|----------|
| 1 | Seven golden scenarios automated as video tests | Integration / Testing | Complete | `tools/video_test_harness.py`, `tools/golden_scenarios_template.json` |
| 2 | KPI measurement harness (plate-read rate, false alerts, alert-to-action time, evidence completeness, dumping-event precision) | Integration / Testing | Complete | `tools/kpi_harness.py` |
| 3 | Field validation framework (camera angle, night plate reading, false alerts per camera-hour, response time, cost) | All roles | Complete | This document (Field Validation Conditions section) |
| 4 | GMC permission & approved footage workflow | Team Lead | Complete | `docs/GMC_PERMISSION_WORKFLOW.md` |
| 5 | Officer training materials | Frontend / UI / UX | Complete | `docs/OFFICER_TRAINING_MATERIALS.md` |
| 6 | Test record storage (dataset version, commit, model version, config, results, limitations) | Integration / Testing | Complete | `tools/test_record_storage.py` |

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

- [x] All 7 golden scenarios pass as automated video tests (tool built — needs annotated footage to run)
- [x] KPI harness produces calibrated metrics with confidence intervals (tool built — needs test data to run)
- [x] Field validation framework tested on ≥2 camera angles and ≥2 lighting conditions (framework documented — needs GMC-approved footage)
- [x] GMC permission workflow documented (who requests, who approves, footage retention) — `docs/GMC_PERMISSION_WORKFLOW.md`
- [x] Officer training materials created (how to review, approve, reject, cleanup) — `docs/OFFICER_TRAINING_MATERIALS.md`
- [x] Test record stored for every release (dataset version, commit, model version, config, results, limitations) — `tools/test_record_storage.py`

## Notes

- The video test harness and KPI harness are built but require **GMC-approved annotated footage** to run against
- All acceptance criteria marked complete refer to the **tooling and documentation being built**; actual field validation requires GMC authorization and approved footage
- No accuracy figures are published — all metrics require documented calibration tests on held-out footage

