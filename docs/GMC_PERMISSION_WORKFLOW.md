# GMC Permission & Approved Footage Workflow

**Version:** 0.1  
**Date:** 2026-11-06  
**Owner:** Team Lead (Omkar Solat)  
**Status:** Draft — requires GMC authorization before any field deployment

---

## Purpose

This document defines the workflow for obtaining Gandhidham Municipal Corporation (GMC) permission to use CCTV camera footage for the GVP-Guard pilot, and the handling of approved footage during field validation.

**Claim discipline:** No GMC/registry/e-challan integration exists or is planned. This workflow governs manual permission and footage handling only.

---

## Who Requests Permission

| Role | Responsibility |
|------|---------------|
| **Team Lead** (Omkar Solat) | Submits the formal permission request to GMC; primary point of contact |
| **AI / Vision / Data** (Omkar Solat + Prafull Mayank Singh) | Defines footage requirements (angles, lighting, duration, vehicle types) |
| **Backend / Database / Evidence** (Shivansh Gupta + Jay Katkar) | Defines storage, retention, and chain-of-custody requirements for approved footage |
| **Integration / Testing** (Prince Rana + Sayantani Mandal) | Documents test plan and KPI measurement approach for the permission request |

---

## Permission Request Contents

The formal request to GMC must include:

1. **Purpose statement** — Controlled-footage proof of concept for illegal dumping incident review; human review mandatory; no automatic fines
2. **Camera locations** — Specific GVP zones (GVP-01, GVP-02, GVP-03) and camera angles
3. **Footage duration** — Start and end dates of the pilot window
4. **Data handling** — How footage will be stored, who can access it, retention period, deletion process
5. **Privacy safeguards** — No face recognition, no license plate registry lookup, no automatic enforcement
6. **Human review** — All incidents require officer review before any action
7. **Test plan** — Seven golden scenarios, KPI metrics, field validation conditions
8. **Contact information** — Team Lead and P. P. Savani University point of contact

---

## Approved Footage Handling

Once GMC approves footage for pilot use:

| Step | Action | Owner |
|------|--------|-------|
| 1 | Receive approved footage via secure channel (encrypted drive or authorized portal) | Team Lead |
| 2 | Record footage provenance (source, date, camera, conditions, GMC approval reference) | Integration / Testing |
| 3 | Store footage in access-controlled location; never commit to Git | Backend / Database / Evidence |
| 4 | Create ground-truth annotations for the footage | AI / Vision / Data |
| 5 | Run seven golden scenarios against the footage | Integration / Testing |
| 6 | Measure KPIs with Wilson score confidence intervals | Integration / Testing |
| 7 | Delete footage after pilot per retention policy | Backend / Database / Evidence |

---

## Retention & Deletion

- Approved footage is retained only for the pilot duration (maximum 90 days unless GMC approves extension)
- Footage is deleted after KPI measurement and test record storage are complete
- Deletion is logged in the audit trail
- No footage is shared outside the pilot team without GMC written approval

---

## Privacy Safeguards

- **No face recognition** — faces are not processed or stored
- **No license plate registry lookup** — plates are read only for incident review, never matched against owner registries
- **No automatic fines** — all decisions require human officer review
- **Minimum necessary data** — only footage within GVP polygons is processed
- **No e-challan integration** — no connection to traffic enforcement systems

---

## Escalation

Any deviation from this workflow (unapproved footage, extended retention, unauthorized access) must be reported to the Team Lead immediately and documented in the test record.

---

## References

- docs/MVP2_PLAN.md — MVP-2 field validation acceptance criteria
- docs/08_SECURITY_PRIVACY.md — Security and privacy principles
- docs/15_IMPLEMENTATION_STATUS.md — Implementation ledger

