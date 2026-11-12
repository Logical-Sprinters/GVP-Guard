# Officer Training Materials — GVP-Guard NightEye AI

**Version:** 0.1  
**Date:** 2026-11-06  
**Owner:** Frontend / UI / UX (Janed Patel + Smeet Jariwala)  
**Status:** Draft — for pilot officer training

---

## Purpose

These materials train authorized officers on how to use the GVP-Guard prototype for illegal dumping incident review. Training is required before any officer accesses the system.

**Claim discipline:** The prototype never issues automatic fines. Human review is mandatory. All decisions are review-ready incident records, not legally admissible evidence.

---

## System Overview

GVP-Guard is a controlled-footage proof of concept that:

- Captures video from recorded files, webcam, or RTSP/CCTV cameras
- Detects scene changes inside GVP (Garbage Vulnerable Point) zones using a scene-stability heuristic
- Creates before/during/after evidence frames for officer review
- Allows officers to approve, reject, or request cleanup for each incident
- Stores incidents locally or in an optional backend (SQLite + object storage)

---

## Roles & Permissions

| Role | Can View | Can Write (Create/Decide/Cleanup) | Can Manage Users |
|------|----------|-----------------------------------|------------------|
| Viewer | Incidents, history, map, system status | No | No |
| Officer | All read-only views | Yes (incidents, decisions, cleanup requests) | No |
| Admin | All views | Yes | Yes (create users, update roles, deactivate) |

---

## Officer Workflow

### Step 1: Sign In

1. Open the GVP-Guard interface in a browser
2. Enter your username and password
3. Click **Sign In**
4. If you don't have credentials, contact your system administrator (admin role)

**Demo credentials (training only):** `admin / admin123` or `officer / officer123`

### Step 2: Choose a Source

Select one of the following:
- **Recorded video** — Upload a controlled clip (MP4, AVI, MOV, etc.)
- **Webcam** — Use the computer's camera for live input
- **RTSP camera** — Connect to a GMC-approved CCTV stream via Camera ID

### Step 3: Set the GVP Zone

1. Click **Edit polygon** to define the Garbage Vulnerable Point zone
2. Click to add vertices, drag to adjust, double-click to finish
3. Click **Save zone** to persist the polygon
4. The zone is stored as normalised [0..1] coordinates

### Step 4: Run Analysis or Monitoring

- **Run Event Analysis** — Analyze a recorded video at 10%, 52%, and 90% of its duration
- **Start monitoring** — Use the scene-stability heuristic on live input (webcam or RTSP)

**Important:** Monitoring uses scene-stability only — it does NOT detect vehicles, track stops, measure dumping, or read plates. All results require officer review.

### Step 5: Review the Incident

When an incident is generated:

1. **Review evidence frames** — Before, during, and after the detected event
2. **Check the plate** — If a plate was read (DEMO STAGE), verify it visually; never trust OCR blindly
3. **Read the cue score** — This is an uncalibrated pixel-difference heuristic, not a trained model
4. **Add a comment** — Optional comment or reject reason
5. **Enter reviewer name** — Defaults to "Demo officer"

### Step 6: Make a Decision

Choose one of three actions:

| Decision | Meaning |
|----------|---------|
| **Approved for follow-up** | Incident warrants further investigation |
| **Rejected — insufficient evidence** | No actionable evidence; incident closed |
| **Cleanup requested** | Waste/object needs cleanup; assign an officer |

**Never** issue an automatic fine. All decisions require human judgment.

### Step 7: Cleanup Request (if applicable)

1. If you select "Cleanup requested," fill in the assigned officer name
2. The cleanup request is logged with a timestamp
3. The assigned officer can mark it **Complete** when done
4. You can close the cleanup request at any time

---

## Evidence Handling

- Evidence frames are JPEG images captured from the video source
- In API mode, frames are stored in object storage with SHA-256 checksums
- Signed, time-limited URLs gate all evidence access
- Every view/download of evidence is logged in a chain-of-custody access log
- **This is NOT a legal chain of custody** — not admissible as evidence in court

---

## Do's and Don'ts

### Do
- Review every incident before making a decision
- Verify plate reads visually before trusting them
- Add comments explaining your reasoning
- Use the correct role for your actions
- Log out when finished

### Don't
- Trust the cue score as proof of dumping — it's an uncalibrated heuristic
- Issue automatic fines — the system never does this, and neither should you
- Assume a long stop means guilt — stop time alone does NOT imply guilt
- Share footage or incident records outside the authorized team
- Use unapproved footage — only GMC-approved footage for pilot testing

---

## Common Scenarios

| Scenario | Expected Officer Action |
|----------|------------------------|
| Vehicle passes through zone without stopping | No incident or reject |
| Vehicle stops long, no object deposited | Review, likely reject |
| Person deposits object near stopped vehicle | Review, consider cleanup |
| Waste present before vehicle arrives | Do not blame arriving vehicle |
| Plate unreadable | Retain incident without invented plate |
| Network fails during review | Incident queued locally; syncs when restored |

---

## Escalation

Report any of the following to the Team Lead immediately:

- Unapproved footage being used
- System issuing or suggesting automatic fines
- Unauthorized access to incident records
- Footage retention beyond the approved period
- Any privacy concern (faces, plates, unrelated individuals)

---

## References

- docs/MVP2_PLAN.md — MVP-2 field validation acceptance criteria
- docs/GMC_PERMISSION_WORKFLOW.md — GMC permission and footage handling
- docs/08_SECURITY_PRIVACY.md — Security and privacy principles
- docs/06_API_SPEC.md — API specification (for technical reference)
