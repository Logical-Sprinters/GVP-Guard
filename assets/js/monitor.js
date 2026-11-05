import { CONFIG } from './config.js';
import { sceneDifference } from './core.js';

/**
 * Live scene-stability monitor.
 * IMPORTANT: this is a heuristic frame-differencing timer inside the GVP polygon.
 * It is NOT vehicle detection, tracking, a vehicle stop timer or a dumping model.
 */
export function createMonitor({ camera, getPolygon, evidence, onEvent, onTick, getStableSeconds }) {
  let timer = null;
  let lastFrame = null;
  let eventStartFrame = null;
  let active = false;
  let stableSince = 0;

  function tick() {
    const frame = camera.grabFrame(CONFIG.capture.width, CONFIG.capture.height);
    if (!frame) {
      onTick({ diff: 0, stableFor: 0, active, noFrame: true });
      return;
    }
    const polygon = getPolygon();
    const diff = lastFrame ? sceneDifference(lastFrame, frame, polygon) : 0;
    evidence.push(frame);
    const now = performance.now();
    let stableFor = 0;

    if (diff >= CONFIG.monitor.changeThreshold) {
      if (!active) {
        active = true;
        eventStartFrame = lastFrame || frame;
      }
      stableSince = 0;
    } else if (active) {
      if (!stableSince) stableSince = now;
      stableFor = (now - stableSince) / 1000;
      if (stableFor >= getStableSeconds()) {
        const beforeAfterDiff = sceneDifference(eventStartFrame, frame, polygon);
        const frames = evidence.snapshots();
        onEvent({ diff: beforeAfterDiff, frames, stableFor });
        active = false;
        eventStartFrame = null;
        stableSince = 0;
        evidence.clear();
      }
    }
    lastFrame = frame;
    onTick({ diff, stableFor, active });
  }

  function start() {
    if (timer) return;
    lastFrame = null;
    active = false;
    stableSince = 0;
    eventStartFrame = null;
    evidence.clear();
    timer = setInterval(tick, 1000 / CONFIG.monitor.fps);
    tick();
  }

  function stop() {
    if (timer) clearInterval(timer);
    timer = null;
    lastFrame = null;
    active = false;
    stableSince = 0;
    eventStartFrame = null;
  }

  return { start, stop, isRunning: () => Boolean(timer) };
}
