# Step 4 Tools — Vehicle Detection & Benchmarking

Concrete, downloadable resources for Step 4 readiness. All Step 4 features
remain **DEMO STAGE** — not WORKING until benchmarked on a held-out test set.

## Files

| File | Purpose |
|------|---------|
| `download_weights.py` | Download YOLO11n / YOLO11s weights (Ultralytics CDN + HF mirror) |
| `benchmark_detection.py` | FPS / latency / per-class detection benchmark → `benchmark_results.json` |
| `track_vehicles.py` | YOLO11n + ByteTrack vehicle tracking → per-track stop durations |
| `requirements.txt` | Python dependencies: ultralytics, opencv-python, numpy, easyocr, Pillow |
| `dataset_acquisition.md` | Exact dataset URLs (Indian plates + vehicle detection) |

## Quick start

```powershell
# 1. Activate venv (user local)
c:\bloodbridge\backend\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r tools/requirements.txt

# 3. Download YOLO11n weights (~5.6 MB)
python tools/download_weights.py --model yolo11n --out models/weights/yolo11n.pt

# 4. Verify model loads
python -c "from ultralytics import YOLO; m=YOLO('models/weights/yolo11n.pt'); print('Model loaded')"

# 5. Benchmark detection on dataset images
python tools/benchmark_detection.py --source datasets/indian-truck-plates/images/ --weights models/weights/yolo11n.pt --max-frames 20

# 6. Track vehicles with ByteTrack
python tools/track_vehicles.py --source datasets/indian-truck-plates/images/ --weights models/weights/yolo11n.pt
```

## Go / No-Go checklist

| Criterion | Target | Your result |
|-----------|--------|-------------|
| YOLO11n loads without error | ✅ | |
| Benchmark runs without error | ✅ | |
| effective_fps ≥ 5 | ≥ 5 fps | |
| avg_inference_ms ≤ 200 | ≤ 200 ms | |
| vehicle_detections > 0 | > 0 | |

All boxes checked → Step 4 may begin implementation.

## Claim discipline

- All Step 4 code is DEMO STAGE — not WORKING until benchmarked
- Stop time alone does NOT imply guilt
- No accuracy figures without documented tests
- Human review mandatory — no automatic fines or guilt
- Weights and datasets are external dependencies — NOT committed to Git