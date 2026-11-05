import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  STATUS, escapeHTML, pointInPolygon, normalisePolygon, sceneDifference,
  cueScore, classify, makeIncidentId, decisionToStatus, priorityScore, buildReport
} from '../assets/js/core.js';

const RECT = [
  { x: 0.17, y: 0.48 }, { x: 0.90, y: 0.48 },
  { x: 0.90, y: 0.86 }, { x: 0.17, y: 0.86 }
];

function makeFrame(width, height, value) {
  const data = new Uint8ClampedArray(width * height * 4);
  for (let i = 0; i < data.length; i += 4) {
    data[i] = value; data[i + 1] = value; data[i + 2] = value; data[i + 3] = 255;
  }
  return { data, width, height };
}

test('escapeHTML neutralises injection payloads', () => {
  assert.equal(escapeHTML('<img onerror="x">'), '&lt;img onerror=&quot;x&quot;&gt;');
  assert.equal(escapeHTML(null), '');
  assert.equal(escapeHTML(42), '42');
});

test('pointInPolygon uses ray casting', () => {
  assert.equal(pointInPolygon({ x: 0.5, y: 0.6 }, RECT), true);
  assert.equal(pointInPolygon({ x: 0.05, y: 0.05 }, RECT), false);
  assert.equal(pointInPolygon({ x: 0.5, y: 0.5 }, []), false);
});

test('normalisePolygon rejects malformed input and clamps coordinates', () => {
  assert.equal(normalisePolygon(null, RECT).length, 4);
  assert.equal(normalisePolygon([{ x: 1.4, y: -2 }], RECT).length, 4);
  const clean = normalisePolygon([{ x: 2, y: 3 }, { x: 0, y: 0 }, { x: 1, y: 1 }], RECT);
  assert.deepEqual(clean[0], { x: 1, y: 1 });
});

test('sceneDifference is zero for identical frames and positive for changed frames', () => {
  const a = makeFrame(40, 20, 20);
  assert.equal(sceneDifference(a, makeFrame(40, 20, 20)), 0);
  assert.ok(sceneDifference(a, makeFrame(40, 20, 200)) > 0);
  assert.equal(sceneDifference(a, { data: a.data, width: 41, height: 20 }), 0);
});

test('sceneDifference ignores changes outside the GVP polygon', () => {
  const base = makeFrame(40, 20, 20);
  const outside = makeFrame(40, 20, 20);
  const pixel = 4; // x=4/40=0.10, y=0 → outside the default rectangle
  outside.data[pixel * 4] = 250;
  outside.data[pixel * 4 + 1] = 250;
  outside.data[pixel * 4 + 2] = 250;
  assert.ok(sceneDifference(base, outside) > 0, 'whole-frame change is visible');
  assert.equal(sceneDifference(base, outside, RECT), 0, 'zone-limited change is ignored');
});

test('cueScore is bounded and never negative', () => {
  assert.equal(cueScore(0), 0.56);
  assert.equal(cueScore(100), 0.94);
  assert.ok(cueScore(30) > cueScore(10));
});

test('classify applies the documented heuristic threshold', () => {
  assert.equal(classify(8, 8).status, 'Probable dumping');
  assert.equal(classify(7.9, 8).status, 'Ambiguous');
  assert.deepEqual(classify(8, 8).triggerReasons.length, 2);
});

test('makeIncidentId has a stable format and does not collide', () => {
  const ids = new Set();
  for (let i = 0; i < 200; i++) ids.add(makeIncidentId(1700000000000, () => 0.5));
  assert.equal(ids.size, 200);
  assert.match([...ids][0], /^INC-\d{12}-[0-9a-f]{4}$/);
});

test('decisionToStatus maps officer actions to the canonical enum', () => {
  assert.equal(decisionToStatus('Approved for follow-up'), STATUS.APPROVED);
  assert.equal(decisionToStatus('Rejected — insufficient evidence'), STATUS.REJECTED);
  assert.equal(decisionToStatus('Cleanup requested'), STATUS.CLEANUP_REQUESTED);
  assert.equal(decisionToStatus('Pending'), STATUS.REVIEW_REQUIRED);
});

test('priorityScore is transparent, monotone and capped at 100', () => {
  assert.equal(priorityScore(), 5);
  assert.ok(priorityScore({ frequency: 2 }) > priorityScore({ frequency: 1 }));
  assert.equal(priorityScore({ frequency: 100 }), 100);
});

test('buildReport keeps the honesty notices and the incident fields', () => {
  const report = buildReport({ id: 'INC-1', plate: 'GJ 05 XX 0001' }, new Date('2026-11-05T00:00:00Z'));
  assert.equal(report.problemCode, 'PS000048');
  assert.equal(report.id, 'INC-1');
  assert.match(report.scoreNotice, /uncalibrated/);
  assert.match(report.evidenceNotice, /chain of custody/);
  assert.equal(report.generatedAt, '2026-11-05T00:00:00.000Z');
});
