# Prioritized Backlog

## P0 — Before technical expansion
- Freeze terminology and status labels ✅ DONE (2026-11-06)
- Add repository structure and environment setup ✅ DONE
- Add issue templates and coding standards ✅ DONE (CONTRIBUTING.md, .github/ISSUE_TEMPLATE/)
- Preserve current demo as a tagged release ✅ DONE (v0.9.0, v0.9.1, v0.9.2)
- Regenerate judge-deck slide 8 for the settled 4-role × 2-member roster (`16_TEAM_ROSTER_AND_OWNERSHIP.md`, confirmed 2026-11-06) — PENDING (Frontend/UI/UX pair to rebuild before final round; spec at `docs/JUDGE_DECK_SLIDE_8_SPEC.md` is NOT the actual slide deck)
- Step 4 readiness: acquire and verify model weights (YOLO11n/yolo11s), document controlled dataset collection protocol, and create benchmarking plan with go/no-go criteria ✅ DONE (`docs/STEP4_READINESS_PLAN.md`, `models/manifest.json`, `tools/download_weights.py`, `tools/benchmark_detection.py`)

## P1 — Live MVP ✅ DONE
- Webcam input ✅
- Baseline capture ✅
- GVP polygon editor ✅
- Motion and scene stability ✅
- Rolling evidence buffer ✅
- Incident persistence API ✅

## P2 — Vehicle AI ✅ CODE COMPLETE (DEMO STAGE)
- Detection benchmark ✅ `tools/benchmark_detection.py` — 11–16 FPS, 74–110ms on synthetic footage
- Tracking integration ✅ `tools/track_vehicles.py` — ByteTrack persistent track IDs
- Stop timer ✅ `assets/js/vehicle-detection.js` + `tools/track_vehicles.py`
- Region filtering ✅ GVP polygon-based zone filtering
- Track visualization ✅ `assets/js/vehicle-detection.js` detection overlay

## P3 — Event and ANPR ✅ CODE COMPLETE (DEMO STAGE)
- Annotation tool/schema ✅ `tools/ground_truth_template.json`, `docs/05_DATA_AND_ML_PLAN.md` annotation schema
- Controlled dataset ⚠️ PARTIAL — synthetic footage + real plate dataset (no full-vehicle GT, no person GT)
- Object-transfer cues ✅ `tools/anpr_pipeline.py` dumping-event cue (stopped vehicle + person overlap)
- Plate detector ❌ NOT DONE — EasyOCR on raw crops gives 0.0% exact match on real Indian plates; dedicated plate detector required
- Frame-quality score ❌ NOT DONE
- Multi-frame OCR ✅ `tools/anpr_pipeline.py` multi-frame consensus

## P4 — Platform ✅ DONE
- Authentication/roles ✅ JWT auth, RBAC (officer/admin/viewer)
- Evidence storage ✅ Object storage with SHA-256 checksums, signed URLs, chain-of-custody access log
- Audit history ✅ SQLite audit_events table
- Cleanup assignment ✅ Cleanup request workflow
- Notifications ✅ SSE alerting for scene-stability
- Observability ✅ Structured JSON logging, Prometheus-compatible /metrics, /health with camera status

## P5 — Pilot ❌ NOT STARTED (requires GMC permission)
- Permissions ❌ GMC approval pending for Gandhidham site
- Site/camera assessment ❌ Requires GMC-approved footage collection
- Baseline study ❌ Requires controlled dataset from permitted site
- Cost sheet ❌ NOT DONE
- Officer training ✅ `docs/OFFICER_TRAINING_MATERIALS.md`
- KPI dashboard ❌ NOT DONE (KPI harness exists at `tools/kpi_harness.py` but needs pilot data)

## Backlog rule
Every issue must contain problem, user value, acceptance criteria, owner, dependencies, estimate and test evidence.
