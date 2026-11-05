/** Rolling frame buffer + canvas painting. Frames are real captured pixels, not labels. */
export function createEvidenceBuffer(size) {
  const frames = [];
  return {
    push(frame) {
      if (!frame) return;
      frames.push(frame);
      while (frames.length > size) frames.shift();
    },
    snapshots() {
      if (!frames.length) return { before: null, during: null, after: null };
      const mid = Math.floor((frames.length - 1) / 2);
      return { before: frames[0], during: frames[mid], after: frames[frames.length - 1] };
    },
    clear() { frames.length = 0; },
    get size() { return frames.length; }
  };
}

/** Paint a captured frame object onto a <canvas> using its raw ImageData. */
export function paintFrame(canvas, frame) {
  if (!canvas || !frame) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  canvas.width = frame.width;
  canvas.height = frame.height;
  if (ctx.putImageData) ctx.putImageData(frame.imageData, 0, 0);
}

export function clearCanvas(canvas) {
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (ctx && ctx.clearRect) ctx.clearRect(0, 0, canvas.width, canvas.height);
}
