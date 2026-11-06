import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
// jsdom's Performance delegates to the global `performance`; keep Node's native
// implementation to avoid infinite recursion when multiple JSDOMs are created.
const NODE_PERFORMANCE = globalThis.performance;

function stubCanvas(window) {
  window.HTMLCanvasElement.prototype.getContext = () => ({
    clearRect() {}, drawImage() {}, putImageData() {}, beginPath() {},
    moveTo() {}, lineTo() {}, closePath() {}, fill() {}, stroke() {},
    setLineDash() {}, arc() {},
    getImageData(x, y, w, h) {
      return { data: new Uint8ClampedArray(w * h * 4), width: w, height: h };
    }
  });
  window.HTMLCanvasElement.prototype.toDataURL = () => 'data:image/jpeg;base64,AAAA';
  window.HTMLMediaElement.prototype.pause = () => {};
  window.HTMLMediaElement.prototype.play = async () => {};
  window.URL.createObjectURL = () => 'blob:fake';
  window.URL.revokeObjectURL = () => {};
}

function installGlobals(window) {
  window.fetch = async () => ({ ok: false, status: 404, json: async () => ({}) });
  window.requestAnimationFrame = cb => setTimeout(cb, 0);
  window.navigator.mediaDevices = { getUserMedia: async () => { throw new Error('no camera in test'); } };
  // Node 22 exposes some globals as getter-only, so define them explicitly.
  const setGlobal = (name, value) => Object.defineProperty(
    globalThis, name, { value, writable: true, configurable: true }
  );
  setGlobal('window', window);
  setGlobal('document', window.document);
  setGlobal('navigator', window.navigator);
  setGlobal('performance', NODE_PERFORMANCE);
  setGlobal('requestAnimationFrame', window.requestAnimationFrame);
  setGlobal('URL', window.URL);
  setGlobal('localStorage', window.localStorage);
  setGlobal('fetch', window.fetch);
  setGlobal('Blob', window.Blob);
  setGlobal('HTMLElement', window.HTMLElement);
  setGlobal('HTMLCanvasElement', window.HTMLCanvasElement);
}

const tick = () => new Promise(resolve => setTimeout(resolve, 60));

test('static prototype boots, wires tabs, and keeps claim discipline', async () => {
  const dom = new JSDOM(html, { url: 'http://localhost:8000/', pretendToBeVisual: true });
  const { window } = dom;
  stubCanvas(window);
  installGlobals(window);
  const $ = id => window.document.getElementById(id);

  await import('../assets/js/app.js');
  await tick();

  assert.equal($('storageMode').textContent, 'Local browser storage');
  assert.equal($('histTotal').textContent, '0');
  assert.match($('monitorState').textContent, /heuristic/);
  assert.match($('zoneInfo').textContent, /points/);
  assert.match($('persistenceStatus').textContent, /LOCAL/);
  assert.match($('apiStatus').textContent, /offline mode/);

  // Tabs
  window.document.querySelector('.tab[data-view="history"]').click();
  assert.ok($('view-history').classList.contains('active'));
  assert.ok(!$('view-live').classList.contains('active'));

  // Seeded sample records are clearly labelled
  $('seedHistory').click();
  await tick();
  assert.equal($('histTotal').textContent, '3');
  assert.match($('histBody').innerHTML, /DEMO/);
  assert.match($('histNote').textContent, /illustrative only/);

  // XSS through a stored plate value is neutralised
  window.localStorage.setItem('gvpHistory', JSON.stringify([{
    id: 'INC-XSS', time: 't', location: 'GVP-01', sceneChange: '1%',
    plate: '<img src=x onerror=alert(1)>', decision: 'Approved for follow-up',
    status: 'SUSPICIOUS', statusCode: 'APPROVED'
  }]));
  window.document.querySelector('.tab[data-view="live"]').click();
  window.document.querySelector('.tab[data-view="history"]').click();
  await tick();
  assert.ok(!/<img/i.test($('histBody').innerHTML));
  assert.ok($('histBody').textContent.includes('<img src=x onerror=alert(1)>'));

  $('clearHistory').click();
  await tick();
  assert.equal($('histTotal').textContent, '0');

  // Map derives counts and a transparent score from records
  window.localStorage.setItem('gvpHistory', JSON.stringify([
    { id: 'A', location: 'GVP-02', decision: 'Cleanup requested', time: '2026-11-01', statusCode: 'CLEANUP_REQUESTED' },
    { id: 'B', location: 'GVP-02', decision: 'Pending', time: '2026-11-02', statusCode: 'REVIEW_REQUIRED' }
  ]));
  window.document.querySelector('.tab[data-view="map"]').click();
  await tick();
  window.document.querySelector('.pin[data-zone="GVP-02"]').click();
  assert.equal($('zoneName').textContent, 'GVP-02');
  assert.equal($('zoneCount').textContent, '2');
  assert.ok(Number($('zoneScore').textContent) > 0);

  // Zone editor and status codes exist
  $('editZone').click();
  assert.equal($('editZone').textContent, 'Finish editing');
  assert.equal($('saveZone').disabled, false);
  assert.equal($('statusCode').textContent, '—');

  dom.window.close();
});

test('index.html is self-contained and points at real assets', () => {
  assert.ok(!/https?:\/\//.test(html.replace(/<!--[\s\S]*?-->/g, '')), 'no external URLs');
  const refs = [...html.matchAll(/(?:src|href)="(assets\/[^"]+)"/g)].map(m => m[1]);
  assert.ok(refs.length >= 2, 'CSS and JS are linked');
  for (const ref of refs) {
    assert.ok(fs.existsSync(path.join(ROOT, ref)), `${ref} exists`);
  }
  assert.match(html, /type="module"/);
});

test('API mode is detected via relative /api/v1 calls', async () => {
  const dom = new JSDOM(html, { url: 'http://localhost:8000/', pretendToBeVisual: true });
  const { window } = dom;
  stubCanvas(window);
  installGlobals(window);

  const records = [{
    id: 'INC-API-1', time: '2026-11-05', location: 'GVP-03', sceneChange: '9.0%',
    plate: 'Manual review', decision: 'Pending', status: 'SUSPICIOUS',
    statusCode: 'REVIEW_REQUIRED'
  }];
  window.fetch = async (url, options = {}) => {
    const method = options.method || 'GET';
    if (url.endsWith('/health')) return { ok: true, json: async () => ({ ok: true }) };
    if (url.endsWith('/incidents') && method === 'GET') {
      return { ok: true, json: async () => ({ items: records, count: records.length }) };
    }
    return { ok: true, json: async () => ({ ok: true }) };
  };
  Object.defineProperty(globalThis, 'fetch', { value: window.fetch, writable: true, configurable: true });

  const $ = id => window.document.getElementById(id);
  await import('../assets/js/app.js?api=1');
  await tick();

  assert.equal($('storageMode').textContent, 'API persistence (SQLite)');
  assert.equal($('persistenceStatus').textContent, 'API');
  assert.match($('apiStatus').textContent, /detected/);
  assert.equal($('histTotal').textContent, '1');
  window.document.querySelector('.tab[data-view="map"]').click();
  await tick();
  assert.equal($('mapSource').textContent, 'API (SQLite)');
  dom.window.close();
});
