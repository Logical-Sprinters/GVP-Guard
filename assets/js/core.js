// Pure, DOM-free logic. Importable by the browser and by `node --test`.
// Keeping business rules here makes the prototype testable without a browser.

export const STATUS = Object.freeze({
  CANDIDATE: 'CANDIDATE',
  SUSPICIOUS: 'SUSPICIOUS',
  REVIEW_REQUIRED: 'REVIEW_REQUIRED',
  APPROVED: 'APPROVED',
  REJECTED: 'REJECTED',
  CLEANUP_REQUESTED: 'CLEANUP_REQUESTED',
  CLEANUP_ASSIGNED: 'CLEANUP_ASSIGNED',
  CLOSED: 'CLOSED'
});

export const STATUS_LABEL = Object.freeze({
  [STATUS.CANDIDATE]: 'Candidate',
  [STATUS.SUSPICIOUS]: 'Suspicious',
  [STATUS.REVIEW_REQUIRED]: 'Review required',
  [STATUS.APPROVED]: 'Approved',
  [STATUS.REJECTED]: 'Rejected',
  [STATUS.CLEANUP_REQUESTED]: 'Cleanup requested',
  [STATUS.CLEANUP_ASSIGNED]: 'Cleanup assigned',
  [STATUS.CLOSED]: 'Closed'
});

export const PRIORITY_WEIGHTS = Object.freeze({
  frequency: 10,        // per incident at the zone
  repeat: 15,           // per repeat day at the same zone
  pendingCleanup: 8,    // per unresolved cleanup request
  isolation: 5          // fixed zone-isolation factor (illustrative)
});

export function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export function escapeHTML(value) {
  return String(value == null ? '' : value).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

/** Ray-casting point-in-polygon test. Polygon points are normalised [0..1]. */
export function pointInPolygon(point, polygon) {
  if (!Array.isArray(polygon) || polygon.length < 3) return false;
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x, yi = polygon[i].y;
    const xj = polygon[j].x, yj = polygon[j].y;
    const intersects = ((yi > point.y) !== (yj > point.y)) &&
      (point.x < ((xj - xi) * (point.y - yi)) / (yj - yi) + xi);
    if (intersects) inside = !inside;
  }
  return inside;
}

/** Reject malformed polygons and clamp coordinates into the visible frame. */
export function normalisePolygon(polygon, fallback) {
  if (!Array.isArray(polygon) || polygon.length < 3) return fallback.map(p => ({ ...p }));
  const clean = polygon
    .filter(p => p && Number.isFinite(p.x) && Number.isFinite(p.y))
    .map(p => ({ x: clamp(p.x, 0, 1), y: clamp(p.y, 0, 1) }));
  return clean.length >= 3 ? clean : fallback.map(p => ({ ...p }));
}

/**
 * Mean absolute RGB difference over sampled pixels, expressed as a 0..99
 * illustrative percentage. NOT a calibrated metric or a model score.
 * When `polygon` is supplied, only samples inside the GVP zone count.
 * Frames look like { data: Uint8ClampedArray, width, height }.
 */
export function sceneDifference(a, b, polygon = null) {
  if (!a || !b || !a.data || !b.data || a.width !== b.width || a.height !== b.height) return 0;
  const { width, height } = a;
  let sum = 0, n = 0;
  for (let i = 0; i < a.data.length; i += 16) { // every 4th pixel (RGBA stride 4)
    const pixel = i / 4;
    const x = pixel % width;
    const y = Math.floor(pixel / width);
    if (polygon && !pointInPolygon({ x: x / width, y: y / height }, polygon)) continue;
    sum += Math.abs(a.data[i] - b.data[i]) +
           Math.abs(a.data[i + 1] - b.data[i + 1]) +
           Math.abs(a.data[i + 2] - b.data[i + 2]);
    n += 3;
  }
  return n ? Math.min(99, (sum / n / 255) * 100 * 3.2) : 0;
}

/** Illustrative cue score derived from the same heuristic. Never present as model confidence. */
export function cueScore(diff) {
  return Math.min(0.94, 0.56 + (diff / 100) * 1.7);
}

export function classify(diff, threshold = 8) {
  const probable = diff >= threshold;
  return {
    probable,
    status: probable ? 'Probable dumping' : 'Ambiguous',
    triggerReasons: probable
      ? ['Zone scene change', 'Scene stabilised after change']
      : ['Limited zone scene change', 'Manual review required']
  };
}

let idSequence = 0;
/** Collision-resistant ID: timestamp + random + process sequence. */
export function makeIncidentId(now = Date.now(), rand = Math.random) {
  const stamp = new Date(now).toISOString().replace(/\D/g, '').slice(2, 14);
  const suffix = (Math.floor(rand() * 0xffff) ^ (idSequence++ & 0xffff))
    .toString(16).padStart(4, '0');
  return `INC-${stamp}-${suffix}`;
}

export function decisionToStatus(decision) {
  if (!decision) return STATUS.REVIEW_REQUIRED;
  if (decision.startsWith('Approved')) return STATUS.APPROVED;
  if (decision.startsWith('Rejected')) return STATUS.REJECTED;
  if (decision === 'Cleanup requested') return STATUS.CLEANUP_REQUESTED;
  return STATUS.REVIEW_REQUIRED;
}

/** Transparent, rule-based GVP priority score (0..100). Not a prediction model. */
export function priorityScore({ frequency = 0, repeat = 0, pendingCleanup = 0, isolation = 1 } = {}) {
  const w = PRIORITY_WEIGHTS;
  return Math.min(100, Math.round(
    frequency * w.frequency + repeat * w.repeat +
    pendingCleanup * w.pendingCleanup + isolation * w.isolation
  ));
}

/** Build the downloadable incident report. Frame data URLs are real captured images. */
export function buildReport(incident, now = new Date()) {
  return {
    ...incident,
    project: 'GVP-Guard: NightEye AI',
    problemCode: 'PS000048',
    teamId: 'TM004162',
    prototypeNotice: 'Controlled recorded-footage proof of concept. Human review required.',
    scoreNotice: 'Illustrative cue score is an uncalibrated pixel-difference heuristic, not a calibrated model confidence.',
    evidenceNotice: 'Evidence frames are JPEG data URLs captured from the source. No hashes, chain of custody or legal admissibility is claimed.',
    generatedAt: now.toISOString()
  };
}
