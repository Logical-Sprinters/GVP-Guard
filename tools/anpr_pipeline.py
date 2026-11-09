#!/usr/bin/env python3
"""
Step 4 — Complete ANPR Pipeline (DEMO STAGE)

End-to-end: Vehicle detection (YOLO11n) + ByteTrack tracking +
License plate OCR (EasyOCR multi-frame consensus) +
Dumping-event cue (stopped vehicle + person nearby) +
Incident record output.

Prerequisites:
- ultralytics installed (torch + ultralytics) ✅
- easyocr installed ✅
- models/weights/yolo11n.pt downloaded ✅
- Optional: plate detection model weights (not committed; see --plate-weights)

Usage:
    python tools\anpr_pipeline.py --source <video_or_dir> --weights models\weights\yolo11n.pt

Outputs:
    anpr_results.json — per-track plate reads + stop events + incident cues
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

VEHICLE_CLASS_IDS = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
PERSON_CLASS_ID = 0

# Default GVP polygon (normalised [0..1] coords)
DEFAULT_POLYGON = [
    {"x": 0.10, "y": 0.60},
    {"x": 0.90, "y": 0.60},
    {"x": 0.90, "y": 1.00},
    {"x": 0.10, "y": 1.00},
]

# Plate region as fraction of vehicle box (lower bumper area)
PLATE_REGION = {"ymin": 0.70, "ymax": 0.95, "xmin": 0.25, "xmax": 0.75}


def parse_args():
    p = argparse.ArgumentParser(description="Step 4 ANPR pipeline")
    p.add_argument("--source", required=True, help="Video file or directory of images")
    p.add_argument("--weights", default="models/weights/yolo11n.pt", help="YOLO11n .pt weights")
    p.add_argument("--plate-weights", default=None, help="Optional plate detection .pt weights")
    p.add_argument("--tracker", default="bytetrack.yaml", help="ByteTrack config file")
    p.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold")
    p.add_argument("--ocr-conf", type=float, default=0.30, help="EasyOCR confidence threshold")
    p.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    p.add_argument("--device", default="cpu", help="cpu or cuda:0")
    p.add_argument("--stop-threshold", type=float, default=2.0,
                   help="Seconds stopped to count as a 'stop'")
    p.add_argument("--max-frames", type=int, default=0, help="Max frames (0 = all)")
    p.add_argument("--output", default="anpr_results.json", help="Output JSON path")
    p.add_argument("--polygon", default=None,
                   help='JSON string of polygon points [{"x":0.1,"y":0.6},...]')
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


def boxes_overlap(box_a, box_b, threshold=0.3):
    """Return True if box_a and box_b overlap by more than threshold of box_a area."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return False
    inter_area = (ix2 - ix1) * (iy2 - iy1)
    a_area = (ax2 - ax1) * (ay2 - ay1)
    if a_area <= 0:
        return False
    return (inter_area / a_area) > threshold


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


def crop_plate_region(frame, vehicle_box):
    """Crop the lower bumper area of a vehicle where the plate typically sits."""
    x1, y1, x2, y2 = vehicle_box
    h, w = frame.shape[:2]
    px1 = int(x1 + (x2 - x1) * PLATE_REGION["xmin"])
    px2 = int(x1 + (x2 - x1) * PLATE_REGION["xmax"])
    py1 = int(y1 + (y2 - y1) * PLATE_REGION["ymin"])
    py2 = int(y1 + (y2 - y1) * PLATE_REGION["ymax"])
    px1 = max(0, min(px1, w - 1))
    px2 = max(px1 + 1, min(px2, w))
    py1 = max(0, min(py1, h - 1))
    py2 = max(py1 + 1, min(py2, h))
    return frame[py1:py2, px1:px2]


def main():
    args = parse_args()
    polygon = load_polygon(args.polygon)
    langs = [l.strip() for l in args.langs.split(",")]

    # EasyOCR reader (lazy init — only if OCR needed)
    reader = None

    def get_reader():
        nonlocal reader
        if reader is None:
            if not EASYOCR_AVAILABLE:
                raise RuntimeError("easyocr not installed. pip install easyocr")
            reader = easyocr.Reader(langs, gpu=False)
        return reader

    t_load0 = time.perf_counter()
    model = YOLO(args.weights)
    t_load1 = time.perf_counter()

    plate_model = None
    if args.plate_weights:
        plate_model = YOLO(args.plate_weights)

    source, is_video, total_frames = open_source(args.source)

    # Per-track state
    tracks = {}  # track_id -> track record
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

            # YOLO11n + ByteTrack
            results = model.track(
                frame,
                conf=args.conf,
                imgsz=args.imgsz,
                device=args.device,
                tracker=args.tracker,
                verbose=False,
                persist=True,
            )

            current_track_ids = set()
            persons_in_frame = []

            for r in results:
                if r.boxes is None:
                    continue
                boxes = r.boxes.xyxy.cpu().numpy() if r.boxes.xyxy is not None else np.empty((0, 4))
                track_ids = r.boxes.id.cpu().numpy().astype(int) if r.boxes.id is not None else np.empty((0,), dtype=int)
                class_ids = r.boxes.cls.cpu().numpy().astype(int) if r.boxes.cls is not None else np.empty((0,), dtype=int)
                confs = r.boxes.conf.cpu().numpy() if r.boxes.conf is not None else np.empty((0,), dtype=float)

                for box, tid, cid, conf in zip(boxes, track_ids, class_ids, confs):
                    x1, y1, x2, y2 = [float(v) for v in box]

                    # Collect persons for dumping-event cue
                    if cid == PERSON_CLASS_ID:
                        persons_in_frame.append([x1, y1, x2, y2])
                        continue

                    if cid not in VEHICLE_CLASS_IDS:
                        continue

                    cx = (x1 + x2) / 2 / w
                    cy = (y1 + y2) / 2 / h
                    current_track_ids.add(tid)

                    if tid not in tracks:
                        tracks[tid] = {
                            "track_id": int(tid),
                            "vehicle_type": VEHICLE_CLASS_IDS.get(cid, str(cid)),
                            "first_seen_frame": frame_idx,
                            "in_polygon": False,
                            "stop_start_frame": None,
                            "stop_events": [],
                            "plate_reads": [],
                            "best_plate": None,
                            "best_plate_conf": 0.0,
                            "max_conf": float(conf),
                            "last_frame": frame_idx,
                            "dumping_cues": [],
                        }

                    trk = tracks[tid]
                    trk["last_frame"] = frame_idx
                    trk["max_conf"] = max(trk["max_conf"], float(conf))

                    inside = point_in_polygon({"x": cx, "y": cy}, polygon)

                    if inside and not trk["in_polygon"]:
                        trk["in_polygon"] = True
                        trk["stop_start_frame"] = frame_idx
                    elif not inside and trk["in_polygon"]:
                        trk["in_polygon"] = False
                        if trk["stop_start_frame"] is not None:
                            stop_frames = frame_idx - trk["stop_start_frame"]
                            stop_secs = stop_frames / 25.0
                            trk["stop_events"].append({
                                "start_frame": trk["stop_start_frame"],
                                "end_frame": frame_idx,
                                "duration_secs": round(stop_secs, 2),
                            })
                            trk["stop_start_frame"] = None

                    # Plate OCR on this frame if vehicle is in polygon
                    if inside:
                        vehicle_box = [x1, y1, x2, y2]
                        plate_crop = crop_plate_region(frame, vehicle_box)
                        if plate_crop.size > 0:
                            try:
                                ocr = get_reader()
                                ocr_results = ocr.readtext(plate_crop)
                                for (bbox, text, conf_score) in ocr_results:
                                    if conf_score < args.ocr_conf:
                                        continue
                                    trk["plate_reads"].append({
                                        "frame": frame_idx,
                                        "text": text,
                                        "confidence": round(float(conf_score), 3),
                                    })
                                    if conf_score > trk["best_plate_conf"]:
                                        trk["best_plate_conf"] = float(conf_score)
                                        trk["best_plate"] = {
                                            "text": text,
                                            "confidence": round(float(conf_score), 3),
                                            "frame": frame_idx,
                                            "bbox": [round(float(v), 1) for v in bbox],
                                        }
                            except Exception:
                                # OCR failure on this frame — silent
                                pass

                    # Dumping-event cue: person overlapping or near vehicle box
                    for pbox in persons_in_frame:
                        if boxes_overlap(vehicle_box, pbox, threshold=0.15):
                            trk["dumping_cues"].append({
                                "frame": frame_idx,
                                "person_box": [round(float(v), 1) for v in pbox],
                                "vehicle_box": [round(float(v), 1) for v in vehicle_box],
                            })

            processed += 1
            frame_idx += 1

            if processed % 20 == 0:
                fps = processed / (time.perf_counter() - start_wall)
                print(f"  processed {processed} frames, {fps:.1f} fps, active tracks: {len(current_track_ids)}")

    finally:
        if is_video:
            source.release()

    # Finalise tracks still in polygon
    now_frame = frame_idx
    for tid, trk in tracks.items():
        if trk["in_polygon"] and trk["stop_start_frame"] is not None:
            stop_frames = now_frame - trk["stop_start_frame"]
            stop_secs = stop_frames / 25.0
            trk["stop_events"].append({
                "start_frame": trk["stop_start_frame"],
                "end_frame": now_frame,
                "duration_secs": round(stop_secs, 2),
            })
            trk["stop_start_frame"] = None
            trk["in_polygon"] = False

    # Build output
    track_list = []
    incident_candidates = []

    for tid, trk in tracks.items():
        total_stop = sum(e["duration_secs"] for e in trk["stop_events"])
        long_stops = [e for e in trk["stop_events"] if e["duration_secs"] >= args.stop_threshold]

        # Multi-frame plate consensus: most frequent text across reads
        plate_consensus = None
        if trk["plate_reads"]:
            from collections import Counter
            texts = [r["text"] for r in trk["plate_reads"]]
            most_common = Counter(texts).most_common(1)[0]
            consensus_text = most_common[0]
            consensus_count = most_common[1]
            avg_conf = np.mean([r["confidence"] for r in trk["plate_reads"] if r["text"] == consensus_text])
            plate_consensus = {
                "text": consensus_text,
                "read_count": consensus_count,
                "total_reads": len(trk["plate_reads"]),
                "avg_confidence": round(float(avg_conf), 3),
                "best": trk["best_plate"],
            }

        track_record = {
            "track_id": trk["track_id"],
            "vehicle_type": trk["vehicle_type"],
            "first_seen_frame": trk["first_seen_frame"],
            "last_frame": trk["last_frame"],
            "max_confidence": round(trk["max_conf"], 2),
            "in_polygon_final": trk["in_polygon"],
            "stop_events": trk["stop_events"],
            "total_stop_secs": round(total_stop, 2),
            "long_stop_count": len(long_stops),
            "longest_stop_secs": round(max([e["duration_secs"] for e in trk["stop_events"]], default=0), 2),
            "plate_consensus": plate_consensus,
            "plate_reads": trk["plate_reads"],
            "dumping_cues": trk["dumping_cues"],
            "dumping_cue_count": len(trk["dumping_cues"]),
        }
        track_list.append(track_record)

        # Incident candidate: long stop + dumping cue + plate read
        if long_stops and trk["dumping_cues"]:
            incident_candidates.append({
                "track_id": trk["track_id"],
                "vehicle_type": trk["vehicle_type"],
                "plate_text": plate_consensus["text"] if plate_consensus else None,
                "plate_confidence": plate_consensus["avg_confidence"] if plate_consensus else None,
                "longest_stop_secs": track_record["longest_stop_secs"],
                "dumping_cue_count": trk["dumping_cue_count"],
                "first_cue_frame": trk["dumping_cues"][0]["frame"] if trk["dumping_cues"] else None,
                "reason": "long_stop_with_dumping_cue",
            })

    track_list.sort(key=lambda t: t["track_id"])

    results_dict = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(args.source),
        "weights": args.weights,
        "plate_weights": args.plate_weights,
        "tracker": args.tracker,
        "device": args.device,
        "polygon": polygon,
        "ocr_languages": langs,
        "ocr_conf_threshold": args.ocr_conf,
        "stop_threshold_secs": args.stop_threshold,
        "frames_processed": processed,
        "total_frames_available": total_frames,
        "load_seconds": round(t_load1 - t_load0, 3),
        "wall_seconds": round(time.perf_counter() - start_wall, 3),
        "effective_fps": round(processed / (time.perf_counter() - start_wall), 2) if processed else 0,
        "total_tracks": len(track_list),
        "incident_candidates": incident_candidates,
        "tracks": track_list,
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(results_dict, indent=2))

    print(f"\n=== ANPR Pipeline complete ===")
    print(f"Frames: {processed} | Tracks: {len(track_list)} | FPS: {results_dict['effective_fps']:.1f}")
    print(f"Incident candidates: {len(incident_candidates)}")
    print(f"Results: {out_path}")

    for ic in incident_candidates:
        print(f"  Track {ic['track_id']} ({ic['vehicle_type']}): plate={ic['plate_text']}, "
              f"stop={ic['longest_stop_secs']}s, cues={ic['dumping_cue_count']}")

    for t in track_list:
        if t["plate_consensus"]:
            print(f"  Track {t['track_id']} ({t['vehicle_type']}): plate={t['plate_consensus']['text']} "
                  f"({t['plate_consensus']['read_count']}/{t['plate_consensus']['total_reads']} reads)")


if __name__ == "__main__":
    main()