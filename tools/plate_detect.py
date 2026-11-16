#!/usr/bin/env python3
"""
Step 4 — License Plate Detection Inference

Runs a trained YOLO plate detector on images/video to localise license plates.
Outputs plate bounding boxes (normalised [0..1]) per frame, ready for EasyOCR.

Usage:
    python3 tools/plate_detect.py \\
        --weights runs/plate_detector/weights/best.pt \\
        --source tests/data/real_datasets/ \\
        --output plate_detections.json \\
        --conf 0.25

Prerequisites:
    pip install ultralytics opencv-python numpy

Claim discipline:
    Detection results are DEMO STAGE until benchmarked on held-out test footage.
    Report mAP, precision, recall only from annotated held-out data.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import cv2
    import numpy as np
    from ultralytics import YOLO
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False


def parse_args():
    p = argparse.ArgumentParser(description="Detect license plates with YOLO")
    p.add_argument("--weights", required=True,
                   help="Path to trained plate detector .pt weights")
    p.add_argument("--source", required=True,
                   help="Image file, directory of images, or video file")
    p.add_argument("--output", default="plate_detections.json",
                   help="Output JSON path for detections")
    p.add_argument("--conf", type=float, default=0.25,
                   help="Confidence threshold")
    p.add_argument("--imgsz", type=int, default=640,
                   help="Inference image size")
    p.add_argument("--device", default="cpu",
                   help="cuda:0, cpu, or mps")
    p.add_argument("--max-frames", type=int, default=0,
                   help="Max frames to process (0 = all)")
    return p.parse_args()


def detect_on_image(model, image_path: Path, conf: float, imgsz: int,
                    device: str):
    """Run plate detection on a single image. Returns list of plate bboxes."""
    results = model(str(image_path), conf=conf, imgsz=imgsz,
                    device=device, verbose=False)

    detections = []
    for r in results:
        if r.boxes is None:
            continue
        h, w = r.orig_shape
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf_score = float(box.conf[0])
            # YOLO returns xyxy in absolute pixels
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            # Normalise to [0..1]
            detections.append({
                "class_id": cls_id,
                "confidence": round(conf_score, 4),
                "bbox": [
                    round(x1 / w, 6),
                    round(y1 / h, 6),
                    round(x2 / w, 6),
                    round(y2 / h, 6),
                ],
            })
    return detections


def main():
    args = parse_args()

    if not DEPS_AVAILABLE:
        print("[error] Missing dependencies. Install: pip install ultralytics opencv-python numpy")
        return

    source = Path(args.source)
    output_path = Path(args.output)

    print(f"[load] Loading plate detector: {args.weights}")
    model = YOLO(args.weights)

    results = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "weights": args.weights,
        "source": str(source),
        "conf_threshold": args.conf,
        "imgsz": args.imgsz,
        "device": args.device,
        "detections": [],
    }

    if source.is_file() and source.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}:
        # Video mode
        import cv2
        cap = cv2.VideoCapture(str(source))
        frame_idx = 0
        try:
            while True:
                if args.max_frames and frame_idx >= args.max_frames:
                    break
                ret, frame = cap.read()
                if not ret:
                    break

                # Save frame temporarily for YOLO (or use numpy array directly)
                t0 = time.perf_counter()
                r = model(frame, conf=args.conf, imgsz=args.imgsz,
                          device=args.device, verbose=False)
                t1 = time.perf_counter()

                frame_dets = []
                for res in r:
                    if res.boxes is None:
                        continue
                    h, w = res.orig_shape
                    for box in res.boxes:
                        cls_id = int(box.cls[0])
                        conf_score = float(box.conf[0])
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        frame_dets.append({
                            "frame": frame_idx,
                            "class_id": cls_id,
                            "confidence": round(conf_score, 4),
                            "bbox": [
                                round(x1 / w, 6),
                                round(y1 / h, 6),
                                round(x2 / w, 6),
                                round(y2 / h, 6),
                            ],
                            "inference_ms": round((t1 - t0) * 1000, 2),
                        })
                results["detections"].extend(frame_dets)
                frame_idx += 1

                if frame_idx % 50 == 0:
                    print(f"  processed {frame_idx} frames")
        finally:
            cap.release()
    elif source.is_dir():
        # Directory of images
        images = sorted(source.glob("*.*"))
        images = [p for p in images if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}]
        for idx, img_path in enumerate(images):
            if args.max_frames and idx >= args.max_frames:
                break
            t0 = time.perf_counter()
            frame_dets = detect_on_image(model, img_path, args.conf, args.imgsz, args.device)
            t1 = time.perf_counter()

            for d in frame_dets:
                d["frame"] = idx
                d["image"] = img_path.name
                d["inference_ms"] = round((t1 - t0) * 1000, 2)
                results["detections"].append(d)

            if idx % 10 == 0:
                print(f"  processed {idx + 1}/{len(images)} images")
    else:
        print(f"[error] Source not found or unsupported: {source}")
        return

    output_path.write_text(json.dumps(results, indent=2))
    total = len(results["detections"])
    print(f"\n=== Detection complete ===")
    print(f"Total plate detections: {total}")
    print(f"Results written to {output_path}")


if __name__ == "__main__":
    main()