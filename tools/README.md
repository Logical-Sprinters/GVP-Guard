# Step 4 Tools — Vehicle Detection + Multi-Frame ANPR

This directory contains the concrete tooling to acquire and benchmark the three
Step 4 prerequisites. None of these tools are application code — they are
preparation scripts for the deferred Step 4 build.

## Files

| File | Purpose |
|------|---------|
| `download_weights.py` | Downloads YOLO11n/s pretrained weights (exact URLs) |
| `requirements.txt` | Python dependencies (ultralytics, opencv-python, easyocr, numpy) |
| `benchmark_detection.py` | Runs detection benchmark; outputs `benchmark_results.json` |
| `dataset_acquisition.md` | Exact dataset URLs for vehicle detection + Indian ANPR |

## Quick start (run on your own machine — this sandbox has no internet)

```bash
# 1. Install dependencies
pip install -r tools/requirements.txt

# 2. Download weights (~5.6 MB for nano)
python3 tools/download_weights.py

# 3. Verify weights load
python3 -c "from ultralytics import YOLO; m = YOLO('models/weights/yolo11n.pt'); print('classes:', m.names)"

# 4. Download datasets (see tools/dataset_acquisition.md for exact URLs)
#    - COCO val2017 for vehicle detection baseline
#    - Indian Truck License Plates sample (Kaggle / Hugging Face) for ANPR

# 5. Run benchmark
python3 tools/benchmark_detection.py --source <your_test_video.mp4> --weights models/weights/yolo11n.pt
```

## What this proves

The benchmark script measures exactly the metrics from `docs/05_DATA_AND_ML_PLAN.md`:
- Detection FPS and latency (target: ≥ 5 FPS, ≤ 200 ms per frame)
- Per-class detection counts (car, bus, truck)
- Model load time

If YOLO11n meets the targets on COCO / Indian plate data, Step 4 can proceed
to fine-tuning on the controlled Gandhidham dataset.

## Go / no-go (record in docs/STEP4_READINESS_PLAN.md)

Step 4 may begin only when:
- [ ] Weights downloaded + verified offline (sha256 recorded)
- [ ] Controlled dataset collected + annotated + split
- [ ] Benchmark run completed with all metrics recorded
- [ ] Team agrees in PR that evidence supports beginning Step 4
