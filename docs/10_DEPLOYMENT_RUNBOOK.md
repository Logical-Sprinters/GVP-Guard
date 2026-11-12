# Deployment Runbook

## Environments
- Local development
- Shared integration/demo
- Pilot staging
- Authorized production (future)

## Pre-deployment
- Tests pass (`python -m unittest backend.test_db -v` and `npm test`)
- Database migration reviewed
- Secrets configured (GVP_SECRET_KEY)
- Storage permissions tested
- Camera access authorized
- Retention settings approved
- Backup created

## Deployment Options

### Docker Compose (recommended)

```bash
# Build and start
docker compose up -d --build

# View logs
docker compose logs -f gvp-guard

# Stop
docker compose down

# Open the application
open http://localhost:8000
```

The Docker image serves both the static frontend and the `/api/v1` API on the same origin.
SQLite database and evidence files are persisted in the `gvp-data` volume.

### Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GVP_SECRET_KEY` | Signing secret for JWT tokens and signed evidence URLs | `gvp-guard-dev-secret-change-in-production` |
| `PORT` | HTTP port | `8000` |

**Important:** Change `GVP_SECRET_KEY` in production. Do not commit secrets to Git.

### Manual (no Docker)

```bash
# Backend API
python3 -m pip install -r backend/requirements.txt
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000

# Frontend only (offline mode)
python3 -m http.server 8000 --bind 0.0.0.0
```

## Health checks

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | Overall service health, dependency status, camera status |
| `GET /api/v1/metrics` | Prometheus-compatible metrics (request counts, latency, incident count, camera FPS) |

## Services

Frontend, API, database (SQLite), object storage (local filesystem), RTSP capture workers, reverse proxy.
Use Docker Compose for development; choose pilot hosting after benchmarking.

## Observability

- **Structured JSON logs**: All requests logged with method, path, status, duration, client IP
- **Metrics endpoint**: Prometheus-compatible text format at `/api/v1/metrics`
- **Health endpoint**: `/api/v1/health` with dependency and camera status
- **Docker healthcheck**: Built into the Dockerfile, checks `/api/v1/health` every 30s

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

## Security

- Non-root user in Docker container
- Security headers middleware (CSP, nosniff, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy)
- Rate limiting middleware (sliding window per client IP)
- Signed, time-limited evidence URLs
- Stream credentials never in source code or logs
