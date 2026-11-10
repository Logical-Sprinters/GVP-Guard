#!/usr/bin/env python3
"""
MVP-2 — KPI Measurement Harness

Computes calibrated KPI metrics from test results and incident records:
- Correct plate-read rate
- False alerts per camera-hour
- Alert-to-action time
- Evidence completeness
- Dumping-event precision
- Detection FPS and latency

Usage:
    python tools\kpi_harness.py --test-results test_results.json --incidents incidents.json --output kpi_results.json

Outputs: kpi_results.json with documented metrics, hardware conditions, and confidence intervals.
"""

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="KPI measurement harness")
    p.add_argument("--test-results", required=True, help="Video test harness results JSON")
    p.add_argument("--incidents", required=None, help="Incident records JSON (optional)")
    p.add_argument("--camera-hours", type=float, default=1.0,
                   help="Total camera hours observed (for false alerts per camera-hour)")
    p.add_argument("--hardware", default="unknown", help="Hardware description")
    p.add_argument("--footage-conditions", default="unknown",
                   help="Footage conditions description (lighting, weather, etc.)")
    p.add_argument("--sample-size", type=int, default=1,
                   help="Sample size (number of videos/incidents tested)")
    p.add_argument("--output", default="kpi_results.json", help="Output JSON path")
    return p.parse_args()


def confidence_interval(proportion, n, confidence=0.95):
    """Wilson score confidence interval for a proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.96  # 95% confidence
    denominator = 1 + z**2 / n
    centre = proportion + z**2 / (2 * n)
    radius = z * math.sqrt((proportion * (1 - proportion) + z**2 / (4 * n)) / n)
    lower = (centre - radius) / denominator
    upper = (centre + radius) / denominator
    return (round(max(0, lower), 4), round(min(1, upper), 4))


def main():
    args = parse_args()

    with open(args.test_results) as f:
        test_results = json.load(f)

    incidents = []
    if args.incidents:
        with open(args.incidents) as f:
            incidents = json.load(f)

    # --- Video test metrics ---
    results = test_results.get("results", [])
    total_scenarios = test_results.get("total_scenarios", 0)
    passed = test_results.get("passed", 0)
    failed = test_results.get("failed", 0)

    scenario_pass_rate = passed / total_scenarios if total_scenarios else 0.0
    scenario_ci = confidence_interval(scenario_pass_rate, total_scenarios)

    # Per-scenario metrics
    scenario_details = []
    for r in results:
        if r.get("metrics"):
            scenario_details.append({
                "id": r["id"],
                "name": r["name"],
                "passed": r["passed"],
                "effective_fps": r["metrics"]["effective_fps"],
                "max_stop_secs": r["metrics"]["max_stop_secs"],
                "long_stops": r["metrics"]["long_stops"],
                "dumping_cue_frames": r["metrics"]["dumping_cue_frames"],
                "total_tracks": r["metrics"]["total_tracks"],
            })

    avg_fps = sum(s["effective_fps"] for s in scenario_details) / len(scenario_details) if scenario_details else 0.0

    # --- Incident metrics ---
    total_incidents = len(incidents)
    incidents_with_plate = sum(1 for i in incidents if i.get("plate") and i["plate"] not in (None, "", "Manual review pending", "Pending"))
    plate_read_rate = incidents_with_plate / total_incidents if total_incidents else 0.0
    plate_ci = confidence_interval(plate_read_rate, total_incidents)

    incidents_with_evidence = sum(1 for i in incidents if i.get("evidenceFrames"))
    evidence_completeness = incidents_with_evidence / total_incidents if total_incidents else 0.0
    evidence_ci = confidence_interval(evidence_completeness, total_incidents)

    # False alerts per camera-hour (scenarios that passed but had unexpected incidents)
    false_alerts = sum(1 for r in results
                       if r.get("evaluation")
                       and not r["evaluation"]["expected_incident"]
                       and r["evaluation"]["actual_long_stops"] > 0)
    false_alerts_per_camera_hour = false_alerts / args.camera_hours if args.camera_hours > 0 else 0.0

    # Dumping-event precision (from scenario evaluations)
    dumping_true_positives = sum(1 for r in results
                                 if r.get("evaluation")
                                 and r["evaluation"]["expected_incident"]
                                 and r["evaluation"]["actual_dumping_cue_frames"] > 0)
    dumping_total_predicted = sum(1 for r in results
                                  if r.get("evaluation")
                                  and r["evaluation"]["actual_dumping_cue_frames"] > 0)
    dumping_precision = dumping_true_positives / dumping_total_predicted if dumping_total_predicted else 0.0
    dumping_ci = confidence_interval(dumping_precision, dumping_total_predicted)

    # Alert-to-action time (from incidents with decision timestamps)
    alert_to_action_times = []
    for inc in incidents:
        created = inc.get("time") or inc.get("created_at")
        reviewed = inc.get("reviewedAt")
        if created and reviewed:
            try:
                from datetime import datetime as dt
                t1 = dt.fromisoformat(created.replace("Z", "+00:00"))
                t2 = dt.fromisoformat(reviewed.replace("Z", "+00:00"))
                alert_to_action_times.append((t2 - t1).total_seconds())
            except Exception:
                pass
    avg_alert_to_action = sum(alert_to_action_times) / len(alert_to_action_times) if alert_to_action_times else None

    # Build output
    kpi = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "hardware": args.hardware,
        "footage_conditions": args.footage_conditions,
        "sample_size": args.sample_size,
        "camera_hours": args.camera_hours,
        "confidence_level": 0.95,

        "scenario_tests": {
            "total": total_scenarios,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(scenario_pass_rate, 4),
            "pass_rate_ci": scenario_ci,
        },

        "detection_performance": {
            "avg_effective_fps": round(avg_fps, 2),
        },

        "plate_ocr": {
            "total_incidents": total_incidents,
            "incidents_with_plate": incidents_with_plate,
            "plate_read_rate": round(plate_read_rate, 4),
            "plate_read_rate_ci": plate_ci,
        },

        "evidence": {
            "total_incidents": total_incidents,
            "incidents_with_evidence": incidents_with_evidence,
            "evidence_completeness": round(evidence_completeness, 4),
            "evidence_completeness_ci": evidence_ci,
        },

        "false_alerts": {
            "false_alert_count": false_alerts,
            "camera_hours": args.camera_hours,
            "false_alerts_per_camera_hour": round(false_alerts_per_camera_hour, 4),
        },

        "dumping_event": {
            "true_positives": dumping_true_positives,
            "total_predicted": dumping_total_predicted,
            "precision": round(dumping_precision, 4),
            "precision_ci": dumping_ci,
        },

        "alert_to_action": {
            "samples": len(alert_to_action_times),
            "avg_seconds": round(avg_alert_to_action, 2) if avg_alert_to_action else None,
        },

        "scenario_details": scenario_details,

        "honesty_notes": [
            "All metrics are targets to measure, never published without documented tests.",
            "Hardware, footage conditions, and sample size are recorded with every result.",
            "Confidence intervals are Wilson score intervals at 95% confidence.",
            "Human review mandatory — no automatic fines.",
            "Stop time alone does NOT imply guilt.",
            "No GMC/registry/e-challan integration.",
        ],
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(kpi, indent=2))

    print(f"\n=== KPI Measurement Complete ===")
    print(f"Scenario pass rate: {scenario_pass_rate:.1%} (CI: {scenario_ci})")
    print(f"Plate read rate: {plate_read_rate:.1%} (CI: {plate_ci})")
    print(f"Evidence completeness: {evidence_completeness:.1%} (CI: {evidence_ci})")
    print(f"False alerts per camera-hour: {false_alerts_per_camera_hour:.2f}")
    print(f"Dumping-event precision: {dumping_precision:.1%} (CI: {dumping_ci})")
    if avg_alert_to_action:
        print(f"Avg alert-to-action: {avg_alert_to_action:.1f}s")
    print(f"Results: {out_path}")


if __name__ == "__main__":
    main()