"""RTSP/CCTV camera capture service.

Uses OpenCV VideoCapture to connect to RTSP streams and capture frames
for scene-stability monitoring. Runs in the backend so the browser only
ever uses same-origin HTTP (no CORS, no direct RTSP from the client).

Claim discipline: this is a scene-stability heuristic feed, not vehicle
detection, tracking, or a dumping model. Human review is mandatory.
"""

import threading
import time
from datetime import datetime, timezone

import cv2

from . import db


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


class RTSPCamera:
    """Background capture for a single RTSP camera."""

    def __init__(self, camera_id: str, stream_ref: str):
        self.camera_id = camera_id
        self.stream_ref = stream_ref
        self._cap = None
        self._thread = None
        self._stop = threading.Event()
        self._latest_frame = None
        self._lock = threading.Lock()
        self._fps = 0.0
        self._error = None
        self._connected = False
        self._last_ts = 0.0

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self._connected = False

    def _capture_loop(self):
        backoff = 1.0
        while not self._stop.is_set():
            try:
                if self._cap is None:
                    self._cap = cv2.VideoCapture(self.stream_ref)
                    if not self._cap.isOpened():
                        self._error = f'Cannot open stream: {self.stream_ref}'
                        self._connected = False
                        if self._cap:
                            self._cap.release()
                            self._cap = None
                        time.sleep(min(backoff, 30))
                        backoff = min(backoff * 2, 30)
                        continue
                    self._connected = True
                    self._error = None
                    backoff = 1.0
                    db.update_camera_status(self.camera_id, 'online')

                ret, frame = self._cap.read()
                if not ret or frame is None:
                    self._error = 'Lost stream connection'
                    self._connected = False
                    db.update_camera_status(self.camera_id, 'offline')
                    try:
                        self._cap.release()
                    except Exception:
                        pass
                    self._cap = None
                    time.sleep(min(backoff, 30))
                    backoff = min(backoff * 2, 30)
                    continue

                ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ok:
                    jpeg = buf.tobytes()
                    ts = time.time()
                    with self._lock:
                        self._latest_frame = (ts, jpeg)
                        self._last_ts = ts
                    interval = ts - self._last_ts if ts > self._last_ts else 0.001
                    self._fps = self._fps * 0.9 + 0.1 * (1.0 / interval)

            except Exception as exc:
                self._error = str(exc)
                self._connected = False
                db.update_camera_status(self.camera_id, 'error')
                try:
                    if self._cap:
                        self._cap.release()
                except Exception:
                    pass
                self._cap = None
                time.sleep(min(backoff, 30))
                backoff = min(backoff * 2, 30)

    def get_latest_frame(self):
        with self._lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame

    def is_connected(self):
        return self._connected

    def get_error(self):
        return self._error

    def get_fps(self):
        return self._fps


_camera_registry = {}
_registry_lock = threading.Lock()


def start_camera(camera_id: str, stream_ref: str) -> bool:
    with _registry_lock:
        if camera_id in _camera_registry:
            return True
        cam = RTSPCamera(camera_id, stream_ref)
        cam.start()
        _camera_registry[camera_id] = cam
    return True


def stop_camera(camera_id: str) -> bool:
    with _registry_lock:
        cam = _camera_registry.pop(camera_id, None)
    if cam:
        cam.stop()
        db.update_camera_status(camera_id, 'offline')
        return True
    return False


def get_camera_instance(camera_id: str):
    with _registry_lock:
        return _camera_registry.get(camera_id)


def get_camera_frame(camera_id: str):
    cam = get_camera_instance(camera_id)
    if cam is None:
        return None
    return cam.get_latest_frame()


def stop_all_cameras():
    with _registry_lock:
        ids = list(_camera_registry.keys())
    for cid in ids:
        stop_camera(cid)


def list_active_cameras():
    result = []
    with _registry_lock:
        for cid, cam in _camera_registry.items():
            result.append({
                'camera_id': cid,
                'connected': cam.is_connected(),
                'fps': round(cam.get_fps(), 1),
                'error': cam.get_error(),
            })
    return result
