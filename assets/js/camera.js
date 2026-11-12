import { CONFIG } from './config.js';
import { clamp } from './core.js';

/** Owns the <video> element: recorded file or live webcam, plus frame capture.
 *  Also owns an  element for RTSP/MJPEG camera feeds (same-origin only).
 */
export function createCamera(video, mjpegImg) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  let objectUrl = null;
  let stream = null;
  let mode = 'none'; // 'none' | 'file' | 'webcam' | 'rtsp'
  let rtspCameraId = null;
  let mjpegController = null; // AbortController for MJPEG fetch

  function releaseObjectUrl() {
    if (objectUrl) { URL.revokeObjectURL(objectUrl); objectUrl = null; }
  }

  function stopWebcam() {
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    if (video.srcObject) video.srcObject = null;
  }

  function stopRTSP() {
    if (mjpegController) { mjpegController.abort(); mjpegController = null; }
    if (mjpegImg) mjpegImg.style.display = 'none';
    rtspCameraId = null;
  }

  function waitForMetadata(timeout = 5000) {
    return new Promise(resolve => {
      if (video.readyState >= 1) return resolve();
      let done = false;
      const finish = () => {
        if (done) return;
        done = true;
        video.removeEventListener('loadedmetadata', finish);
        clearTimeout(timer);
        resolve();
      };
      const timer = setTimeout(finish, timeout);
      video.addEventListener('loadedmetadata', finish, { once: true });
    });
  }

  async function useFile(file) {
    stopWebcam();
    stopRTSP();
    releaseObjectUrl();
    objectUrl = URL.createObjectURL(file);
    video.srcObject = null;
    video.src = objectUrl;
    video.controls = true;
    video.style.display = 'block';
    if (mjpegImg) mjpegImg.style.display = 'none';
    mode = 'file';
    await waitForMetadata();
    return file.name;
  }

  async function useWebcam() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Webcam API is not available in this browser or origin.');
    }
    stopWebcam();
    stopRTSP();
    releaseObjectUrl();
    video.removeAttribute('src');
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false
    });
    video.srcObject = stream;
    video.muted = true;
    video.controls = false;
    video.style.display = 'block';
    if (mjpegImg) mjpegImg.style.display = 'none';
    mode = 'webcam';
    await waitForMetadata();
    try { await video.play(); } catch { /* autoplay may be blocked */ }
  }

  /** Connect to an RTSP camera via same-origin MJPEG proxy. */
  async function useRTSP(cameraId) {
    stopWebcam();
    stopRTSP();
    releaseObjectUrl();
    video.removeAttribute('src');
    video.style.display = 'none';
    if (mjpegImg) {
      mjpegImg.style.display = 'block';
      mjpegImg.src = '';
    }
    mode = 'rtsp';
    rtspCameraId = cameraId;
    const url = `${CONFIG.apiBase}/cameras/${encodeURIComponent(cameraId)}/stream`;
    mjpegController = new AbortController();
    try {
      const response = await fetch(url, { signal: mjpegController.signal });
      if (!response.ok || !response.body) {
        throw new Error(`RTSP stream failed: ${response.status}`);
      }
      if (mjpegImg) mjpegImg.src = url;
    } catch (err) {
      mode = 'none';
      rtspCameraId = null;
      throw new Error('RTSP camera unavailable: ' + err.message);
    }
    return cameraId;
  }

  function clear() {
    stopWebcam();
    stopRTSP();
    releaseObjectUrl();
    video.pause();
    video.removeAttribute('src');
    video.style.display = 'none';
    mode = 'none';
  }

  /** Capture one frame. Returns both raw pixels (for differencing) and a JPEG data URL. */
  function grabFrame(width = CONFIG.capture.width, height = CONFIG.capture.height) {
    const source = mode === 'rtsp' && mjpegImg ? mjpegImg : video;
    if (!source) return null;
    if (mode === 'file' || mode === 'webcam') {
      if (!video.videoWidth || !video.videoHeight) return null;
    }
    if (mode === 'rtsp') {
      if (!mjpegImg || !mjpegImg.complete || mjpegImg.naturalWidth === 0) return null;
    }
    canvas.width = width;
    canvas.height = height;
    ctx.drawImage(source, 0, 0, width, height);
    const imageData = ctx.getImageData(0, 0, width, height);
    let dataUrl = '';
    try { dataUrl = canvas.toDataURL('image/jpeg', CONFIG.capture.jpegQuality); } catch { /* non-browser test env */ }
    return { imageData, data: imageData.data, width, height, dataUrl };
  }

  /** Seek with a timeout fallback (only meaningful for recorded files). */
  function seekTo(time) {
    if (mode !== 'file') return Promise.resolve();
    return new Promise(resolve => {
      const target = clamp(time, 0, Math.max(0, (video.duration || 1) - 0.05));
      let done = false;
      const finish = () => {
        if (done) return;
        done = true;
        video.removeEventListener('seeked', finish);
        clearTimeout(timer);
        setTimeout(resolve, 80);
      };
      const timer = setTimeout(finish, 1500);
      video.addEventListener('seeked', finish, { once: true });
      if (Math.abs(video.currentTime - target) < 0.01) return finish();
      try { video.currentTime = target; } catch { finish(); }
    });
  }

  return {
    useFile, useWebcam, useRTSP, clear, grabFrame, seekTo,
    get mode() { return mode; },
    get rtspCameraId() { return rtspCameraId; },
    get duration() { return mode === 'file' ? video.duration : undefined; },
    get hasFrame() {
      if (mode === 'rtsp') return Boolean(mjpegImg && mjpegImg.complete && mjpegImg.naturalWidth > 0);
      return Boolean(video.videoWidth && video.videoHeight);
    },
  };
}
