# Deployment Runbook (Draft)

## Environments
- Local development
- Shared integration/demo
- Pilot staging
- Authorized production (future)

## Pre-deployment
- Tests pass
- Database migration reviewed
- Secrets configured
- Storage permissions tested
- Camera access authorized
- Retention settings approved
- Backup created

## Services
Frontend, API, database, object storage, worker/inference service and reverse proxy. Use Docker Compose for development; choose pilot hosting after benchmarking.

## Health checks
API readiness, database connectivity, storage write/read, queue depth, camera heartbeat, disk space and model load.

## Rollback
Keep previous image/version and reversible migrations. If incident integrity is at risk, stop ingestion and preserve evidence rather than partially processing.

## Incident response
1. Detect and classify severity
2. Disable affected integration if needed
3. Preserve logs/evidence
4. Restore service
5. Notify authorized stakeholders
6. Document root cause and prevention

## Pilot checklist
Authorized camera, calibrated GVP zone, time sync, network test, officer account, cleanup contact, baseline data and daily review meeting.
