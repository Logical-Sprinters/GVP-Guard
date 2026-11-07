#!/usr/bin/env python3
"""
Step 4 Benchmarking Script — Vehicle Detection + Tracking
Run:  python3 tools/benchmark_detection.py --source tests/data/sample.mp4 --weights models/weights/yolo11n.pt

Outputs benchmark_results.json with all metrics required by docs/05_DATA_AND_ML_PLAN.md.

Prerequisites:
  pip install ultralytics opencv-python numpy
  python3 tools/download_weights.py   (to get yolo11n.pt)
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


# COCO class IDs relevant to vehicles
VEHICLE_CLASS_IDS = {2: "car", 5: "bus", 7: "truck"}


def parse_args():
    p = argparse.ArgumentParser(description="Benchmark YOLO11 vehicle detection")
    p.add_argument("--source", required=True, help="Video file or image directory")
    p.add_argument("--weights", default="models/weights/yolo11n.pt", help="Path to .pt weights")
    p.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    p.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    p.add_argument("--device", default="cpu", help="cpu or cuda:0")
    p.add_argument("--max-frames", type=int, default=0, help="Max frames to process (0 = all)")
    p.add_argument("--output", default="benchmark_results.json", help="Output JSON path")
    return p.parse_args()


def main():
    args = parse_args()
    source = Path(args.source)

    # --- Load model ---
    load_t0 = time.perf_counter()
    model = YOLO(args.weights)
    load_t1 = time.perf_counter()
    load_seconds = load_t1 - load_t0

    # --- Warmup (first inference is slower due to weight load / CUDA init) ---
    dummy = np.zeros((args.imgsz, args.imgsz, 3), dtype=np.uint8)
    _ = model(dummy, verbose=False)

    # --- Open source ---
    if source.is_file() and source.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}:
        cap = cv2.VideoCapture(str(source))
        fps_source = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        is_video = True
    elif source.is_dir():
        images = sorted(source.glob("*.*"))
        images = [p for p in images if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}]
        total_frames = len(images)
        fps_source = 0.0
        is_video = False
        idx = 0
    else:
        raise SystemExit(f"Source not found or unsupported: {source}")

    # --- Metrics accumulators ---
    latencies = []          # per-frame inference ms
    detection_counts = {}   # class_name -> count
    frames_processed = 0
    start_wall = time.perf_counter()

    try:
        while True:
            if args.max_frames and frames_processed >= args.max_frames:
                break

            if is_video:
                ret, frame = cap.read()
                if not ret:
                    break
            else:
                if idx >= len(images):
                    break
                frame = cv2.imread(str(images[idx]))
                idx += 1
                if frame is None:
                    continue

            # Resize to inference size
            resized = cv2.resize(frame, (args.imgsz, args.imgsz))

            t0 = time.perf_counter()
            results = model(resized, conf=args.conf, imgsz=args.imgsz, device=args.device, verbose=False)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)  # ms

            for r in results:
                if r.boxes is None:
                    continue
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = model.names.get(cls_id, str(cls_id))
                    detection_counts[cls_name] = detection_counts.get(cls_name, 0) + 1

            frames_processed += 1

            # Print progress every 50 frames
            if frames_processed % 50 == 0:
                fps_so_far = frames_processed / (time.perf_counter() - start_wall)
                print(f"  processed {frames_processed} frames, {fps_so_far:.1f} fps")

    finally:
        if is_video:
            cap.release()

    wall_seconds = time.perf_counter() - start_wall
    effective_fps = frames_processed / wall_seconds if wall_seconds > 0 else 0
    avg_latency = float(np.mean(latencies)) if latencies else 0.0
    p95_latency = float(np.percentile(latencies, 95)) if latencies else 0.0
    p99_latency = float(np.percentile(latencies, 99)) if latencies else 0.0

    total_detections = sum(detection_counts.values())
    vehicle_detections = sum(detection_counts.get(c, 0) for c in VEHICLE_CLASS_IDS.values())

    results_dict = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "weights": args.weights,
        "device": args.device,
        "conf_threshold": args.conf,
        "imgsz": args.imgsz,
        "frames_processed": frames_processed,
        "load_seconds": round(load_seconds, 3),
        "wall_seconds": round(wall_seconds, 3),
        "effective_fps": round(effective_fps, 2),
        "avg_inference_ms": round(avg_latency, 2),
        "p95_inference_ms": round(p95_latency, 2),
        "p99_inference_ms": round(p99_latency, 2),
        "total_detections": total_detections,
        "vehicle_detections": vehicle_detections,
        "detections_by_class": detection_counts,
        "source_fps": round(fps_source, 2),
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(results_dict, indent=2))
    print(f"\n=== Benchmark complete ===")
    print(f"Frames: {frames_processed} | FPS: {effective_fps:.1f} | Avg latency: {avg_latency:.1f} ms")
    print(f"Total detections: {total_detections} | Vehicle detections: {vehicle_detections}")
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    main()