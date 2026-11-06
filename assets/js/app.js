import { CONFIG } from './config.js';
import {
  STATUS, STATUS_LABEL, escapeHTML, clamp, normalisePolygon, sceneDifference,
  cueScore, classify, makeIncidentId, decisionToStatus, priorityScore, buildReport
} from './core.js';
import { createCamera } from './camera.js';
import { createZoneEditor } from './zone.js';
import { createEvidenceBuffer, paintFrame, clearCanvas } from './evidence.js';
import { createMonitor } from './monitor.js';
import { createStorage } from './storage.js';

const $ = id => document.getElementById(id);
const video = $('vid');
const stage = $('stage');

function loadPolygon() {
  try {
    return normalisePolygon(
      JSON.parse(window.localStorage.getItem(CONFIG.zoneKey) || 'null'),
      CONFIG.defaultPolygon
    );
  } catch { return CONFIG.defaultPolygon.map(p => ({ ...p })); }
}

const state = {
  polygon: loadPolygon(),
  history: [],
  incident: null,
  filename: 'No video selected',
  mapZone: 'GVP-01',
  mapRisk: 'High'
};

const camera = createCamera(video);
const evidence = createEvidenceBuffer(CONFIG.monitor.bufferSize);
const storage = createStorage();

const zoneEditor = createZoneEditor({
  stage, canvas: $('zoneCanvas'),
  getPolygon: () => state.polygon,
  setPolygon: polygon => { state.polygon = normalisePolygon(polygon, CONFIG.defaultPolygon); },
  onChange: () => { $('zoneInfo').textContent = `${state.polygon.length} points • edited`; }
});

/* ------------------------------- UI helpers ------------------------------- */

function setStep(n, percent) {
  $('s' + n).classList.add('on');
  $('bar').style.width = percent + '%';
}

function clearSteps() {
  [1, 2, 3, 4, 5].forEach(n => $('s' + n).classList.remove('on'));
  $('bar').style.width = '0';
}

function showVideo() {
  video.style.display = 'block';
  $('empty').style.display = 'none';
  requestAnimationFrame(() => { zoneEditor.sizeCanvas(); zoneEditor.draw(); });
}

function resetIncidentUI(clearSource) {
  clearSteps();
  $('track').style.display = 'none';
  ['score', 'change', 'pstat', 'iid', 'time', 'decision', 'statusCode']
    .forEach(id => { $(id).textContent = '—'; });
  $('istatus').textContent = 'WAITING';
  $('plate').textContent = 'Pending';
  $('confidence').textContent = 'Awaiting analysis';
  $('plateEdit').value = '';
  $('comment').value = '';
  $('alert').innerHTML = '<strong>No incident generated</strong><div style="font-size:12px;margin-top:4px;color:#6c625b">Run analysis or monitoring after setting a source and zone.</div>';
  ['c1', 'c2', 'c3'].forEach(id => clearCanvas($(id)));
  $('location').textContent = $('zoneSelect').value;
  $('note').textContent = 'Human review is mandatory before any enforcement action.';
  state.incident = null;
  state.cleanup = { id: null, status: null, assignee: null, requestedAt: null };
  $('cleanupSection').style.display = 'none';

  if (clearSource) {
    monitor.stop();
    camera.clear();
    video.style.display = 'none';
    $('empty').style.display = 'block';
    $('file').value = '';
    $('filename').textContent = 'No video selected';
    state.filename = 'No video selected';
    $('camera').textContent = 'CAM-DEMO-01';
    $('stopWebcam').disabled = true;
    updateMonitorUI();
    $('monitorState').textContent = 'Idle • scene-stability heuristic, not vehicle tracking';
  }
}

function getStableSeconds() {
  return clamp(parseFloat($('stableSeconds').value) || CONFIG.monitor.defaultStableSeconds, 0.5, 30);
}

/* ----------------------------- Incident record ---------------------------- */

function createIncident({ diff, frames, source, stableFor = null }) {
  const score = cueScore(diff);
  const result = classify(diff, CONFIG.analysis.threshold);
  const zone = $('zoneSelect').value;
  const vehicleMode = $('scenario').value === 'vehicle';

  const incident = {
    id: makeIncidentId(),
    time: new Date().toLocaleString(),
    file: state.filename,
    sceneChange: diff.toFixed(1) + '%',
    illustrativeCueScore: score.toFixed(2),
    plate: $('plateEdit').value.trim() || 'Manual review pending',
    decision: 'Pending',
    location: zone,
    status: result.status,
    statusCode: STATUS.REVIEW_REQUIRED,
    triggerReasons: result.triggerReasons,
    detectionMethod: 'Zone-limited pixel difference (heuristic)',
    source,
    stableFor,
    evidenceFrames: frames ? {
      before: frames.before?.dataUrl || null,
      during: frames.during?.dataUrl || null,
      after: frames.after?.dataUrl || null
    } : null,
    reviewer: $('reviewer').value.trim() || 'Demo officer',
    comment: '',
    demo: false
  };
  state.incident = incident;

  $('change').textContent = diff.toFixed(1) + '%';
  $('score').textContent = score.toFixed(2);
  $('pstat').textContent = vehicleMode ? 'Manual review' : 'N/A';
  $('confidence').textContent = vehicleMode
    ? 'ANPR is demo-stage • enter plate after visual review'
    : 'Person/object event • no vehicle plate expected';
  $('iid').textContent = incident.id;
  $('time').textContent = incident.time;
  $('location').textContent = zone;
  $('decision').textContent = 'Pending';
  $('statusCode').textContent = incident.statusCode;
  $('istatus').textContent = STATUS_LABEL[STATUS.REVIEW_REQUIRED];
  $('plate').textContent = incident.plate;
  $('alert').innerHTML = '<strong>' + STATUS_LABEL[result.status] + ' event</strong><div style="font-size:12px;margin-top:4px;color:#6c625b">Zone scene change detected by a heuristic. Officer confirmation required.</div>';
  $('track').style.display = 'block';
  $('trackLabel').textContent = source === 'Recorded video analysis'
    ? 'Zone scene-change overlay (heuristic)'
    : 'Live monitoring • heuristic cue';

  if (frames) {
    paintFrame($('c1'), frames.before);
    paintFrame($('c2'), frames.during);
    paintFrame($('c3'), frames.after);
  }
  // Persist pending incidents too; the earlier demo only saved after a decision.
  storage.upsert(incident).then(async () => {
    await refreshHistory();
    await loadCleanupSection();
  }).catch(() => {});
}

async function runAnalysis() {
  if (camera.mode === 'none') { alert('Choose a recorded video or start the webcam first.'); return; }
  if (camera.mode === 'webcam') {
    $('note').textContent = 'Live input uses scene-stability monitoring. Click Start monitoring instead.';
    return;
  }
  if (!isFinite(camera.duration) || camera.duration < 2) {
    alert('Wait until the video finishes loading, then try again.');
    return;
  }
  resetIncidentUI(false);
  $('istatus').textContent = 'ANALYSING';
  $('note').textContent = 'Extracting zone-limited evidence frames…';
  video.pause();
  setStep(1, 15);
  zoneEditor.draw();
  setStep(2, 35);
  const d = camera.duration;
  await camera.seekTo(d * 0.10); const before = camera.grabFrame();
  setStep(3, 55);
  await camera.seekTo(d * 0.52); const during = camera.grabFrame();
  await camera.seekTo(d * 0.90); const after = camera.grabFrame();
  setStep(4, 80);
  const diff = sceneDifference(before, after, state.polygon);
  createIncident({ diff, frames: { before, during, after }, source: 'Recorded video analysis' });
  setStep(5, 100);
  $('note').textContent = 'Analysis complete. Review all evidence before choosing an action.';
  try { video.currentTime = 0; } catch { /* ignore */ }
}

async function decide(action) {
  if (!state.incident) {
    $('note').textContent = 'Run analysis or monitoring before recording a decision.';
    return;
  }
  const incident = state.incident;
  incident.plate = $('plateEdit').value.trim() || incident.plate;
  incident.decision = action;
  incident.statusCode = decisionToStatus(action);
  incident.reviewer = $('reviewer').value.trim() || 'Demo officer';
  incident.comment = $('comment').value.trim();
  incident.reviewedAt = new Date().toISOString();

  $('plate').textContent = incident.plate;
  $('decision').textContent = action;
  $('statusCode').textContent = incident.statusCode;
  $('istatus').textContent = STATUS_LABEL[incident.statusCode];
  $('note').textContent = `${action} • recorded for ${incident.reviewer}. Review-ready incident saved.`;

  await storage.upsert(incident);
  await storage.recordDecision(incident.id, {
    decision: action, reviewer: incident.reviewer,
    comment: incident.comment, reviewedPlate: incident.plate
  });
  await refreshHistory();
  await loadCleanupSection();
}

/* --------------------------- Cleanup Request --------------------------- */

state.cleanup = { id: null, status: null, assignee: null, requestedAt: null };

async function loadCleanupSection() {
  if (!state.incident) {
    $('cleanupSection').style.display = 'none';
    return;
  }
  const requests = await storage.loadCleanupRequests(state.incident.id);
  if (requests.length === 0) {
    $('cleanupSection').style.display = state.incident.decision === 'Cleanup requested' ? 'block' : 'none';
    $('cleanupStatus').textContent = '—';
    $('cleanupAssignee').textContent = '—';
    $('cleanupRequestedAt').textContent = '—';
    return;
  }
  const latest = requests[0];
  state.cleanup.id = latest.id;
  state.cleanup.status = latest.status;
  state.cleanup.assignee = latest.assigned_to;
  state.cleanup.requestedAt = latest.requested_at;
  $('cleanupSection').style.display = 'block';
  $('cleanupStatus').textContent = latest.status;
  $('cleanupAssignee').textContent = latest.assigned_to || 'Unassigned';
  $('cleanupRequestedAt').textContent = latest.requested_at;
  $('cleanupRequest').disabled = latest.status === 'completed';
  $('cleanupComplete').disabled = latest.status !== 'requested';
}

async function requestCleanup() {
  if (!state.incident) return;
  const assignee = $('cleanupAssigneeInput').value.trim() || null;
  const result = await storage.requestCleanup(state.incident.id, assignee);
  if (result) {
    state.cleanup.id = result.cleanupRequestId;
    state.cleanup.status = result.status;
    state.cleanup.assignee = result.assignedTo;
    state.cleanup.requestedAt = result.requestedAt;
    $('cleanupStatus').textContent = result.status;
    $('cleanupAssignee').textContent = result.assignedTo || 'Unassigned';
    $('cleanupRequestedAt').textContent = result.requestedAt;
    $('cleanupRequest').disabled = true;
    $('cleanupComplete').disabled = false;
    $('note').textContent = `Cleanup requested${result.assignedTo ? ' for ' + result.assignedTo : ''}. Officer confirmation required.`;
    await refreshHistory();
  } else {
    $('note').textContent = 'Cleanup request recorded locally (API unavailable).';
  }
}

async function completeCleanup() {
  if (!state.cleanup.id) return;
  const result = await storage.updateCleanupRequest(state.cleanup.id, { status: 'completed' });
  if (result) {
    state.cleanup.status = result.status;
    $('cleanupStatus').textContent = result.status;
    $('cleanupComplete').disabled = true;
    $('note').textContent = 'Cleanup marked complete.';
    await refreshHistory();
  }
}

function cancelCleanup() {
  $('cleanupSection').style.display = 'none';
  state.cleanup = { id: null, status: null, assignee: null, requestedAt: null };
  $('note').textContent = 'Cleanup request closed.';
}

/* -------------------------------- History -------------------------------- */

function renderHistory() {
  const records = state.history;
  $('histTotal').textContent = records.length;
  $('histApproved').textContent = records.filter(x => x.decision && x.decision.startsWith('Approved')).length;
  $('histCleanup').textContent = records.filter(x => x.decision === 'Cleanup requested').length;
  $('histBody').innerHTML = records.length
    ? records.map(x => `<tr>
        <td><b>${escapeHTML(x.id)}</b>${x.demo ? ' <span class="demotag">DEMO</span>' : ''}<br><small>${escapeHTML(STATUS_LABEL[x.status] || x.status || '')}</small></td>
        <td>${escapeHTML(x.time)}</td><td>${escapeHTML(x.location)}</td>
        <td>${escapeHTML(x.sceneChange)}</td><td>${escapeHTML(x.plate)}</td>
        <td>${escapeHTML(x.decision)}</td>
        <td><span class="statuscode">${escapeHTML(x.statusCode || '—')}</span></td>
      </tr>`).join('')
    : '<tr><td colspan="7">No incidents recorded yet.</td></tr>';
  $('histNote').textContent = records.some(x => x.demo)
    ? 'Sample DEMO records are illustrative only — they are not real incidents.'
    : (storage.isRemote()
        ? 'Records are mirrored to the API (SQLite) and cached in this browser.'
        : 'Records shown are generated in this browser and stored only in localStorage.');
}

async function refreshHistory() {
  state.history = await storage.load();
  renderHistory();
  updateMap();
}

async function seedHistory() {
  const now = Date.now();
  const sample = [
    { id: 'INC-240381', demo: true, time: new Date(now - 86400000).toLocaleString(), location: 'GVP-01', sceneChange: '16.8%', plate: 'GJ 12 AB 4381', decision: 'Approved for follow-up', status: STATUS.SUSPICIOUS, statusCode: STATUS.APPROVED, source: 'Demo seed', detectionMethod: 'Sample record', evidenceFrames: null },
    { id: 'INC-240296', demo: true, time: new Date(now - 172800000).toLocaleString(), location: 'GVP-02', sceneChange: '4.1%', plate: 'Manual review', decision: 'Rejected — insufficient evidence', status: STATUS.CANDIDATE, statusCode: STATUS.REJECTED, source: 'Demo seed', detectionMethod: 'Sample record', evidenceFrames: null },
    { id: 'INC-240174', demo: true, time: new Date(now - 259200000).toLocaleString(), location: 'GVP-01', sceneChange: '12.4%', plate: 'GJ 05 XX 0001', decision: 'Cleanup requested', status: STATUS.SUSPICIOUS, statusCode: STATUS.CLEANUP_REQUESTED, source: 'Demo seed', detectionMethod: 'Sample record', evidenceFrames: null }
  ];
  await storage.seed(sample);
  await refreshHistory();
}

async function clearHistory() {
  await storage.clear();
  await refreshHistory();
}

/* ---------------------------------- Map ---------------------------------- */

function updateMap() {
  const records = state.history.filter(x => x.location === state.mapZone);
  const frequency = records.length;
  const repeat = new Set(records.map(x => String(x.time || '').slice(0, 10))).size;
  const pendingCleanup = records.filter(x => x.decision === 'Cleanup requested').length;
  $('zoneName').textContent = state.mapZone;
  $('zoneRisk').textContent = state.mapRisk;
  $('zoneCount').textContent = frequency;
  $('zoneScore').textContent = priorityScore({ frequency, repeat, pendingCleanup, isolation: 1 });
  $('mapSource').textContent = storage.isRemote() ? 'API (SQLite)' : 'localStorage';
}

function showZone(name, risk) {
  state.mapZone = name;
  state.mapRisk = risk;
  updateMap();
}

/* ------------------------------- Monitoring ------------------------------ */

function updateMonitorUI() {
  const running = monitor.isRunning();
  $('startMonitor').disabled = running || camera.mode === 'none';
  $('stopMonitor').disabled = !running;
  $('monitorState').className = 'livebadge' + (running ? ' on' : '');
}

const monitor = createMonitor({
  camera,
  getPolygon: () => state.polygon,
  evidence,
  getStableSeconds,
  onTick: ({ diff, stableFor, active, noFrame }) => {
    if (noFrame) { $('monitorState').textContent = 'Waiting for camera frames…'; return; }
    $('monitorState').textContent =
      `${active ? 'Event in progress' : 'Monitoring'} • zone diff ${diff.toFixed(1)}% • stable ${stableFor.toFixed(1)}/${getStableSeconds().toFixed(1)}s`;
  },
  onEvent: ({ diff, frames, stableFor }) => {
    monitor.stop();
    updateMonitorUI();
    createIncident({
      diff, frames, stableFor: Number(stableFor.toFixed(1)),
      source: 'Live monitoring (scene-stability heuristic)'
    });
    $('note').textContent = 'Monitoring produced a review-ready incident. Officer confirmation required.';
    $('monitorState').textContent = 'Incident ready for review';
  }
});

/* --------------------------- Storage indicator --------------------------- */

function updateStorageUI() {
  const remote = storage.isRemote();
  $('storageMode').textContent = remote ? 'API persistence (SQLite)' : 'Local browser storage';
  $('persistenceStatus').textContent = remote ? 'API' : 'LOCAL';
  $('persistenceStatus').className = remote ? 'live' : 'optional';
  $('persistenceDetail').textContent = remote
    ? 'SQLite via /api/v1, mirrored to localStorage'
    : 'localStorage, with optional API backend';
  $('apiStatus').textContent = remote
    ? 'API backend detected — incidents are mirrored to SQLite.'
    : 'API backend not detected — running in offline mode.';
}

/* -------------------------------- Wiring --------------------------------- */

function wireEvents() {
  document.querySelectorAll('.tab').forEach(button => {
    button.onclick = () => {
      document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
      document.querySelectorAll('.view').forEach(x => x.classList.remove('active'));
      button.classList.add('active');
      const view = button.dataset.view;
      $('view-' + view).classList.add('active');
      if (view === 'history' || view === 'map') refreshHistory(); // reload from storage on data views
      if (view === 'live') requestAnimationFrame(() => zoneEditor.sizeCanvas());
    };
  });

  $('srcFile').onclick = () => $('file').click();

  $('file').onchange = async () => {
    const file = $('file').files[0];
    if (!file) return;
    try {
      await camera.useFile(file);
      showVideo();
      state.filename = file.name;
      $('filename').textContent = file.name;
      $('camera').textContent = 'CAM-DEMO-01';
      $('stopWebcam').disabled = true;
      $('note').textContent = 'Video loaded. Run analysis or start monitoring.';
      updateMonitorUI();
    } catch (error) { alert('Could not load video: ' + error.message); }
  };

  $('srcWebcam').onclick = async () => {
    try {
      await camera.useWebcam();
      showVideo();
      state.filename = 'Live webcam';
      $('filename').textContent = 'Live webcam';
      $('camera').textContent = 'CAM-WEBCAM-01';
      $('stopWebcam').disabled = false;
      $('note').textContent = 'Webcam ready. Set the zone, then start monitoring.';
      updateMonitorUI();
    } catch (error) { alert('Webcam unavailable: ' + error.message); }
  };

  $('stopWebcam').onclick = () => resetIncidentUI(true);

  $('editZone').onclick = () => {
    const editing = zoneEditor.setEditing(!zoneEditor.isEditing());
    $('editZone').textContent = editing ? 'Finish editing' : 'Edit polygon';
    $('saveZone').disabled = !editing;
    $('zoneInfo').textContent = editing
      ? 'Click to add • drag vertices • double-click to finish'
      : `${state.polygon.length} points • custom polygon`;
  };

  $('saveZone').onclick = () => {
    zoneEditor.setEditing(false);
    $('editZone').textContent = 'Edit polygon';
    $('saveZone').disabled = true;
    window.localStorage.setItem(CONFIG.zoneKey, JSON.stringify(state.polygon));
    $('zoneInfo').textContent = `${state.polygon.length} points • saved`;
    $('note').textContent = 'GVP zone saved in this browser.';
  };

  $('resetZone').onclick = () => {
    state.polygon = CONFIG.defaultPolygon.map(p => ({ ...p }));
    window.localStorage.setItem(CONFIG.zoneKey, JSON.stringify(state.polygon));
    zoneEditor.draw();
    $('zoneInfo').textContent = '4 points • default rectangle';
    $('note').textContent = 'GVP zone reset to the default rectangle.';
  };

  $('zoneSelect').onchange = () => { $('location').textContent = $('zoneSelect').value; };

  $('analyze').onclick = runAnalysis;
  $('reset').onclick = () => resetIncidentUI(true);
  $('newIncident').onclick = () => resetIncidentUI(false);

  $('startMonitor').onclick = () => {
    if (camera.mode === 'none') { alert('Choose a source first.'); return; }
    monitor.start();
    updateMonitorUI();
    $('note').textContent = 'Monitoring started. Scene-stability heuristic only — not vehicle detection.';
  };

  $('stopMonitor').onclick = () => {
    monitor.stop();
    updateMonitorUI();
    $('monitorState').textContent = 'Stopped';
  };

  $('decideApprove').onclick = () => decide('Approved for follow-up');
  $('decideReject').onclick = () => decide('Rejected — insufficient evidence');
  $('decideCleanup').onclick = () => decide('Cleanup requested');
  $('cleanupRequest').onclick = requestCleanup;
  $('cleanupComplete').onclick = completeCleanup;
  $('cleanupCancel').onclick = cancelCleanup;

  $('plateEdit').oninput = () => {
    const value = $('plateEdit').value.trim();
    $('plate').textContent = value || 'Pending';
    if (state.incident) state.incident.plate = value || 'Manual review pending';
  };

  $('download').onclick = () => {
    if (!state.incident) { alert('Generate and review an incident first.'); return; }
    state.incident.plate = $('plateEdit').value.trim() || state.incident.plate;
    const blob = new Blob([JSON.stringify(buildReport(state.incident), null, 2)], { type: 'application/json' });
    const anchor = document.createElement('a');
    anchor.href = URL.createObjectURL(blob);
    anchor.download = state.incident.id + '-report.json';
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(anchor.href), 1000);
  };

  async function downloadEvidenceFrame(frame) {
    if (!state.incident) { alert('Generate and review an incident first.'); return; }
    const blob = await storage.downloadEvidence(state.incident.id, frame);
    if (blob) {
      const anchor = document.createElement('a');
      anchor.href = URL.createObjectURL(blob);
      anchor.download = `${state.incident.id}-${frame}.jpg`;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(anchor.href), 1000);
    } else {
      // Offline fallback: download from the canvas data URL already rendered
      const canvas = $('c' + ({ before: 1, during: 2, after: 3 }[frame]));
      if (canvas && canvas.toDataURL) {
        const anchor = document.createElement('a');
        anchor.href = canvas.toDataURL('image/jpeg', 0.6);
        anchor.download = `${state.incident.id}-${frame}.jpg`;
        anchor.click();
      }
    }
  }

  $('dlBefore').onclick = () => downloadEvidenceFrame('before');
  $('dlDuring').onclick = () => downloadEvidenceFrame('during');
  $('dlAfter').onclick = () => downloadEvidenceFrame('after');

  $('seedHistory').onclick = seedHistory;
  $('clearHistory').onclick = clearHistory;

  document.querySelectorAll('.pin').forEach(pin => {
    pin.onclick = () => showZone(pin.dataset.zone, pin.dataset.risk);
  });
}

/* --------------------------------- Boot ---------------------------------- */

async function init() {
  await storage.check();
  updateStorageUI();
  $('stableSeconds').value = CONFIG.monitor.defaultStableSeconds;
  $('location').textContent = $('zoneSelect').value;
  zoneEditor.sizeCanvas();
  zoneEditor.draw();
  $('zoneInfo').textContent = `${state.polygon.length} points • ${window.localStorage.getItem(CONFIG.zoneKey) ? 'saved polygon' : 'default rectangle'}`;
  wireEvents();
  resetIncidentUI(true);
  await refreshHistory();
  updateMonitorUI();
  $('monitorState').textContent = 'Idle • scene-stability heuristic, not vehicle tracking';
}

init();
