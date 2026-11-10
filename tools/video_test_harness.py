#!/usr/bin/env python3
"""
MVP-2 — Video Test Harness for Seven Golden Scenarios

Runs controlled video clips through the GVP-Guard detection pipeline and
compares outcomes against expected results for each golden scenario.

Usage:
    python tools\video_test_harness.py --scenarios scenarios.json --output test_results.json

Scenario format (scenarios.json):
{
  "scenarios": [
    {
      "id": "GS-01",
      "name": "Normal pass",
      "video": "path/to/normal_pass.mp4",
      "expected_incident": false,
      "expected_plate": null,
      "max_stop_secs": 1.0,
      "notes": "Vehicle passes through zone without stopping"
    },
    {
      "id": "GS-02",
      "name": "Long stop, no deposit",
      "video": "path/to/long_stop.mp4",
      "expected_incident": true,
      "expected_decision": "Rejected",
      "max_stop_secs": 10.0,
      "notes": "Vehicle stops but no object deposited"
    },
    ...
  ]
}

Outputs: test_results.json with per-scenario pass/fail and metrics.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

VEHICLE_CLASS_IDS = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
PERSON_CLASS_ID = 0

DEFAULT_POLYGON = [
    {"x": 0.10, "y": 0.60},
    {"x": 0.90, "y": 0.60},
    {"x": 0.90, "y": 1.00},
    {"x": 0.10, "y": 1.00},
]


def parse_args():
    p = argparse.ArgumentParser(description="Video test harness for golden scenarios")
    p.add_argument("--scenarios", required=True, help="Scenarios JSON file")
    p.add_argument("--weights", default="models/weights/yolo11n.pt", help="YOLO11n .pt weights")
    p.add_argument("--tracker", default="bytetrack.yaml", help="ByteTrack config file")
    p.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold")
    p.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    p.add_argument("--device", default="cpu", help="cpu or cuda:0")
    p.add_argument("--stop-threshold", type=float, default=2.0,
                   help="Seconds stopped to count as a 'stop'")
    p.add_argument("--max-frames", type=int, default=0, help="Max frames per video (0 = all)")
    p.add_argument("--output", default="test_results.json", help="Output JSON path")
    p.add_argument("--polygon", default=None, help='JSON polygon string')
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


def boxes_overlap(box_a, box_b, threshold=0.15):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    ix1 = max(ax1, bx1); iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2); iy2 = min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return False
    inter = (ix2 - ix1) * (iy2 - iy1)
    a_area = (ax2 - ax1) * (ay2 - ay1)
    if a_area <= 0:
        return False
    return (inter / a_area) > threshold


def analyze_video(video_path, model, tracker, conf, imgsz, device,
                  stop_threshold, max_frames, polygon):
    """Run detection + tracking on a video and return summary metrics."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    tracks = {}
    frame_idx = 0
    processed = 0
    start_wall = time.perf_counter()
    max_stop_secs = 0.0
    dumping_cue_frames = 0
    person_overlap_frames = 0

    try:
        while True:
            if max_frames and processed >= max_frames:
                break
            ret, frame = cap.read()
            if not ret:
                break
            h, w = frame.shape[:2]

            results = model.track(
                frame,
                conf=conf,
                imgsz=imgsz,
                device=device,
                tracker=tracker,
                verbose=False,
                persist=True,
            )

            current_track_ids = set()
            persons = []

            for r in results:
                if r.boxes is None:
                    continue
                boxes = r.boxes.xyxy.cpu().numpy() if r.boxes.xyxy is not None else np.empty((0, 4))
                track_ids = r.boxes.id.cpu().numpy().astype(int) if r.boxes.id is not None else np.empty((0,), dtype=int)
                class_ids = r.boxes.cls.cpu().numpy().astype(int) if r.boxes.cls is not None else np.empty((0,), dtype=int)

                for box, tid, cid in zip(boxes, track_ids, class_ids):
                    x1, y1, x2, y2 = [float(v) for v in box]
                    if cid == PERSON_CLASS_ID:
                        persons.append([x1, y1, x2, y2])
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
                            "dumping_cue_frames": 0,
                            "person_overlap_frames": 0,
                            "max_conf": 0.0,
                            "last_frame": frame_idx,
                        }
                    trk = tracks[tid]
                    trk["last_frame"] = frame_idx

                    inside = point_in_polygon({"x": cx, "y": cy}, polygon)
                    if inside and not trk["in_polygon"]:
                        trk["in_polygon"] = True
                        trk["stop_start_frame"] = frame_idx
                    elif not inside and trk["in_polygon"]:
                        trk["in_polygon"] = False
                        if trk["stop_start_frame"] is not None:
                            stop_frames = frame_idx - trk["stop_start_frame"]
                            stop_secs = stop_frames / fps
                            trk["stop_events"].append({
                                "start_frame": trk["stop_start_frame"],
                                "end_frame": frame_idx,
                                "duration_secs": round(stop_secs, 2),
                            })
                            trk["stop_start_frame"] = None

                    if inside:
                        vehicle_box = [x1, y1, x2, y2]
                        for pbox in persons:
                            if boxes_overlap(vehicle_box, pbox, threshold=0.15):
                                trk["dumping_cue_frames"] += 1
                                trk["person_overlap_frames"] += 1

            processed += 1
            frame_idx += 1

        # Finalise tracks still in polygon
        now_frame = frame_idx
        for tid, trk in tracks.items():
            if trk["in_polygon"] and trk["stop_start_frame"] is not None:
                stop_frames = now_frame - trk["stop_start_frame"]
                stop_secs = stop_frames / fps
                trk["stop_events"].append({
                    "start_frame": trk["stop_start_frame"],
                    "end_frame": now_frame,
                    "duration_secs": round(stop_secs, 2),
                })
                trk["stop_start_frame"] = None
                trk["in_polygon"] = False

    finally:
        cap.release()

    # Aggregate metrics
    for trk in tracks.values():
        for ev in trk["stop_events"]:
            max_stop_secs = max(max_stop_secs, ev["duration_secs"])
        dumping_cue_frames += trk["dumping_cue_frames"]
        person_overlap_frames += trk["person_overlap_frames"]

    long_stops = sum(
        1 for trk in tracks.values()
        for ev in trk["stop_events"]
        if ev["duration_secs"] >= stop_threshold
    )

    return {
        "video": str(video_path),
        "fps": fps,
        "total_frames": total_frames,
        "processed_frames": processed,
        "wall_seconds": round(time.perf_counter() - start_wall, 3),
        "effective_fps": round(processed / (time.perf_counter() - start_wall), 2) if processed else 0,
        "total_tracks": len(tracks),
        "long_stops": long_stops,
        "max_stop_secs": round(max_stop_secs, 2),
        "dumping_cue_frames": dumping_cue_frames,
        "person_overlap_frames": person_overlap_frames,
        "tracks": [
            {
                "track_id": trk["track_id"],
                "vehicle_type": trk["vehicle_type"],
                "stop_events": trk["stop_events"],
                "total_stop_secs": round(sum(e["duration_secs"] for e in trk["stop_events"]), 2),
                "long_stop_count": sum(1 for e in trk["stop_events"] if e["duration_secs"] >= stop_threshold),
                "dumping_cue_frames": trk["dumping_cue_frames"],
                "person_overlap_frames": trk["person_overlap_frames"],
            }
            for trk in tracks.values()
        ],
    }


def evaluate_scenario(scenario, metrics):
    """Compare metrics against expected scenario outcome."""
    expected_incident = scenario.get("expected_incident", False)
    expected_decision = scenario.get("expected_decision")
    max_stop_secs = scenario.get("max_stop_secs", float("inf"))

    passed = True
    reasons = []

    # Check incident expectation
    has_long_stop = metrics["long_stops"] > 0
    has_dumping_cue = metrics["dumping_cue_frames"] > 0

    if expected_incident and not (has_long_stop or has_dumping_cue):
        passed = False
        reasons.append("Expected incident but no long stop or dumping cue detected")
    if not expected_incident and (has_long_stop or has_dumping_cue):
        passed = False
        reasons.append("Unexpected incident indicators detected")

    # Check max stop duration
    if metrics["max_stop_secs"] > max_stop_secs:
        passed = False
        reasons.append(f"Max stop {metrics['max_stop_secs']}s exceeds expected {max_stop_secs}s")

    # Check decision expectation
    if expected_decision and expected_decision not in ("Review", "Reject", "Approve", "Cleanup"):
        reasons.append(f"Decision {expected_decision} noted (manual review required)")

    return {
        "passed": passed,
        "reasons": reasons,
        "has_long_stop": has_long_stop,
        "has_dumping_cue": has_dumping_cue,
        "max_stop_secs": metrics["max_stop_secs"],
        "long_stops": metrics["long_stops"],
        "dumping_cue_frames": metrics["dumping_cue_frames"],
    }


def main():
    args = parse_args()
    polygon = load_polygon(args.polygon)

    with open(args.scenarios) as f:
        scenario_defs = json.load(f)

    scenarios = scenario_defs.get("scenarios", [])
    if not scenarios:
        raise SystemExit("No scenarios found in scenarios file")

    model = YOLO(args.weights)

    results = []
    total_passed = 0

    for sc in scenarios:
        print(f"\n=== Scenario {sc['id']}: {sc['name']} ===")
        print(f"Video: {sc['video']}")

        try:
            metrics = analyze_video(
                sc["video"], model, args.tracker, args.conf, args.imgsz,
                args.device, args.stop_threshold, args.max_frames, polygon,
            )
            eval_result = evaluate_scenario(sc, metrics)

            scenario_result = {
                "id": sc["id"],
                "name": sc["name"],
                "video": sc["video"],
                "passed": eval_result["passed"],
                "reasons": eval_result["reasons"],
                "metrics": metrics,
                "evaluation": {
                    "expected_incident": sc.get("expected_incident", False),
                    "expected_decision": sc.get("expected_decision"),
                    "max_stop_secs": sc.get("max_stop_secs"),
                    "actual_max_stop_secs": metrics["max_stop_secs"],
                    "actual_long_stops": metrics["long_stops"],
                    "actual_dumping_cue_frames": metrics["dumping_cue_frames"],
                },
            }
            results.append(scenario_result)

            if eval_result["passed"]:
                total_passed += 1
                print(f"✅ PASS — {eval_result['reasons'] if eval_result['reasons'] else 'all checks met'}")
            else:
                print(f"❌ FAIL — {'; '.join(eval_result['reasons'])}")

            print(f"  Tracks: {metrics['total_tracks']} | Long stops: {metrics['long_stops']} | "
                  f"Max stop: {metrics['max_stop_secs']}s | Dumping cue frames: {metrics['dumping_cue_frames']} | "
                  f"FPS: {metrics['effective_fps']:.1f}")

        except Exception as e:
            print(f"❌ ERROR — {e}")
            results.append({
                "id": sc["id"],
                "name": sc["name"],
                "video": sc["video"],
                "passed": False,
                "reasons": [f"Error: {e}"],
                "metrics": None,
                "evaluation": None,
            })

    total = len(results)
    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "scenarios_file": str(args.scenarios),
        "weights": args.weights,
        "tracker": args.tracker,
        "device": args.device,
        "stop_threshold_secs": args.stop_threshold,
        "total_scenarios": total,
        "passed": total_passed,
        "failed": total - total_passed,
        "pass_rate": round(total_passed / total, 4) if total else 0.0,
        "results": results,
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(summary, indent=2))

    print(f"\n=== Test Harness Complete ===")
    print(f"Total: {total} | Passed: {total_passed} | Failed: {total - total_passed} | "
          f"Pass rate: {summary['pass_rate']:.1%}")
    print(f"Results: {out_path}")


if __name__ == "__main__":
    main()