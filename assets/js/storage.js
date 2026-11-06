import { CONFIG } from './config.js';

/**
 * Dual-mode persistence. Default is browser localStorage (fully offline).
 * When the optional FastAPI backend is reachable on the same origin, records are
 * mirrored to `/api/v1` using relative URLs (no CORS, no localhost calls).
 * If the API is unavailable, the app silently keeps working locally.
 */
export function createStorage(apiBase = CONFIG.apiBase) {
  let remote = false;

  async function check() {
    try {
      const response = await fetch(`${apiBase}/health`, { headers: { Accept: 'application/json' } });
      if (response.ok) {
        const body = await response.json();
        remote = Boolean(body && body.ok);
      } else remote = false;
    } catch { remote = false; }
    return remote;
  }

  function localList() {
    try {
      const value = JSON.parse(window.localStorage.getItem(CONFIG.storageKey) || '[]');
      return Array.isArray(value) ? value : [];
    } catch { return []; }
  }

  function localWrite(records) {
    window.localStorage.setItem(CONFIG.storageKey, JSON.stringify(records.slice(0, 100)));
  }

  async function load() {
    if (remote) {
      try {
        const response = await fetch(`${apiBase}/incidents`);
        if (response.ok) {
          const body = await response.json();
          const items = Array.isArray(body) ? body : body.items;
          if (Array.isArray(items)) return items;
        }
      } catch { /* fall through to local cache */ }
    }
    return localList();
  }

  async function upsert(incident) {
    if (remote) {
      try {
        await fetch(`${apiBase}/incidents`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(incident)
        });
      } catch { /* local cache below still succeeds */ }
    }
    const records = localList();
    const index = records.findIndex(x => x.id === incident.id);
    if (index >= 0) records[index] = incident; else records.unshift(incident);
    localWrite(records);
    return records;
  }

  async function recordDecision(id, payload) {
    if (!remote) return;
    try {
      await fetch(`${apiBase}/incidents/${encodeURIComponent(id)}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch { /* audit is best-effort in the prototype */ }
  }

  async function requestCleanup(incidentId, assignedTo) {
    if (!remote) return null;
    try {
      const response = await fetch(`${apiBase}/incidents/${encodeURIComponent(incidentId)}/cleanup-request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assigned_to: assignedTo || null })
      });
      if (response.ok) return await response.json();
    } catch { /* best-effort */ }
    return null;
  }

  async function updateCleanupRequest(cleanupId, changes) {
    if (!remote) return null;
    try {
      const response = await fetch(`${apiBase}/cleanup-requests/${cleanupId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(changes)
      });
      if (response.ok) return await response.json();
    } catch { /* best-effort */ }
    return null;
  }

  async function loadCleanupRequests(incidentId) {
    if (!remote) return [];
    try {
      const response = await fetch(`${apiBase}/incidents/${encodeURIComponent(incidentId)}/cleanup-request`);
      if (response.ok) {
        const body = await response.json();
        return Array.isArray(body.items) ? body.items : [];
      }
    } catch { /* best-effort */ }
    return [];
  }

  async function seed(records) {
    if (remote) {
      for (const record of records) {
        try {
          await fetch(`${apiBase}/incidents`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(record)
          });
        } catch { /* ignore */ }
      }
    }
    localWrite(records);
  }

  async function clear() {
    if (remote) {
      try { await fetch(`${apiBase}/incidents`, { method: 'DELETE' }); } catch { /* ignore */ }
    }
    window.localStorage.removeItem(CONFIG.storageKey);
  }

  return { check, load, upsert, recordDecision, requestCleanup, updateCleanupRequest,
    loadCleanupRequests, seed, clear, isRemote: () => remote };
}
