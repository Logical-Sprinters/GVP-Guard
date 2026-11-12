#!/usr/bin/env python3
"""
MVP-2 — Test Record Storage

Stores test records for every release, capturing:
- Dataset version
- Git commit
- Model version
- Test configuration
- Results
- Limitations

Usage:
    python tools/test_record_storage.py --commit <sha> --test-results test_results.json --kpi-results kpi_results.json --output test_records.json

Outputs: test_records.json (append-only log of all test records)
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Store test records for a release")
    p.add_argument("--commit", required=True, help="Git commit SHA")
    p.add_argument("--test-results", required=None, help="Video test harness results JSON")
    p.add_argument("--kpi-results", required=None, help="KPI measurement results JSON")
    p.add_argument("--model-version", default="unknown", help="Model version (e.g. yolo11n)")
    p.add_argument("--dataset-version", default="unknown", help="Dataset version identifier")
    p.add_argument("--hardware", default="unknown", help="Hardware description")
    p.add_argument("--footage-conditions", default="unknown", help="Footage conditions")
    p.add_argument("--limitations", default="", help="Known limitations of this test run")
    p.add_argument("--output", default="test_records.json", help="Output/test record log path")
    return p.parse_args()


def get_git_info(commit_sha):
    """Get git repository info for the given commit."""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        branch = "unknown"

    try:
        date = subprocess.check_output(
            ["git", "log", "-1", "--format=%ci", commit_sha],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        date = "unknown"

    try:
        message = subprocess.check_output(
            ["git", "log", "-1", "--format=%s", commit_sha],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        message = "unknown"

    return {
        "commit": commit_sha,
        "branch": branch,
        "commit_date": date,
        "commit_message": message,
    }


def load_json(path):
    if path is None:
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        return {"_error": f"Could not load {path}: {e}"}


def compute_file_hash(path):
    """SHA-256 of a file for integrity tracking."""
    if path is None:
        return None
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def main():
    args = parse_args()

    git_info = get_git_info(args.commit)

    test_results = load_json(args.test_results)
    kpi_results = load_json(args.kpi_results)

    # Extract key metrics from results
    scenario_summary = None
    if test_results and isinstance(test_results, dict):
        scenario_summary = {
            "total_scenarios": test_results.get("total_scenarios"),
            "passed": test_results.get("passed"),
            "failed": test_results.get("failed"),
            "pass_rate": test_results.get("pass_rate"),
        }

    kpi_summary = None
    if kpi_results and isinstance(kpi_results, dict):
        kpi_summary = {
            "scenario_pass_rate": kpi_results.get("scenario_tests", {}).get("pass_rate"),
            "plate_read_rate": kpi_results.get("plate_ocr", {}).get("plate_read_rate"),
            "evidence_completeness": kpi_results.get("evidence", {}).get("evidence_completeness"),
            "false_alerts_per_camera_hour": kpi_results.get("false_alerts", {}).get("false_alerts_per_camera_hour"),
            "dumping_event_precision": kpi_results.get("dumping_event", {}).get("precision"),
        }

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git": git_info,
        "model_version": args.model_version,
        "dataset_version": args.dataset_version,
        "hardware": args.hardware,
        "footage_conditions": args.footage_conditions,
        "limitations": args.limitations,
        "test_results_file": args.test_results,
        "test_results_hash": compute_file_hash(args.test_results),
        "kpi_results_file": args.kpi_results,
        "kpi_results_hash": compute_file_hash(args.kpi_results),
        "scenario_summary": scenario_summary,
        "kpi_summary": kpi_summary,
        "honesty_notes": [
            "All metrics are targets to measure, never published without documented tests.",
            "Hardware, footage conditions, and sample size are recorded with every result.",
            "Test records are append-only — never modify or delete historical records.",
            "Human review mandatory — no automatic fines.",
            "Stop time alone does NOT imply guilt.",
            "No GMC/registry/e-challan integration.",
        ],
    }

    # Append to test records log (append-only)
    output_path = Path(args.output)
    records = []
    if output_path.exists():
        try:
            with open(output_path) as f:
                existing = json.load(f)
            if isinstance(existing, list):
                records = existing
        except Exception:
            records = []

    records.append(record)
    output_path.write_text(json.dumps(records, indent=2))

    print(f"\n=== Test Record Stored ===")
    print(f"Commit: {args.commit[:12]} ({git_info['branch']})")
    print(f"Model: {args.model_version}")
    print(f"Dataset: {args.dataset_version}")
    print(f"Record: {output_path}")
    print(f"Total records: {len(records)}")


if __name__ == "__main__":
    main()
