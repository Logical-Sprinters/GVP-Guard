import { clamp } from './core.js';

/**
 * Editable GVP polygon drawn on an overlay canvas.
 * Coordinates are normalised [0..1] so they survive resizes and video sources.
 */
export function createZoneEditor({ stage, canvas, getPolygon, setPolygon, onChange }) {
  let editing = false;
  let dragging = -1;

  function sizeCanvas() {
    const rect = stage.getBoundingClientRect();
    canvas.width = Math.max(1, Math.round(rect.width || stage.clientWidth || 640));
    canvas.height = Math.max(1, Math.round(rect.height || stage.clientHeight || 360));
    draw();
  }

  function pointFromEvent(event) {
    const rect = canvas.getBoundingClientRect();
    const w = rect.width || canvas.width;
    const h = rect.height || canvas.height;
    return {
      x: clamp((event.clientX - rect.left) / w, 0, 1),
      y: clamp((event.clientY - rect.top) / h, 0, 1)
    };
  }

  function draw() {
    const ctx = canvas.getContext('2d');
    if (!ctx || !ctx.clearRect) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const poly = getPolygon();
    if (!poly || poly.length < 3) return;
    ctx.beginPath();
    poly.forEach((p, i) => {
      const x = p.x * canvas.width, y = p.y * canvas.height;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.closePath();
    if (ctx.fill) { ctx.fillStyle = 'rgba(244,91,11,0.10)'; ctx.fill(); }
    if (ctx.setLineDash) ctx.setLineDash(editing ? [7, 5] : []);
    if (ctx.stroke) { ctx.strokeStyle = '#f45b0b'; ctx.lineWidth = 3; ctx.stroke(); }
    if (ctx.setLineDash) ctx.setLineDash([]);
    if (!editing || !ctx.arc) return;
    poly.forEach(p => {
      const x = p.x * canvas.width, y = p.y * canvas.height;
      ctx.beginPath();
      ctx.arc(x, y, 7, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.strokeStyle = '#f45b0b';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }

  function nearestVertex(point) {
    const poly = getPolygon();
    let best = -1, bestDistance = 0.035;
    poly.forEach((p, i) => {
      const d = Math.hypot(p.x - point.x, p.y - point.y);
      if (d < bestDistance) { bestDistance = d; best = i; }
    });
    return best;
  }

  canvas.addEventListener('pointerdown', event => {
    if (!editing) return;
    const point = pointFromEvent(event);
    dragging = nearestVertex(point);
    if (dragging >= 0) return;
    setPolygon([...getPolygon(), point]);
    onChange();
    draw();
  });

  canvas.addEventListener('pointermove', event => {
    if (!editing || dragging < 0) return;
    const point = pointFromEvent(event);
    const poly = [...getPolygon()];
    poly[dragging] = point;
    setPolygon(poly);
    onChange();
    draw();
  });

  const stopDrag = () => { dragging = -1; };
  canvas.addEventListener('pointerup', stopDrag);
  canvas.addEventListener('pointercancel', stopDrag);
  canvas.addEventListener('dblclick', () => { if (editing) setEditing(false); });
  window.addEventListener('resize', sizeCanvas);

  function setEditing(value) {
    editing = Boolean(value);
    stage.classList.toggle('editing', editing);
    dragging = -1;
    draw();
    return editing;
  }

  return { sizeCanvas, draw, setEditing, isEditing: () => editing };
}
