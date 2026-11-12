# Step 4 Tools — Vehicle Detection + Multi-Frame ANPR + Incident Association

This directory contains the concrete tooling for Step 4 of GVP-Guard:
vehicle detection, ByteTrack tracking, EasyOCR plate OCR, dumping-event cue,
confidence calibration, and incident association with the SQLite pipeline.

All Step 4 features remain **DEMO STAGE** — not WORKING until benchmarked on
held-out test footage. No accuracy figures published without documented tests.

## Files

| File | Purpose |
|------|---------|
| `download_weights.py` | Download YOLO11n / YOLO11s weights (Ultralytics CDN + Hugging Face mirror) |
| `benchmark_detection.py` | FPS / latency / per-class detection benchmark → `benchmark_results.json` |
| `track_vehicles.py` | YOLO11n + ByteTrack vehicle tracking → per-track stop durations → `tracking_results.json` |
| `anpr_pipeline.py` | Full pipeline: detect → track → plate OCR → dumping-event cue → `anpr_results.json` |
| `calibrate_step4.py` | Confidence calibration: precision/recall/F1 on held-out footage → `calibration_results.json` |
| `associate_incidents.py` | Convert `anpr_results.json` incident candidates into SQLite incident records |
| `test_record_storage.py` | Append-only test record log: dataset version, commit, model version, config, results, limitations → `test_records.json` |
| `ground_truth_template.json` | Template for ground-truth annotations for calibration |
| `requirements.txt` | Python dependencies: ultralytics, opencv-python, numpy, easyocr, Pillow |
| `dataset_acquisition.md` | Exact dataset URLs (Indian plates + vehicle detection) |
| `README.md` | This file |

## Quick start (run on your own machine)

```powershell
# 1. Activate venv (your local machine)
c:\bloodbridge\backend\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r tools/requirements.txt

# 3. Download YOLO11n weights (~5.6 MB)
python tools/download_weights.py --model yolo11n --out models/weights/yolo11n.pt

# 4. Verify weights load
python -c "from ultralytics import YOLO; m=YOLO('models/weights/yolo11n.pt'); print('Model loaded')"

# 5. Run ANPR pipeline on your video
python tools\anpr_pipeline.py --source path\to\your\video.mp4 --weights models\weights\yolo11n.pt --max-frames 100

# 6. Associate AI incidents with SQLite pipeline
python tools\associate_incidents.py --input anpr_results.json --db backend/data/gvp_guard.db

# 7. Run calibration (needs ground-truth annotations)
python tools\calibrate_step4.py --source path\to\test.mp4 --weights models\weights\yolo11n.pt --ground-truth tools\ground_truth.json

# 8. Store test record for the release
python tools\test_record_storage.py --commit <sha> --test-results test_results.json --kpi-results kpi_results.json --output test_records.json
```

## What this proves

- Detection FPS and latency (target: ≥ 5 FPS, ≤ 200 ms per frame)
- ByteTrack persistent track IDs across frames
- EasyOCR multi-frame plate consensus
- Dumping-event cue detection (stopped vehicle + person overlap)
- Calibration metrics: precision/recall/F1 for each component
- Incident association with SQLite evidence pipeline

## Go / no-go (record in docs/STEP4_READINESS_PLAN.md)

Step 4 may proceed to WORKING only when:

- [ ] Weights downloaded + verified offline
- [ ] Controlled dataset collected + annotated + split
- [ ] Benchmark run completed with all metrics recorded
- [ ] Calibration run on held-out test footage with documented precision/recall/F1
- [ ] Team agrees in PR that evidence supports moving DEMO STAGE → WORKING

## Claim discipline

- All Step 4 code is DEMO STAGE — stop time alone does NOT imply guilt
- Human review mandatory — no automatic fines or guilt
- Weights and datasets are external dependencies — NOT committed to Git
- No accuracy figures without documented calibration tests