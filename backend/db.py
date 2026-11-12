"""Minimal SQLite persistence for the GVP-Guard prototype.

Only metadata is stored in the database; evidence frames travel inside the
incident payload as JPEG data URLs. No object storage or signed URLs yet —
see docs/07_DATABASE_SCHEMA.md and docs/08_SECURITY_PRIVACY.md.
"""
import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / 'data'
DB_PATH = DATA_DIR / 'gvp_guard.db'
_LOCK = threading.Lock()


def _now():
    return datetime.now(timezone.utc).isoformat()


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _LOCK, sqlite3.connect(DB_PATH) as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS incidents (
                id           TEXT PRIMARY KEY,
                payload      TEXT NOT NULL,
                status_code  TEXT,
                decision     TEXT,
                location     TEXT,
                occurred_at  TEXT,
                created_at   TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at DESC);
            CREATE TABLE IF NOT EXISTS decisions (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id    TEXT NOT NULL,
                reviewer       TEXT,
                decision       TEXT,
                comment        TEXT,
                reviewed_plate TEXT,
                created_at     TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cleanup_requests (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id    TEXT NOT NULL,
                status         TEXT NOT NULL DEFAULT 'requested',
                assigned_to    TEXT,
                requested_at   TEXT NOT NULL,
                completed_at   TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents(id)
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id     TEXT,
                entity_type  TEXT,
                entity_id    TEXT,
                action       TEXT,
                old_json     TEXT,
                new_json     TEXT,
                created_at   TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                username     TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role         TEXT NOT NULL DEFAULT 'officer',
                created_at   TEXT NOT NULL,
                is_active    INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS user_sessions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                token_hash   TEXT NOT NULL,
                expires_at   TEXT NOT NULL,
                created_at   TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
        ''')
        conn.commit()


@contextmanager
def connection():
    with _LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def _row_to_incident(row):
    return json.loads(row['payload'])


def list_incidents(status=None, location=None):
    query = 'SELECT payload FROM incidents'
    clauses, params = [], []
    if status:
        clauses.append('status_code = ?')
        params.append(status)
    if location:
        clauses.append('location = ?')
        params.append(location)
    if clauses:
        query += ' WHERE ' + ' AND '.join(clauses)
    query += ' ORDER BY created_at DESC, rowid DESC'
    with connection() as conn:
        return [_row_to_incident(row) for row in conn.execute(query, params)]


def get_incident(incident_id):
    with connection() as conn:
        row = conn.execute('SELECT payload FROM incidents WHERE id = ?', (incident_id,)).fetchone()
    return _row_to_incident(row) if row else None


def upsert_incident(payload):
    data = dict(payload)
    incident_id = data['id']
    record = {
        'id': incident_id,
        'payload': json.dumps(data),
        'status_code': data.get('statusCode') or 'REVIEW_REQUIRED',
        'decision': data.get('decision'),
        'location': data.get('location'),
        'occurred_at': data.get('time'),
        'created_at': _now()
    }
    with connection() as conn:
        old = conn.execute('SELECT payload FROM incidents WHERE id = ?', (incident_id,)).fetchone()
        conn.execute('''
            INSERT INTO incidents (id, payload, status_code, decision, location, occurred_at, created_at)
            VALUES (:id, :payload, :status_code, :decision, :location, :occurred_at, :created_at)
            ON CONFLICT(id) DO UPDATE SET
                payload = excluded.payload,
                status_code = excluded.status_code,
                decision = excluded.decision,
                location = excluded.location,
                occurred_at = excluded.occurred_at
        ''', record)
        add_audit(conn, actor=data.get('reviewer') or 'demo', entity_id=incident_id,
                  action='UPDATE' if old else 'CREATE',
                  old_json=old['payload'] if old else None,
                  new_json=record['payload'])
    return data


def patch_incident(incident_id, changes):
    current = get_incident(incident_id)
    if current is None:
        return None
    current.update(changes)
    current['id'] = incident_id
    return upsert_incident(current)


def delete_all_incidents():
    with connection() as conn:
        count = conn.execute('SELECT COUNT(*) FROM incidents').fetchone()[0]
        conn.execute('DELETE FROM incidents')
        conn.execute('DELETE FROM decisions')
        conn.execute('DELETE FROM cleanup_requests')
        add_audit(conn, actor='demo', entity_id='*', action='CLEAR',
                  old_json=json.dumps({'deleted': count}), new_json=None)


def add_decision(incident_id, decision, reviewer, comment, reviewed_plate):
    with connection() as conn:
        conn.execute('''
            INSERT INTO decisions (incident_id, reviewer, decision, comment, reviewed_plate, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (incident_id, reviewer, decision, comment, reviewed_plate, _now()))
        add_audit(conn, actor=reviewer or 'demo', entity_id=incident_id, action='DECISION',
                  old_json=None, new_json=json.dumps({'decision': decision, 'comment': comment}))


def add_audit(conn, actor, entity_id, action, old_json, new_json):
    conn.execute('''
        INSERT INTO audit_events (actor_id, entity_type, entity_id, action, old_json, new_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (actor, 'incident', entity_id, action, old_json, new_json, _now()))


def get_audit(incident_id):
    with connection() as conn:
        rows = conn.execute('''
            SELECT id, actor_id, entity_type, entity_id, action, old_json, new_json, created_at
            FROM audit_events WHERE entity_id = ? ORDER BY id
        ''', (incident_id,)).fetchall()
    return [dict(row) for row in rows]


def get_decisions(incident_id):
    with connection() as conn:
        rows = conn.execute('''
            SELECT id, incident_id, reviewer, decision, comment, reviewed_plate, created_at
            FROM decisions WHERE incident_id = ? ORDER BY id
        ''', (incident_id,)).fetchall()
    return [dict(row) for row in rows]


def add_cleanup_request(incident_id, assigned_to=None):
    """Create a cleanup request for an incident. Returns the new row dict."""
    with connection() as conn:
        incident = conn.execute('SELECT id FROM incidents WHERE id = ?', (incident_id,)).fetchone()
        if incident is None:
            return None
        now = _now()
        cur = conn.execute('''\n            INSERT INTO cleanup_requests (incident_id, status, assigned_to, requested_at, completed_at)\n            VALUES (?, ?, ?, ?, NULL)\n        ''', (incident_id, 'requested', assigned_to, now))
        conn.execute('''\n            INSERT INTO audit_events (actor_id, entity_type, entity_id, action, old_json, new_json, created_at)\n            VALUES (?, ?, ?, ?, ?, ?, ?)\n        ''', ('demo', 'incident', incident_id, 'CLEANUP_REQUESTED', None,
               json.dumps({'assigned_to': assigned_to}), now))
        row = conn.execute('SELECT * FROM cleanup_requests WHERE id = ?', (cur.lastrowid,)).fetchone()
    return dict(row)


def get_cleanup_request(cleanup_id):
    with connection() as conn:
        row = conn.execute('SELECT * FROM cleanup_requests WHERE id = ?', (cleanup_id,)).fetchone()
    return dict(row) if row else None


def get_cleanup_requests(incident_id=None):
    query = 'SELECT * FROM cleanup_requests'
    params = []
    if incident_id is not None:
        query += ' WHERE incident_id = ?'
        params.append(incident_id)
    query += ' ORDER BY id DESC'
    with connection() as conn:
        return [dict(row) for row in conn.execute(query, params)]


def update_cleanup_request(cleanup_id, changes):
    with connection() as conn:
        row = conn.execute('SELECT * FROM cleanup_requests WHERE id = ?', (cleanup_id,)).fetchone()
        if row is None:
            return None
        current = dict(row)
        current.update(changes)
        if current.get('status') == 'completed' and not current.get('completed_at'):
            current['completed_at'] = _now()
        conn.execute('''\n            UPDATE cleanup_requests\n            SET status = ?, assigned_to = ?, completed_at = ?\n            WHERE id = ?\n        ''', (current['status'], current.get('assigned_to'), current.get('completed_at'), cleanup_id))
        conn.execute('''\n            INSERT INTO audit_events (actor_id, entity_type, entity_id, action, old_json, new_json, created_at)\n            VALUES (?, ?, ?, ?, ?, ?, ?)\n        ''', ('demo', 'cleanup_request', str(cleanup_id), 'UPDATE',
               json.dumps({k: current.get(k) for k in ('status', 'assigned_to', 'completed_at') if k != 'completed_at' or current.get('completed_at')}),
               json.dumps({k: current.get(k) for k in ('status', 'assigned_to', 'completed_at')}), _now()))
        return current


def delete_all_cleanup_requests():
    with connection() as conn:
        count = conn.execute('SELECT COUNT(*) FROM cleanup_requests').fetchone()[0]
        conn.execute('DELETE FROM cleanup_requests')
    return count


def priority_score(frequency, repeat, pending_cleanup, isolation=1):
    """Transparent rule-based score, identical weights to assets/js/core.js."""
    return min(100, round(frequency * 10 + repeat * 15 + pending_cleanup * 8 + isolation * 5))


def gvps():
    zones = {}
    for incident in list_incidents():
        zone = incident.get('location') or 'Unassigned'
        entry = zones.setdefault(zone, {'id': zone, 'name': zone, 'incidentCount': 0,
                                       'days': set(), 'pendingCleanup': 0})
        entry['incidentCount'] += 1
        entry['days'].add(str(incident.get('time') or '')[:10])
        if incident.get('decision') == 'Cleanup requested':
            entry['pendingCleanup'] += 1
    result = []
    for entry in zones.values():
        result.append({
            'id': entry['id'],
            'name': entry['name'],
            'incidentCount': entry['incidentCount'],
            'pendingCleanup': entry['pendingCleanup'],
            'priorityScore': priority_score(entry['incidentCount'], len(entry['days']),
                                            entry['pendingCleanup'])
        })
    return sorted(result, key=lambda x: (-x['priorityScore'], x['id']))


def summary():
    records = list_incidents()
    return {
        'totalIncidents': len(records),
        'approved': sum(1 for r in records if (r.get('decision') or '').startswith('Approved')),
        'cleanupRequested': sum(1 for r in records if r.get('decision') == 'Cleanup requested'),
        'demoRecords': sum(1 for r in records if r.get('demo')),
        'zones': len(gvps()),
        'generatedAt': _now()
    }


# ============================================================================
# User & Session CRUD
# ============================================================================

def create_user(username: str, password_hash: str, role: str = "officer") -> int | None:
    """Create a new user. Returns user id or None if username exists."""
    with connection() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (username, password_hash, role, _now()),
            )
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None


def get_user_by_username(username: str) -> dict | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, created_at, is_active FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role, created_at, is_active FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def authenticate_user(username: str, password: str) -> dict | None:
    """Verify username/password. Returns user dict without password_hash if valid."""
    user = get_user_by_username(username)
    if not user or not user.get("is_active"):
        return None
    import hashlib
    expected_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if user["password_hash"] != expected_hash:
        return None
    return {k: v for k, v in user.items() if k != "password_hash"}


def create_session(user_id: int, token_hash: str, expires_at: str) -> int:
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO user_sessions (user_id, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (user_id, token_hash, expires_at, _now()),
        )
        return cur.lastrowid


def get_session(token_hash: str) -> dict | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT id, user_id, token_hash, expires_at, created_at FROM user_sessions WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
    return dict(row) if row else None


def delete_session(token_hash: str) -> bool:
    with connection() as conn:
        cur = conn.execute(
            "DELETE FROM user_sessions WHERE token_hash = ?",
            (token_hash,),
        )
        return cur.rowcount > 0


def delete_expired_sessions() -> int:
    with connection() as conn:
        cur = conn.execute(
            "DELETE FROM user_sessions WHERE expires_at < ?",
            (_now(),),
        )
        return cur.rowcount


def list_users() -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at, is_active FROM users ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def update_user_role(user_id: int, role: str) -> dict | None:
    with connection() as conn:
        conn.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (role, user_id),
        )
        return get_user_by_id(user_id)


def deactivate_user(user_id: int) -> bool:
    with connection() as conn:
        cur = conn.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?",
            (user_id,),
        )
        return cur.rowcount > 0
