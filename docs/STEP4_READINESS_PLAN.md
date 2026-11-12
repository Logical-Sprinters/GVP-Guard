# Step 4 Readiness Plan — Vehicle Detection + Multi-Frame ANPR

**Status:** Benchmarking complete (DEMO STAGE — prerequisites 1 partially met, 2–3 not yet met)  
**Owned by:** AI / Vision / Data (Omkar Solat, Prafull Mayank Singh)  
**Related:** `docs/05_DATA_AND_ML_PLAN.md`, `docs/04_TECH_STACK.md`, `docs/15_IMPLEMENTATION_STATUS.md`, `docs/12_BACKLOG.md`

Step 4 (YOLO/ByteTrack vehicle detection + multi-frame ANPR) remains **DEFERRED** per the team decision of 2026-11-06. It may only begin once all three prerequisites below are in place. This document defines what each prerequisite looks like and how to verify it.

## Benchmarking Results (2026-11-07, synthetic test footage)

Benchmarking was run on synthetic test footage (7 golden scenarios GS-01 to GS-07) using YOLO11n + ByteTrack + EasyOCR on CPU. All results are **DEMO STAGE** — not WORKING until validated on held-out real footage with annotated persons and plates.

| Scenario | Result | Max Stop | FPS | Notes |
|----------|--------|----------|-----|-------|
| GS-01 Normal pass | FAIL (stop measured 2.96s > 1.0s expected) | 2.96s | 14.1 | Car transits zone; polygon-based stop metric counts transit time |
| GS-02 Long stop, no deposit | PASS | 5.44s | 16.0 | Long stop correctly detected; no dumping cue (no person) |
| GS-03 Person deposits | FAIL (5.36s > 5.0s; no person detected) | 5.36s | 15.3 | Person overlap NOT detected — synthetic figures not seen by YOLO11n |
| GS-04 Waste present | FAIL (stop measured 2.2s > 1.0s expected) | 2.2s | 15.6 | Car transits zone past pre-existing waste |
| GS-05 Plate unreadable | FAIL (5.56s > 5.0s; no person detected) | 5.56s | 16.1 | Plate OCR: 0 reads (no readable plates in synthetic car crops) |
| GS-06 Network fails | FAIL (5.36s > 5.0s; no person detected) | 5.36s | 16.0 | Same person-detection limitation as GS-03 |
| GS-07 Duplicate event | PASS | 2.88s | 15.7 | Duplicate entry tracked as separate track |

**Summary:** 2/7 scenarios passed (28.6%). Vehicle detection and tracking work (11–16 FPS, 74–110ms/frame). Person detection and plate OCR not validated — requires real person/plate footage.

**Test records:** `tests/data/scenarios/test_records.json` (commit 92094a1, model yolo11n, dataset synthetic-v1)

## Prerequisite 1 — Model weights

| Component | Spec (docs/04) | Source / weights | Verification |
|-----------|----------------|------------------|--------------|
| Vehicle detector | Ultralytics YOLO11 nano/small | Download from Ultralytics (`yolo11n.pt` / `yolo11s.pt`) | ✅ Model loads and runs inference; car/truck/bus/motorcycle detected in test footage |
| Tracker | ByteTrack (IoU fallback) | Ultralytics `tracker` config | ✅ Track IDs persist across frames |
| Plate detector | Plate detector (OpenCV/YOLO) | To be selected after benchmarking | Not yet evaluated |
| OCR | EasyOCR (PaddleOCR backup) | `pip install easyocr` | ✅ Installed; no readable plates found in synthetic car crops |

**Action items:**
- Pin exact model versions and weight file hashes in a `models/manifest.json` (not committed — weights stay outside Git)
- Record download source, license, and date for each weight file
- Verify each model loads offline on the target hardware (Raspberry Pi / edge device or dev laptop)

> Weights are **not committed** to Git. Only the manifest + inference script are versioned.

### Weight file hashes

| File | SHA-256 | Source |
|------|---------|--------|
| `models/weights/yolo11n.pt` | `0ebbc80d4a7680d1...` | https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt |
| `models/weights/yolo11s.pt` | `85a76fe86dd8afe3...` | https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11s.pt |

## Prerequisite 2 — Controlled dataset

Per `docs/05_DATA_AND_ML_PLAN.md`: permitted location, clean boxes/bags, fixed camera, varied angles/light, negative scenarios, remove all staged material.

### Current status

Synthetic test footage created for 7 golden scenarios (GS-01 to GS-07) at `tests/data/scenarios/`. This is **not** a controlled dataset from a permitted site — it is synthetic video generated from car crops composited on a road background. Real controlled dataset still required.

### Collection protocol

| Step | Detail |
|------|--------|
| Site | One permitted GVP in Gandhidham (GMC approval required — see docs/08) |
| Camera | Fixed position, fixed angle, night-capable (IR/low-light), 1080p, 5–10 fps |
| Lighting conditions | Night, dawn, dusk, glare, rain/dust (per docs/09 field tests) |
| Positive scenarios | Vehicle stops, person deposits object, object remains after vehicle leaves |
| Negative scenarios | Vehicle parks and leaves (no deposit), waste already present before arrival, person-only deposit, legal unloading |
| Staged waste | Clean boxes/bags only; remove all staged material after collection |
| Annotation | Per `docs/05` schema: source/license, camera, date, lighting, weather, polygon, vehicle boxes/tracks, person boxes, plate boxes, event start/end, object transfer, final label |

### Dataset split (per docs/05)

- Split by location/camera, **not** random frames (prevents leakage)
- Train / validation / held-out test sets
- Held-out test set is never touched during development

### Minimum sample size (target, to be confirmed by benchmarking)

| Split | Clips | Vehicles | Events |
|-------|-------|----------|--------|
| Train | 20 | 40 | 20 |
| Validation | 5 | 10 | 5 |
| Held-out test | 5 | 10 | 5 |

> These are starting targets. The benchmarking plan below defines when they are sufficient.

## Prerequisite 3 — Benchmarking plan

Per `docs/04` selection rules: benchmark before changing models; record exact model version, weights, hardware, resolution and FPS for every result.

### Metrics (from docs/05)

| Metric | Definition | Target (to be confirmed) | Measured (synthetic) |
|--------|------------|--------------------------|----------------------|
| Detection mAP | Mean average precision for vehicle classes | ≥ 0.80 (validation) | Not measured (GT box mismatch) |
| Detection precision/recall | Per-class precision and recall | ≥ 0.80 / ≥ 0.75 | 0.00 / 0.00 (GT box mismatch) |
| Tracking ID switches | Number of times a track changes ID | ≤ 5 per 100 vehicles | Not measured |
| Event precision | Fraction of flagged events that are real dumping | ≥ 0.70 | 0.00% (no dumping cues detected) |
| Event recall | Fraction of real dumping events flagged | ≥ 0.70 | 0.00% (no persons detected) |
| False alerts per camera-hour | Incorrect incidents during monitoring | ≤ 2 | 1.14 |
| Full plate accuracy | Correct full plate read | ≥ 0.60 | 0.00% (no plates in synthetic footage) |
| Character accuracy | Per-character correctness | ≥ 0.85 | 0.00% |
| Processing latency | End-to-end ms per frame | ≤ 200 ms | 74–110 ms ✅ |
| FPS | Sustained processing frames per second | ≥ 5 | 11–16 FPS ✅ |

### Hardware to record (for every result)

- Device (laptop / edge / Pi)
- CPU / GPU model
- RAM
- Resolution
- FPS
- Model version + weight hash
- Confidence threshold

### Go / no-go criteria for Step 4

Step 4 may begin only when **all** of the following are documented:

- [ ] All three model weights acquired, verified offline, and hashes recorded in `models/manifest.json`
- [ ] Controlled dataset collected at a permitted site, annotated per docs/05 schema, split train/val/test
- [ ] Baseline benchmarking run completed on target hardware with all metrics above recorded
- [ ] Benchmark results meet or exceed the targets (or targets are revised with team agreement)
- [ ] Team agrees in PR that evidence supports beginning Step 4 implementation

### What "begin Step 4" means

Only after go/no-go passes:

- Add detection/tracking code to `assets/js/` or a new Python inference service
- Add vehicle stop timer
- Add object-transfer cue logic
- Add plate detector + multi-frame OCR
- All new code is DEMO STAGE until benchmarked on the held-out test set
- No accuracy figures may be published without the recorded hardware, footage conditions, and sample size

## Go / no-go record

| Date | Reviewer | Decision | Evidence |
|------|----------|----------|----------|
| 2026-11-07 | AI/Vision/Data | NOT READY | Benchmarking complete on synthetic footage; person detection + plate OCR not validated; controlled dataset not yet collected |
