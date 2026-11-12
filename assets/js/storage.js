import { CONFIG } from './config.js';
import { fetchWithAuth } from './auth.js';

/**
 * Dual-mode persistence. Default is browser localStorage (fully offline).
 * When the optional FastAPI backend is reachable on the same origin, records are
 * mirrored to `/api/v1` using relative URLs (no CORS, no localhost calls).
 * If the API is unavailable, the app silently keeps working locally.
 * Write operations use fetchWithAuth to attach the JWT bearer token when
 * authenticated; unauthenticated API writes will trigger a session redirect.
 *
 * Evidence frames are stored in object storage (separate files with SHA-256
 * checksums and signed, time-limited URLs) rather than embedded as data URLs
 * in the incident payload.
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

  /**
   * Strip evidenceFrames before sending to the API — evidence is uploaded
   * separately via uploadEvidence() to object storage.
   */
  function _stripEvidenceFrames(incident) {
    const { evidenceFrames, ...rest } = incident;
    return rest;
  }

  async function upsert(incident) {
    if (remote) {
      try {
        await fetchWithAuth(`${apiBase}/incidents`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(_stripEvidenceFrames(incident))
        });
      } catch { /* local cache below still succeeds */ }
    }
    const records = localList();
    const index = records.findIndex(x => x.id === incident.id);
    if (index >= 0) records[index] = incident; else records.unshift(incident);
    localWrite(records);
    return records;
  }

  /**
   * Upload an evidence frame (base64 data URL) to object storage.
   * Returns the evidence item with storage_key and signed_url.
   */
  async function uploadEvidence(incidentId, kind, dataUrl, mimeType = 'image/jpeg', capturedAt = null) {
    if (!remote) return null;
    try {
      // Extract base64 payload from data URL
      let b64 = dataUrl;
      if (dataUrl.startsWith('data:')) {
        b64 = dataUrl.split(',', 2)[1] || dataUrl;
      }
      const response = await fetchWithAuth(`${apiBase}/incidents/${encodeURIComponent(incidentId)}/evidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: incidentId,
          kind,
          storage_key: b64,
          mime_type: mimeType,
          captured_at: capturedAt,
        }),
      });
      if (response.ok) return await response.json();
    } catch { /* best-effort */ }
    return null;
  }

  async function recordDecision(id, payload) {
    if (!remote) return;
    try {
      await fetchWithAuth(`${apiBase}/incidents/${encodeURIComponent(id)}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch { /* audit is best-effort in the prototype */ }
  }

  async function requestCleanup(incidentId, assignedTo) {
    if (!remote) return null;
    try {
      const response = await fetchWithAuth(`${apiBase}/incidents/${encodeURIComponent(incidentId)}/cleanup-request`, {
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
      const response = await fetchWithAuth(`${apiBase}/cleanup-requests/${cleanupId}`, {
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

  /**
   * List evidence items for an incident, each with a signed, time-limited URL.
   */
  async function getEvidence(incidentId) {
    if (!remote) return null;
    try {
      const response = await fetch(`${apiBase}/incidents/${encodeURIComponent(incidentId)}/evidence`);
      if (response.ok) return await response.json();
    } catch { /* best-effort */ }
    return null;
  }

  /**
   * Get a signed URL for an evidence storage key.
   */
  async function getEvidenceSignedUrl(storageKey) {
    if (!remote) return null;
    try {
      const response = await fetch(`${apiBase}/evidence/${encodeURIComponent(storageKey)}`);
      if (response.ok) return await response.json();
    } catch { /* best-effort */ }
    return null;
  }

  /**
   * Download an evidence file using a signed URL token.
   * Returns a Blob or null.
   */
  async function downloadEvidence(incidentId, frame) {
    if (!remote) return null;
    try {
      // First, get the evidence list to find the storage_key for this frame kind
      const evidence = await getEvidence(incidentId);
      if (!evidence || !evidence.items) return null;
      const item = evidence.items.find(i => i.kind === frame);
      if (!item) return null;

      // Get a signed URL for this storage key
      const signed = await getEvidenceSignedUrl(item.storage_key);
      if (!signed || !signed.signed_url) return null;

      // Download using the signed URL token
      const response = await fetch(
        `${apiBase}/evidence/${encodeURIComponent(item.storage_key)}/download?token=${encodeURIComponent(signed.signed_url)}`
      );
      if (response.ok) return await response.blob();
    } catch { /* best-effort */ }
    return null;
  }

  /**
   * Verify an evidence file's SHA-256 checksum.
   */
  async function verifyChecksum(storageKey) {
    if (!remote) return null;
    try {
      const response = await fetch(`${apiBase}/evidence/${encodeURIComponent(storageKey)}/checksum`);
      if (response.ok) return await response.json();
    } catch { /* best-effort */ }
    return null;
  }

  async function seed(records) {
    if (remote) {
      for (const record of records) {
        try {
          await fetchWithAuth(`${apiBase}/incidents`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(_stripEvidenceFrames(record))
          });
        } catch { /* ignore */ }
      }
    }
    localWrite(records);
  }

  async function clear() {
    if (remote) {
      try { await fetchWithAuth(`${apiBase}/incidents`, { method: 'DELETE' }); } catch { /* ignore */ }
    }
    window.localStorage.removeItem(CONFIG.storageKey);
  }

  return { check, load, upsert, uploadEvidence, recordDecision, requestCleanup, updateCleanupRequest,
    loadCleanupRequests, getEvidence, getEvidenceSignedUrl, downloadEvidence, verifyChecksum,
    seed, clear, isRemote: () => remote };
}
