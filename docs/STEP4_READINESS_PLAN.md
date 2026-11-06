# Step 4 Readiness Plan — Vehicle Detection + Multi-Frame ANPR

**Status:** Planning (prerequisites not yet met)  
**Owned by:** AI / Vision / Data (Omkar Solat, Prafull Mayank Singh)  
**Related:** `docs/05_DATA_AND_ML_PLAN.md`, `docs/04_TECH_STACK.md`, `docs/15_IMPLEMENTATION_STATUS.md`, `docs/12_BACKLOG.md`

Step 4 (YOLO/ByteTrack vehicle detection + multi-frame ANPR) remains **DEFERRED** per the team decision of 2026-11-06. It may only begin once all three prerequisites below are in place. This document defines what each prerequisite looks like and how to verify it.

## Prerequisite 1 — Model weights

| Component | Spec (docs/04) | Source / weights | Verification |
|-----------|----------------|------------------|--------------|
| Vehicle detector | Ultralytics YOLO11 nano/small | Download from Ultralytics (`yolo11n.pt` / `yolo11s.pt`) | Model loads and runs inference on a sample frame; class IDs include car/truck/auto |
| Tracker | ByteTrack (IoU fallback) | Ultralytics `tracker` config or custom ByteTrack impl | Track IDs persist across frames for a stationary vehicle |
| Plate detector | Plate detector (OpenCV/YOLO) | To be selected after benchmarking | Detects license-plate region on Indian-format plates |
| OCR | EasyOCR (PaddleOCR backup) | `pip install easyocr` / PaddleOCR | Reads digits/letters from cropped plate images |

**Action items:**
- Pin exact model versions and weight file hashes in a `models/manifest.json` (not committed — weights stay outside Git)
- Record download source, license, and date for each weight file
- Verify each model loads offline on the target hardware (Raspberry Pi / edge device or dev laptop)

> Weights are **not committed** to Git. Only the manifest + inference script are versioned.

## Prerequisite 2 — Controlled dataset

Per `docs/05_DATA_AND_ML_PLAN.md`: permitted location, clean boxes/bags, fixed camera, varied angles/light, negative scenarios, remove all staged material.

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

| Metric | Definition | Target (to be confirmed) |
|--------|------------|--------------------------|
| Detection mAP | Mean average precision for vehicle classes | ≥ 0.80 (validation) |
| Detection precision/recall | Per-class precision and recall | ≥ 0.80 / ≥ 0.75 |
| Tracking ID switches | Number of times a track changes ID | ≤ 5 per 100 vehicles |
| Event precision | Fraction of flagged events that are real dumping | ≥ 0.70 |
| Event recall | Fraction of real dumping events flagged | ≥ 0.70 |
| False alerts per camera-hour | Incorrect incidents during monitoring | ≤ 2 |
| Full plate accuracy | Correct full plate read | ≥ 0.60 |
| Character accuracy | Per-character correctness | ≥ 0.85 |
| Processing latency | End-to-end ms per frame | ≤ 200 ms |
| FPS | Sustained processing frames per second | ≥ 5 |

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
| — | — | Not yet reviewed | Prerequisites 1–3 not yet complete |
