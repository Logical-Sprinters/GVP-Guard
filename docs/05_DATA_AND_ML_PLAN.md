# Data and Machine-Learning Plan

## Event taxonomy
- Normal pass
- Short stop
- Long stop without dumping
- Legal/ambiguous unloading
- Probable dumping
- Person-only deposit
- Waste present before arrival
- Object removed after temporary placement

## Annotation schema
For each clip: source/license, camera, date, lighting, weather, GVP polygon, vehicle boxes/tracks, person boxes, plate boxes, event start/end, object transfer and final label.

## Dataset split
Split by location/camera, not random frames, to prevent leakage. Maintain train, validation and held-out test sets.

## Controlled data collection
Use a permitted location, clean boxes/bags, fixed camera, varied angles/light and negative scenarios. Remove all staged material.

## Event model strategy
Start rule-based: zone + stop + scene change. Add learned cues only when data supports them. Compare against the simple baseline.

## ANPR strategy
Detect plate -> track -> score frames -> rectify/enhance -> OCR each frame -> majority agreement -> Indian-format validation -> manual review.

## Metrics
- Detection precision/recall/mAP
- Tracking ID switches
- Event precision/recall and false alerts per camera-hour
- Full plate and character accuracy
- Processing latency and FPS

## Benchmarking results (2026-11-07, DEMO STAGE)

### Synthetic footage (7 golden scenarios GS-01 to GS-07)
- Vehicle detection + ByteTrack tracking: 11–16 FPS, 74–110 ms/frame (meets ≥5 FPS / ≤200 ms targets)
- 2/7 scenarios pass (28.6%) — long stop and duplicate event pass; person deposit, plate unreadable, network fail fail due to person detection not validated on synthetic figures
- Person detection: NOT validated (synthetic figures not detected by YOLO11n)
- Plate OCR: NOT validated (no readable plates in synthetic car crops)

### Real Indian license plate dataset (witvix/indian-truck-license-plates-sample)
- 16 sampled images, 17 plate annotations from COCO ground truth
- Plate OCR exact match: 0.0% (0/17) vs target ≥0.60 ❌
- Plate OCR character accuracy: 18.2% (30/165) vs target ≥0.85 ❌
- Key finding: EasyOCR on raw plate crops (no dedicated plate detector) struggles with Indian plates — two-line formats, hand-painted fonts, small plates, night photos
- A dedicated plate detector (YOLO fine-tuned on license plates) is required before ANPR accuracy targets can be met

### Data and model artifacts
- Weight hashes: `models/manifest.json` (weights NOT committed to Git)
- Test records: `tests/data/scenarios/test_records.json` (synthetic), `tests/data/real_datasets/test_records_real.json` (real plates)

## Data governance
Store provenance and consent/permission. Avoid faces where unnecessary. Do not use unlicensed footage or real registry data without authorization.
