import { CONFIG } from './config.js';
import { clamp } from './core.js';

/** Owns the <video> element: recorded file or live webcam, plus frame capture. */
export function createCamera(video) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  let objectUrl = null;
  let stream = null;
  let mode = 'none';

  function releaseObjectUrl() {
    if (objectUrl) { URL.revokeObjectURL(objectUrl); objectUrl = null; }
  }

  function stopWebcam() {
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    if (video.srcObject) video.srcObject = null;
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
    releaseObjectUrl();
    objectUrl = URL.createObjectURL(file);
    video.srcObject = null;
    video.src = objectUrl;
    video.controls = true;
    mode = 'file';
    await waitForMetadata();
    return file.name;
  }

  async function useWebcam() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Webcam API is not available in this browser or origin.');
    }
    stopWebcam();
    releaseObjectUrl();
    video.removeAttribute('src');
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false
    });
    video.srcObject = stream;
    video.muted = true;
    video.controls = false;
    mode = 'webcam';
    await waitForMetadata();
    try { await video.play(); } catch { /* autoplay may be blocked; user can still monitor */ }
  }

  function clear() {
    stopWebcam();
    releaseObjectUrl();
    video.pause();
    video.removeAttribute('src');
    video.style.display = 'none';
    mode = 'none';
  }

  /** Capture one frame. Returns both raw pixels (for differencing) and a JPEG data URL. */
  function grabFrame(width = CONFIG.capture.width, height = CONFIG.capture.height) {
    if (!video.videoWidth || !video.videoHeight) return null;
    canvas.width = width;
    canvas.height = height;
    ctx.drawImage(video, 0, 0, width, height);
    const imageData = ctx.getImageData(0, 0, width, height);
    let dataUrl = '';
    try { dataUrl = canvas.toDataURL('image/jpeg', CONFIG.capture.jpegQuality); } catch { /* non-browser test env */ }
    return { imageData, data: imageData.data, width, height, dataUrl };
  }

  /** Seek with a timeout fallback so a missing `seeked` event cannot hang the analysis. */
  function seekTo(time) {
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
    useFile, useWebcam, clear, grabFrame, seekTo,
    get mode() { return mode; },
    get duration() { return video.duration; },
    get hasFrame() { return Boolean(video.videoWidth && video.videoHeight); }
  };
}
