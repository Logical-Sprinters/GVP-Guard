#!/usr/bin/env python3
"""
Step 4 — Incident Association (DEMO STAGE)

Converts ANPR pipeline results (anpr_results.json) into incident records and
pushes them into the GVP-Guard SQLite evidence pipeline.

Usage:
    # Option A: Direct SQLite insert (no server needed)
    python tools\associate_incidents.py --input anpr_results.json --db backend/data/gvp_guard.db

    # Option B: POST to running API server
    python tools\associate_incidents.py --input anpr_results.json --api http://localhost:8000/api/v1

Outputs:
    associated_incidents.json — list of created incident IDs and their payloads

Honesty notes:
- All Step 4 features remain DEMO STAGE — not WORKING until benchmarked
- Human review mandatory — no automatic fines or guilt
- Incidents are created with statusCode=REVIEW_REQUIRED; officer decision required
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Try to import db module for direct SQLite insert
try:
    from backend import db as gvp_db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


def parse_args():
    p = argparse.ArgumentParser(description="Associate ANPR results with incident records")
    p.add_argument("--input", required=True, help="Path to anpr_results.json")
    p.add_argument("--db", default="backend/data/gvp_guard.db",
                   help="Path to SQLite database (direct insert mode)")
    p.add_argument("--api", default=None,
                   help="API base URL (e.g. http://localhost:8000/api/v1). If set, uses POST instead of direct SQLite")
    p.add_argument("--output", default="associated_incidents.json", help="Output JSON path")
    p.add_argument("--reviewer", default="Demo officer", help="Reviewer name for new incidents")
    return p.parse_args()


def make_incident_id(source, track_id, timestamp=None):
    """Generate a deterministic incident ID from source + track + timestamp."""
    ts = timestamp or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"INC-AI-{ts}-T{track_id}"


def candidate_to_incident(candidate, track, source, reviewer):
    """Convert an ANPR incident candidate + its track into an IncidentIn payload."""
    plate = candidate.get("plate_text")
    plate_conf = candidate.get("plate_confidence")
    longest_stop = candidate.get("longest_stop_secs", 0)
    cue_count = candidate.get("dumping_cue_count", 0)
    vehicle_type = track.get("vehicle_type", "unknown")
    track_id = track.get("track_id", 0)

    incident_id = make_incident_id(source, track_id)

    trigger_reasons = []
    if longest_stop > 0:
        trigger_reasons.append(f"vehicle_stop_{longest_stop:.1f}s")
    if cue_count > 0:
        trigger_reasons.append("person_object_overlap")
    if plate:
        trigger_reasons.append("plate_ocr_read")

    vehicle_data = {
        "track_id": track_id,
        "vehicle_type": vehicle_type,
        "stop_events": track.get("stop_events", []),
        "total_stop_secs": track.get("total_stop_secs", 0),
        "long_stop_count": track.get("long_stop_count", 0),
        "longest_stop_secs": track.get("longest_stop_secs", 0),
        "plate_consensus": track.get("plate_consensus"),
        "plate_reads": track.get("plate_reads", []),
        "dumping_cues": track.get("dumping_cues", []),
        "dumping_cue_count": track.get("dumping_cue_count", 0),
    }

    return {
        "id": incident_id,
        "time": datetime.now(timezone.utc).isoformat(),
        "file": source,
        "sceneChange": f"{longest_stop:.1f}s stop",
        "illustrativeCueScore": f"{min(100, longest_stop * 10 + cue_count * 20):.2f}",
        "plate": plate or "Manual review pending",
        "decision": None,
        "location": "GVP-01",
        "status": "REVIEW_REQUIRED",
        "statusCode": "REVIEW_REQUIRED",
        "demo": False,
        "triggerReasons": trigger_reasons,
        "evidenceFrames": None,
        "source": f"ANPR pipeline (YOLO11n + ByteTrack + EasyOCR) — DEMO STAGE",
        "reviewer": reviewer,
        "comment": "",
        "detectionMethod": "YOLO11n + ByteTrack vehicle detection + EasyOCR plate OCR (DEMO STAGE)",
        "vehicleData": vehicle_data,
    }


def insert_direct(db_path, incidents):
    """Insert incidents directly into SQLite via backend.db module."""
    if not DB_AVAILABLE:
        raise RuntimeError("backend.db module not available. Run from repo root or use --api mode.")

    created = []
    for inc in incidents:
        try:
            result = gvp_db.upsert_incident(inc)
            created.append({"id": inc["id"], "status": "inserted", "payload": result})
        except Exception as e:
            created.append({"id": inc["id"], "status": "error", "error": str(e)})
    return created


def post_to_api(api_base, incidents):
    """POST incidents to the FastAPI server."""
    created = []
    for inc in incidents:
        url = api_base.rstrip("/") + "/incidents"
        data = json.dumps(inc).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                created.append({"id": inc["id"], "status": "posted", "response": result})
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            created.append({"id": inc["id"], "status": "error", "error": f"HTTP {e.code}: {body}"})
        except Exception as e:
            created.append({"id": inc["id"], "status": "error", "error": str(e)})
    return created


def main():
    args = parse_args()

    # Load ANPR results
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    with open(input_path) as f:
        anpr = json.load(f)

    candidates = anpr.get("incident_candidates", [])
    tracks_by_id = {t["track_id"]: t for t in anpr.get("tracks", [])}

    if not candidates:
        print("No incident candidates found in ANPR results. Nothing to associate.")
        # Still write empty output
        out_path = Path(args.output)
        out_path.write_text(json.dumps({"created": [], "total": 0, "source": str(input_path)}, indent=2))
        print(f"Results: {out_path}")
        return

    # Build incident payloads
    incidents = []
    for cand in candidates:
        track_id = cand["track_id"]
        track = tracks_by_id.get(track_id, {})
        inc = candidate_to_incident(cand, track, str(input_path), args.reviewer)
        incidents.append(inc)

    # Insert
    if args.api:
        created = post_to_api(args.api, incidents)
        mode = "API"
    else:
        created = insert_direct(args.db, incidents)
        mode = "Direct SQLite"

    # Write output
    output = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(input_path),
        "mode": mode,
        "total_candidates": len(candidates),
        "created": created,
    }
    out_path = Path(args.output)
    out_path.write_text(json.dumps(output, indent=2))

    print(f"\n=== Incident Association complete ===")
    print(f"Mode: {mode} | Candidates: {len(candidates)} | Created: {sum(1 for c in created if c['status'] in ('inserted', 'posted'))}")
    print(f"Results: {out_path}")
    for c in created:
        status = c["status"]
        mark = "✅" if status in ("inserted", "posted") else "❌"
        print(f"  {mark} {c['id']}: {status}")


if __name__ == "__main__":
    main()