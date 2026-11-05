# GVP-Guard API (optional)

A small, dependency-light FastAPI service implementing the first slice of
[`docs/06_API_SPEC.md`](../docs/06_API_SPEC.md) and
[`docs/07_DATABASE_SCHEMA.md`](../docs/07_DATABASE_SCHEMA.md).

## Why one server

`app.py` serves **both** the static prototype (`/`, `/assets/**`) and the API
(`/api/v1/**`) on the same origin. Browser code therefore uses relative URLs
only — no CORS configuration and no `localhost` calls from the client.

## Run

```bash
cd /path/to/GVP-Guard
python3 -m pip install -r backend/requirements.txt
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/`. The header badge changes from
"Local browser storage" to "API persistence (SQLite)". The SQLite file is
created at `backend/data/gvp_guard.db` and is git-ignored.

**Offline mode:** serve the repo with `python3 -m http.server 8000 --bind 0.0.0.0`
instead. The page detects the missing API and keeps working with `localStorage`.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | Feature detection / readiness |
| GET | `/api/v1/incidents?status=&camera=` | List incidents |
| POST | `/api/v1/incidents` | Upsert an incident (also writes an audit row) |
| DELETE | `/api/v1/incidents` | Clear incidents (demo helper) |
| GET | `/api/v1/incidents/{id}` | Read one incident |
| PATCH | `/api/v1/incidents/{id}` | Partial update |
| POST | `/api/v1/incidents/{id}/decision` | Record officer decision + audit |
| GET | `/api/v1/incidents/{id}/audit` | Audit trail and decisions |
| GET | `/api/v1/incidents/{id}/export` | Export bundle |
| GET | `/api/v1/gvps` | Zone counts + transparent priority score |
| GET | `/api/v1/analytics/summary` | Totals |

Interactive docs: `/docs` (FastAPI's built-in Swagger UI).

## Boundaries

- Draft only: no authentication, roles, signed evidence URLs, retention jobs,
  object storage, malware scanning or rate limiting. See
  [`docs/08_SECURITY_PRIVACY.md`](../docs/08_SECURITY_PRIVACY.md).
- Evidence frames are stored inside the incident payload as JPEG data URLs;
  there is no claim of hashes, chain of custody or legal admissibility.
- Human review remains mandatory; the API never issues a fine or an automatic
  enforcement action.
