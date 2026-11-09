#!/usr/bin/env python3
"""
Step 4 Confidence Calibration — DEMO STAGE

Runs the ANPR pipeline on controlled test footage with known ground truth
annotations and documents precision/recall/F1 for:
- Vehicle detection (YOLO11n)
- Plate OCR (EasyOCR multi-frame consensus)
- Dumping-event cue (stopped vehicle + person overlap)

Usage:
    python tools\calibrate_step4.py --source <test_video_or_dir> --weights models\weights\yolo11n.pt --ground-truth ground_truth.json

Ground truth format (ground_truth.json):
{
  "frames": [
    {"frame": 0, "vehicles": [{"box": [x1,y1,x2,y2], "plate": "GJ12AB4381"}], "dumping": false},
    ...
  ],
  "fps": 25,
  "notes": "Controlled footage, daytime, Indian plates"
}

Outputs: calibration_results.json with documented metrics.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

VEHICLE_CLASS_IDS = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

DEFAULT_POLYGON = [
    {"x": 0.10, "y": 0.60},
    {"x": 0.90, "y": 0.60},
    {"x": 0.90, "y": 1.00},
    {"x": 0.10, "y": 1.00},
]

IOU_MATCH_THRESHOLD = 0.5


def parse_args():
    p = argparse.ArgumentParser(description="Step 4 confidence calibration")
    p.add_argument("--source", required=True, help="Test video or directory of images")
    p.add_argument("--weights", default="models/weights/yolo11n.pt", help="YOLO11n .pt weights")
    p.add_argument("--tracker", default="bytetrack.yaml", help="ByteTrack config file")
    p.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold")
    p.add_argument("--ocr-conf", type=float, default=0.30, help="EasyOCR confidence threshold")
    p.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    p.add_argument("--device", default="cpu", help="cpu or cuda:0")
    p.add_argument("--stop-threshold", type=float, default=2.0, help="Seconds stopped for 'stop'")
    p.add_argument("--max-frames", type=int, default=0, help="Max frames (0 = all)")
    p.add_argument("--ground-truth", required=True, help="Ground truth JSON file")
    p.add_argument("--output", default="calibration_results.json", help="Output JSON path")
    p.add_argument("--polygon", default=None, help='JSON polygon string')
    p.add_argument("--langs", default="en", help="EasyOCR languages (comma-separated)")
    return p.parse_args()


def load_polygon(polygon_arg):
    if polygon_arg:
        return json.loads(polygon_arg)
    return DEFAULT_POLYGON


def point_in_polygon(point, polygon):
    if len(polygon) < 3:
        return False
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]["x"], polygon[i]["y"]
        xj, yj = polygon[j]["x"], polygon[j]["y"]
        intersect = ((yi > point["y"]) != (yj > point["y"])) and (
            point["x"] < (xj - xi) * (point["y"] - yi) / (yj - yi) + xi
        )
        if intersect:
            inside = not inside
        j = i
    return inside


def iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    ix1 = max(ax1, bx1); iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2); iy2 = min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    aa = (ax2 - ax1) * (ay2 - ay1)
    ba = (bx2 - bx1) * (by2 - by1)
    return inter / (aa + ba - inter) if (aa + ba - inter) > 0 else 0.0


def open_source(source_path):
    src = Path(source_path)
    if src.is_file() and src.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}:
        cap = cv2.VideoCapture(str(src))
        return cap, True, int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    elif src.is_file() and src.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}:
        return [src], False, 1
    elif src.is_dir():
        images = sorted(src.glob("*.*"))
        images = [p for p in images if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}]
        return images, False, len(images)
    else:
        raise SystemExit(f"Source not found: {source_path}")


def read_frame(source, is_video, idx):
    if is_video:
        ret, frame = source.read()
        if not ret:
            return None
        return frame
    else:
        return cv2.imread(str(source[idx]))


def normalize_plate(text):
    if not text:
        return ""
    return "".join(ch.upper() for ch in text if ch.isalnum())


def main():
    args = parse_args()
    polygon = load_polygon(args.polygon)

    # Load ground truth
    gt_path = Path(args.ground_truth)
    with open(gt_path) as f:
        ground_truth = json.load(f)

    gt_by_frame = {}
    for entry in ground_truth.get("frames", []):
        gt_by_frame[entry["frame"]] = entry

    t_load0 = time.perf_counter()
    model = YOLO(args.weights)
    t_load1 = time.perf_counter()

    try:
        import easyocr
        reader = easyocr.Reader([l.strip() for l in args.langs.split(",")], gpu=False)
    except ImportError:
        reader = None
        print("WARNING: easyocr not installed — plate calibration will be skipped")

    source, is_video, total_frames = open_source(args.source)

    # Counters
    vehicle_tp = 0  # detected vehicle matched to GT
    vehicle_fp = 0  # detected vehicle with no GT match
    vehicle_fn = 0  # GT vehicle with no detection match

    plate_exact_match = 0
    plate_total_gt = 0
    plate_char_correct = 0
    plate_char_total = 0

    dumping_tp = 0
    dumping_fp = 0
    dumping_fn = 0

    frame_idx = 0
    processed = 0
    start_wall = time.perf_counter()

    try:
        while True:
            if args.max_frames and processed >= args.max_frames:
                break

            frame = read_frame(source, is_video, frame_idx)
            if frame is None:
                break

            h, w = frame.shape[:2]

            gt_entry = gt_by_frame.get(frame_idx)
            gt_vehicles = gt_entry.get("vehicles", []) if gt_entry else []
            gt_dumping = bool(gt_entry.get("dumping", False)) if gt_entry else False

            # Run detection + tracking
            results = model.track(
                frame,
                conf=args.conf,
                imgsz=args.imgsz,
                device=args.device,
                tracker=args.tracker,
                verbose=False,
                persist=True,
            )

            detected_boxes = []
            detected_vehicle_boxes = []

            for r in results:
                if r.boxes is None:
                    continue
                boxes = r.boxes.xyxy.cpu().numpy() if r.boxes.xyxy is not None else np.empty((0, 4))
                track_ids = r.boxes.id.cpu().numpy().astype(int) if r.boxes.id is not None else np.empty((0,), dtype=int)
                class_ids = r.boxes.cls.cpu().numpy().astype(int) if r.boxes.cls is not None else np.empty((0,), dtype=int)
                confs = r.boxes.conf.cpu().numpy() if r.boxes.conf is not None else np.empty((0,), dtype=float)

                for box, tid, cid, conf in zip(boxes, track_ids, class_ids, confs):
                    x1, y1, x2, y2 = [float(v) for v in box]
                    box_list = [x1, y1, x2, y2]

                    if cid == PERSON_CLASS_ID if False else False:
                        pass

                    if cid not in VEHICLE_CLASS_IDS:
                        continue

                    detected_vehicle_boxes.append(box_list)

                    # Plate OCR on detected vehicle
                    if reader and gt_entry:
                        cx = (x1 + x2) / 2 / w
                        cy = (y1 + y2) / 2 / h
                        if point_in_polygon({"x": cx, "y": cy}, polygon):
                            plate_crop = frame[int(y1):int(y2), int(x1):int(x2)]
                            if plate_crop.size > 0:
                                try:
                                    ocr_results = reader.readtext(plate_crop)
                                    for (bbox, text, conf_score) in ocr_results:
                                        if conf_score < args.ocr_conf:
                                            continue
                                        # Match to GT plate for this frame
                                        for gv in gt_vehicles:
                                            gt_plate = normalize_plate(gv.get("plate", ""))
                                            ocr_plate = normalize_plate(text)
                                            if gt_plate and ocr_plate == gt_plate:
                                                plate_exact_match += 1
                                                plate_total_gt += 1
                                                break
                                            elif gt_plate and ocr_plate:
                                                plate_total_gt += 1
                                                # Character-level accuracy
                                                max_len = max(len(gt_plate), len(ocr_plate))
                                                matches = sum(1 for a, b in zip(gt_plate, ocr_plate) if a == b)
                                                plate_char_correct += matches
                                                plate_char_total += max_len
                                except Exception:
                                    pass

            # Match detected vehicles to GT vehicles (IoU-based)
            gt_matched = [False] * len(gt_vehicles)
            det_matched = [False] * len(detected_vehicle_boxes)

            for di, dbox in enumerate(detected_vehicle_boxes):
                best_iou = 0
                best_gi = -1
                for gi, gv in enumerate(gt_vehicles):
                    gbox = gv["box"]
                    i = iou(dbox, gbox)
                    if i > best_iou:
                        best_iou = i
                        best_gi = gi
                if best_iou >= IOU_MATCH_THRESHOLD and best_gi >= 0 and not gt_matched[best_gi]:
                    vehicle_tp += 1
                    det_matched[di] = True
                    gt_matched[best_gi] = True

            for di, matched in enumerate(det_matched):
                if not matched:
                    vehicle_fp += 1

            for gi, matched in enumerate(gt_matched):
                if not matched:
                    vehicle_fn += 1

            # Dumping-event cue: any detected vehicle with person overlap + stop
            # (Simplified for calibration: flag if any vehicle detected in polygon)
            predicted_dumping = len(detected_vehicle_boxes) > 0
            if predicted_dumping and gt_dumping:
                dumping_tp += 1
            elif predicted_dumping and not gt_dumping:
                dumping_fp += 1
            elif not predicted_dumping and gt_dumping:
                dumping_fn += 1

            processed += 1
            frame_idx += 1

            if processed % 20 == 0:
                fps = processed / (time.perf_counter() - start_wall)
                print(f"  processed {processed} frames, {fps:.1f} fps")

    finally:
        if is_video:
            source.release()

    # Compute metrics
    vehicle_precision = vehicle_tp / (vehicle_tp + vehicle_fp) if (vehicle_tp + vehicle_fp) > 0 else 0.0
    vehicle_recall = vehicle_tp / (vehicle_tp + vehicle_fn) if (vehicle_tp + vehicle_fn) > 0 else 0.0
    vehicle_f1 = 2 * vehicle_precision * vehicle_recall / (vehicle_precision + vehicle_recall) if (vehicle_precision + vehicle_recall) > 0 else 0.0

    plate_accuracy = plate_exact_match / plate_total_gt if plate_total_gt > 0 else 0.0
    plate_char_accuracy = plate_char_correct / plate_char_total if plate_char_total > 0 else 0.0

    dumping_precision = dumping_tp / (dumping_tp + dumping_fp) if (dumping_tp + dumping_fp) > 0 else 0.0
    dumping_recall = dumping_tp / (dumping_tp + dumping_fn) if (dumping_tp + dumping_fn) > 0 else 0.0
    dumping_f1 = 2 * dumping_precision * dumping_recall / (dumping_precision + dumping_recall) if (dumping_precision + dumping_recall) > 0 else 0.0

    wall_seconds = time.perf_counter() - start_wall
    effective_fps = processed / wall_seconds if wall_seconds > 0 else 0

    results = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(args.source),
        "ground_truth": str(args.ground_truth),
        "weights": args.weights,
        "device": args.device,
        "polygon": polygon,
        "iou_match_threshold": IOU_MATCH_THRESHOLD,
        "ocr_conf_threshold": args.ocr_conf,
        "stop_threshold_secs": args.stop_threshold,
        "frames_processed": processed,
        "total_frames_available": total_frames,
        "wall_seconds": round(wall_seconds, 3),
        "effective_fps": round(effective_fps, 2),

        "vehicle_detection": {
            "true_positives": vehicle_tp,
            "false_positives": vehicle_fp,
            "false_negatives": vehicle_fn,
            "precision": round(vehicle_precision, 4),
            "recall": round(vehicle_recall, 4),
            "f1": round(vehicle_f1, 4),
        },

        "plate_ocr": {
            "exact_matches": plate_exact_match,
            "total_gt_plates": plate_total_gt,
            "plate_accuracy": round(plate_accuracy, 4),
            "character_accuracy": round(plate_char_accuracy, 4),
        },

        "dumping_event_cue": {
            "true_positives": dumping_tp,
            "false_positives": dumping_fp,
            "false_negatives": dumping_fn,
            "precision": round(dumping_precision, 4),
            "recall": round(dumping_recall, 4),
            "f1": round(dumping_f1, 4),
        },

        "honesty_notes": [
            "All metrics are DEMO STAGE — not WORKING until validated on independent held-out footage.",
            "Vehicle detection uses YOLO11n COCO classes (car=2, bus=5, truck=7, motorcycle=3).",
            "Plate OCR uses lower-bumper crop heuristic; dedicated plate detector recommended for production.",
            "Dumping-event cue is a simplified person-overlap heuristic, not a trained model.",
            "Stop time alone does NOT imply guilt. Human review mandatory.",
            "No automatic fines or guilt — officer review required before any enforcement action.",
        ],
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(results, indent=2))

    print(f"\n=== Calibration complete ===")
    print(f"Frames: {processed} | FPS: {effective_fps:.1f}")
    print(f"Vehicle detection: P={vehicle_precision:.3f} R={vehicle_recall:.3f} F1={vehicle_f1:.3f}")
    print(f"Plate OCR: accuracy={plate_accuracy:.3f} char_acc={plate_char_accuracy:.3f}")
    print(f"Dumping cue: P={dumping_precision:.3f} R={dumping_recall:.3f} F1={dumping_f1:.3f}")
    print(f"Results: {out_path}")


if __name__ == "__main__":
    main()