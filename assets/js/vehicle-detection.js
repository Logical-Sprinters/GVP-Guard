/**
 * Vehicle Detection Module — Step 4 (DEMO STAGE)
 *
 * Wraps YOLO11n via OpenCV DNN (ONNX) for vehicle detection in the GVP zone.
 * This is DEMO STAGE code — not WORKING until benchmarked on a held-out test set.
 * No accuracy figures may be published without documented tests.
 *
 * Prerequisites (see docs/STEP4_READINESS_PLAN.md):
 * - models/weights/yolo11n.onnx downloaded (NOT committed to Git)
 * - Controlled dataset collected and annotated
 * - Benchmark results recorded
 *
 * Usage:
 *   const detector = createVehicleDetector({ modelPath, confThreshold, onDetection });
 *   detector.start(videoElement);
 *   detector.stop();
 */

export function createVehicleDetector({
  modelPath = 'models/weights/yolo11n.onnx',
  confThreshold = 0.25,
  iouThreshold = 0.45,
  inputSize = 640,
  onDetection = () => {},
  onError = () => {},
} = {}) {
  let net = null;
  let active = false;
  let rafId = null;

  const VEHICLE_CLASS_IDS = { 2: 'car', 5: 'bus', 7: 'truck', 3: 'motorcycle' };

  // COCO class names for reference
  const CLASS_NAMES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
    'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
    'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
    'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
    'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
    'hair drier', 'toothbrush',
  ];

  async function init() {
    if (active) return;
    try {
      net = cv.dnn.readNetFromONNX(modelPath);
      active = true;
    } catch (err) {
      active = false;
      onError(err);
      throw err;
    }
  }

  function detect(frame) {
    if (!active || !net) return [];

    const { width: vidW, height: vidH } = frame;

    // Preprocess: blob from image (YOLO expects 640x640, normalized 1/255)
    const blob = cv.dnn.blobFromImage(frame, 1 / 255.0, new cv.Size(inputSize, inputSize), new cv.Scalar(), true, false);
    net.setInput(blob);

    const outputs = net.forward();
    blob.delete();

    // outputs shape: [1, 84, 8400] -> transpose to [8400, 84]
    const data = outputs.data32F || outputs.getDataAsFloat32 ? outputs.getDataAsFloat32() : [];
    outputs.delete();

    const rows = 8400;
    const cols = 84;
    const boxes = [];
    const confidences = [];
    const classIds = [];

    for (let r = 0; r < rows; r++) {
      const rowOffset = r * cols;
      const cx = data[rowOffset + 0];
      const cy = data[rowOffset + 1];
      const w = data[rowOffset + 2];
      const h = data[rowOffset + 3];
      const objectness = data[rowOffset + 4];

      // Find best class score
      let bestClassId = 0;
      let bestClassScore = 0;
      for (let c = 5; c < cols; c++) {
        const score = data[rowOffset + c];
        if (score > bestClassScore) {
          bestClassScore = score;
          bestClassId = c - 5;
        }
      }

      const confidence = bestClassScore * objectness;

      if (confidence > confThreshold && VEHICLE_CLASS_IDS.hasOwnProperty(bestClassId)) {
        // Convert center coords + size to x1, y1, x2, y2 in original image coordinates
        const x1 = Math.max(0, Math.floor(((cx - w / 2) / inputSize) * vidW));
        const y1 = Math.max(0, Math.floor(((cy - h / 2) / inputSize) * vidH));
        const x2 = Math.min(vidW, Math.floor(((cx + w / 2) / inputSize) * vidW));
        const y2 = Math.min(vidH, Math.floor(((cy + h / 2) / inputSize) * vidH));

        boxes.push([x1, y1, x2 - x1, y2 - y1]); // [x, y, w, h] for NMS
        confidences.push(confidence);
        classIds.push(bestClassId);
      }
    }

    // Non-Maximum Suppression
    const indices = cv.dnn.NMSBoxes(boxes, confidences, confThreshold, iouThreshold);

    const detections = [];
    for (let i = 0; i < indices.length; i++) {
      const idx = indices.get ? indices.get(i) : indices[i];
      const [x, y, wBox, hBox] = boxes[idx];
      const classId = classIds[idx];
      const label = CLASS_NAMES[classId] || `class_${classId}`;

      detections.push({
        box: { x1: x, y1: y, x2: x + wBox, y2: y + hBox },
        width: wBox,
        height: hBox,
        confidence: confidences[idx],
        classId,
        className: label,
        center: { x: x + wBox / 2, y: y + hBox / 2 },
      });
    }

    indices.delete();

    return detections;
  }

  function start(videoElement) {
    if (!active) {
      init().catch(() => {});
    }
    if (rafId) return;

    function loop() {
      if (!active) return;
      try {
        const detections = detect(videoElement);
        if (detections.length > 0) {
          onDetection(detections);
        }
      } catch (err) {
        // Silent fail on individual frame errors
      }
      rafId = requestAnimationFrame(loop);
    }
    rafId = requestAnimationFrame(loop);
  }

  function stop() {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    active = false;
    if (net) {
      net.delete();
      net = null;
    }
  }

  return { init, detect, start, stop, isActive: () => active };
}

/**
 * Vehicle Stop Timer — Step 4 (DEMO STAGE)
 *
 * Tracks how long each detected vehicle remains stopped inside the GVP polygon.
 * A "stop" is registered when a vehicle's centroid remains inside the polygon
 * for longer than stopThresholdSeconds.
 *
 * DEMO STAGE: not WORKING until benchmarked. Stop time alone does NOT imply guilt.
 */

export function createStopTimer({
  stopThresholdSeconds = 2,
  onStopStart = () => {},
  onStopEnd = () => {},
  onTick = () => {},
} = {}) {
  const tracks = {}; // trackId -> { startTime, vehicleType, firstSeen, lastSeen, stopEvents }

  function update(detections, polygon, now = Date.now()) {
    const activeTrackIds = new Set();

    for (const det of detections) {
      // Use detection center as proxy for track ID (no ByteTrack integration yet)
      // In full implementation, ByteTrack provides persistent trackId
      const trackId = `det_${Math.floor(det.center.x / 10)}_${Math.floor(det.center.y / 10)}`;
      activeTrackIds.add(trackId);

      if (!tracks[trackId]) {
        tracks[trackId] = {
          startTime: now,
          vehicleType: det.className,
          firstSeen: now,
          lastSeen: now,
          stopEvents: [],
          inPolygon: false,
          stopStartTime: null,
        };
      }

      const track = tracks[trackId];
      track.lastSeen = now;

      // Check if centroid is inside GVP polygon
      const inside = pointInPolygon(det.center, polygon);

      if (inside && !track.inPolygon) {
        // Vehicle just entered polygon
        track.inPolygon = true;
        track.stopStartTime = now;
      } else if (!inside && track.inPolygon) {
        // Vehicle just left polygon
        track.inPolygon = false;
        if (track.stopStartTime) {
          const stopDuration = (now - track.stopStartTime) / 1000;
          track.stopEvents.push({ start: track.stopStartTime, end: now, duration: stopDuration });
          if (stopDuration >= stopThresholdSeconds) {
            onStopEnd({ trackId, vehicleType: track.vehicleType, duration: stopDuration });
          }
          track.stopStartTime = null;
        }
      }

      if (inside && track.stopStartTime) {
        const stopDuration = (now - track.stopStartTime) / 1000;
        onTick({ trackId, vehicleType: track.vehicleType, duration: stopDuration });
        if (stopDuration >= stopThresholdSeconds && !track.longStopLogged) {
          track.longStopLogged = true;
          onStopStart({ trackId, vehicleType: track.vehicleType, duration: stopDuration });
        }
      }
    }

    // Clean up tracks that are no longer active
    for (const trackId of Object.keys(tracks)) {
      if (!activeTrackIds.has(trackId)) {
        if (tracks[trackId].stopStartTime) {
          const stopDuration = (now - tracks[trackId].stopStartTime) / 1000;
          tracks[trackId].stopEvents.push({ start: tracks[trackId].stopStartTime, end: now, duration: stopDuration });
        }
        delete tracks[trackId];
      }
    }

    return tracks;
  }

  function getStoppedVehicles(threshold = stopThresholdSeconds) {
    const stopped = [];
    const now = Date.now();
    for (const [trackId, track] of Object.entries(tracks)) {
      if (track.inPolygon && track.stopStartTime) {
        const duration = (now - track.stopStartTime) / 1000;
        if (duration >= threshold) {
          stopped.push({ trackId, vehicleType: track.vehicleType, duration });
        }
      }
    }
    return stopped;
  }

  function reset() {
    for (const trackId of Object.keys(tracks)) {
      delete tracks[trackId];
    }
  }

  return { update, getStoppedVehicles, reset };
}

/**
 * Point-in-polygon test (ray casting). Polygon points are normalised [0..1].
 * Point is {x, y} in normalised [0..1] coords.
 */
function pointInPolygon(point, polygon) {
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