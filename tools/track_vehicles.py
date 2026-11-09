#!/usr/bin/env python3
"""
Step 4.2: Vehicle Tracking with ByteTrack — DEMO STAGE

Tracks vehicles across frames using YOLO11n + ByteTrack. Outputs per-track
stop durations inside a configurable GVP polygon zone.

Prerequisites:
- ultralytics installed (torch + ultralytics)
- models/weights/yolo11n.pt downloaded
- Controlled dataset available

Usage:
    python tools\track_vehicles.py --source <video_or_dir> --weights models\weights\yolo11n.pt

Outputs:
    tracking_results.json — per-track vehicle events with stop durations
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

VEHICLE_CLASS_IDS = {0: "person", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

# Default GVP polygon (normalised [0..1] coords) — adjustable via --polygon
DEFAULT_POLYGON = [
    {"x": 0.10, "y": 0.60},
    {"x": 0.90, "y": 0.60},
    {"x": 0.90, "y": 1.00},
    {"x": 0.10, "y": 1.00},
]


def parse_args():
    p = argparse.ArgumentParser(description="YOLO11n + ByteTrack vehicle tracking")
    p.add_argument("--source", required=True, help="Video file or directory of images")
    p.add_argument("--weights", default="models/weights/yolo11n.pt", help="Path to .pt weights")
    p.add_argument("--tracker", default="bytetrack.yaml", help="ByteTrack config file")
    p.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    p.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    p.add_argument("--device", default="cpu", help="cpu or cuda:0")
    p.add_argument("--stop-threshold", type=float, default=2.0,
                   help="Seconds stopped to count as a 'stop'")
    p.add_argument("--max-frames", type=int, default=0, help="Max frames (0 = all)")
    p.add_argument("--output", default="tracking_results.json", help="Output JSON path")
    p.add_argument("--polygon", default=None,
                   help='JSON string of polygon points [{"x":0.1,"y":0.6},...]')
    return p.parse_args()


def load_polygon(polygon_arg):
    if polygon_arg:
        return json.loads(polygon_arg)
    return DEFAULT_POLYGON


def point_in_polygon(point, polygon):
    """Ray casting point-in-polygon. point={x,y}, polygon=[{x,y},...] normalised [0..1]."""
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
        frame = cv2.imread(str(source[idx]))
        return frame


def main():
    args = parse_args()
    polygon = load_polygon(args.polygon)

    t_load0 = time.perf_counter()
    model = YOLO(args.weights)
    t_load1 = time.perf_counter()

    source, is_video, total_frames = open_source(args.source)

    # State per track ID
    tracks = {}  # track_id -> { vehicle_type, stop_start, in_polygon, stop_events, ... }

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

            # Run YOLO11n + ByteTrack
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

            for r in results:
                if r.boxes is None or r.boxes.id is None:
                    continue
                boxes = r.boxes.xyxy.cpu().numpy()
                track_ids = r.boxes.id.cpu().numpy().astype(int)
                class_ids = r.boxes.cls.cpu().numpy().astype(int)
                confs = r.boxes.conf.cpu().numpy()

                for box, tid, cid, conf in zip(boxes, track_ids, class_ids, confs):
                    if cid not in VEHICLE_CLASS_IDS:
                        continue

                    x1, y1, x2, y2 = box
                    cx = (x1 + x2) / 2 / w   # normalised [0..1]
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
                            "max_conf": float(conf),
                            "last_frame": frame_idx,
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
                            stop_secs = stop_frames / 25.0  # assume 25 fps
                            trk["stop_events"].append({
                                "start_frame": trk["stop_start_frame"],
                                "end_frame": frame_idx,
                                "duration_secs": round(stop_secs, 2),
                            })
                            trk["stop_start_frame"] = None

            processed += 1
            frame_idx += 1

            if processed % 10 == 0:
                fps = processed / (time.perf_counter() - start_wall)
                print(f"  processed {processed} frames, {fps:.1f} fps, active tracks: {len(current_track_ids)}")

    finally:
        if is_video:
            source.release()

    # Finalise any tracks still in polygon at end of video
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
    for tid, trk in tracks.items():
        total_stop = sum(e["duration_secs"] for e in trk["stop_events"])
        long_stops = [e for e in trk["stop_events"] if e["duration_secs"] >= args.stop_threshold]
        track_list.append({
            "track_id": trk["track_id"],
            "vehicle_type": trk["vehicle_type"],
            "first_seen_frame": trk["first_seen_frame"],
            "last_frame": trk["last_frame"],
            "max_confidence": round(trk["max_conf"], 2),
            "stop_events": trk["stop_events"],
            "total_stop_secs": round(total_stop, 2),
            "long_stop_count": len(long_stops),
            "longest_stop_secs": round(max([e["duration_secs"] for e in trk["stop_events"]], default=0), 2),
        })

    track_list.sort(key=lambda t: t["track_id"])

    results_dict = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(args.source),
        "weights": args.weights,
        "tracker": args.tracker,
        "device": args.device,
        "polygon": polygon,
        "frames_processed": processed,
        "total_frames_available": total_frames,
        "load_seconds": round(t_load1 - t_load0, 3),
        "wall_seconds": round(time.perf_counter() - start_wall, 3),
        "effective_fps": round(processed / (time.perf_counter() - start_wall), 2) if processed else 0,
        "total_tracks": len(track_list),
        "tracks": track_list,
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(results_dict, indent=2))

    print(f"\n=== Tracking complete ===")
    print(f"Frames: {processed} | Tracks: {len(track_list)} | FPS: {results_dict['effective_fps']:.1f}")
    print(f"Results: {out_path}")

    for t in track_list:
        if t["long_stop_count"] > 0:
            print(f"  Track {t['track_id']} ({t['vehicle_type']}): {t['long_stop_count']} long stop(s), "
                  f"longest {t['longest_stop_secs']}s")


if __name__ == "__main__":
    main()