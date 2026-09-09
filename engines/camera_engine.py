"""
engines/camera_engine.py  —  Phase 4 & 5
==========================================
Webcam capture + MediaPipe HandLandmarker (Tasks API, mediapipe >= 0.10).
Runs in a QThread; emits signals to the GUI thread.

Only ONE hand is ever tracked at a time.
The first hand detected is locked in (by handedness label).
If that hand disappears for _LOCK_RELEASE_FRAMES frames the lock is released
and the next visible hand becomes the active one.
"""
from __future__ import annotations
import time
import os
import cv2
import mediapipe as mp
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker, HandLandmarkerOptions, RunningMode,
)
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui  import QImage
from core.logger    import get_logger

log = get_logger(__name__)

_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "models", "hand_landmarker.task"
)

_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17),
]
_DOT_COLOR  = (124, 58, 237)
_LINE_COLOR = (167, 139, 250)


def _draw_landmarks(frame, landmarks, w, h):
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    for a, b in _CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], _LINE_COLOR, 1)
    for x, y in pts:
        cv2.circle(frame, (x, y), 3, _DOT_COLOR, -1)


class CameraEngine(QThread):
    sig_frame         = Signal(QImage)
    sig_landmarks     = Signal(list)
    sig_no_hand       = Signal()        # emitted every frame when no hand detected
    sig_fps           = Signal(float)
    sig_hand_detected = Signal(bool)
    sig_error         = Signal(str)

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self._cfg     = cfg
        self._running = False

        model_path = os.path.normpath(_MODEL_PATH)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"hand_landmarker.task not found: {model_path}")

        opts = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.VIDEO,
            num_hands=1,          # hard limit: MediaPipe only returns 1 hand
            min_hand_detection_confidence=cfg.hand_tracking.min_detection_confidence,
            min_hand_presence_confidence=cfg.hand_tracking.min_tracking_confidence,
            min_tracking_confidence=cfg.hand_tracking.min_tracking_confidence,
        )
        self._detector = HandLandmarker.create_from_options(opts)

    def _open_camera(self):
        cap = cv2.VideoCapture(self._cfg.camera.device_index)
        if not cap.isOpened():
            self.sig_error.emit("Camera not available.")
            log.error("Camera index %d not available.", self._cfg.camera.device_index)
            return None
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self._cfg.camera.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._cfg.camera.height)
        cap.set(cv2.CAP_PROP_FPS,          self._cfg.camera.fps)
        return cap

    def _select_hand(self, result):
        """Return landmarks of the largest right-hand detection, or None."""
        chosen_lms = None
        best_size  = 0.0
        if not result.hand_landmarks:
            return None
        for i, lms in enumerate(result.hand_landmarks):
            label = None
            if result.handedness and i < len(result.handedness):
                label = result.handedness[i][0].category_name
            is_right = (label == "Left") if self._cfg.camera.flip_horizontal else (label == "Right")
            if not is_right:
                continue
            xs = [lm.x for lm in lms]
            ys = [lm.y for lm in lms]
            size = (max(xs) - min(xs)) * (max(ys) - min(ys))
            if size > best_size:
                best_size  = size
                chosen_lms = lms
        return chosen_lms

    def _process_frame(self, frame, start_mono, prev_time):
        """Detect hand in one frame, emit signals. Returns updated prev_time."""
        if self._cfg.camera.flip_horizontal:
            frame = cv2.flip(frame, 1)
        h, w   = frame.shape[:2]
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms  = int((time.monotonic() - start_mono) * 1000)
        result = self._detector.detect_for_video(mp_img, ts_ms)

        chosen_lms = self._select_hand(result)
        self.sig_hand_detected.emit(chosen_lms is not None)
        if chosen_lms is not None:
            _draw_landmarks(frame, chosen_lms, w, h)
            self.sig_landmarks.emit(chosen_lms)
        else:
            self.sig_no_hand.emit()

        now = time.monotonic()
        self.sig_fps.emit(1.0 / max(now - prev_time, 1e-6))
        qimg = QImage(frame.data, w, h, 3 * w, QImage.Format_BGR888)
        self.sig_frame.emit(qimg.copy())
        return now

    def run(self):
        self._running = True
        cap = self._open_camera()
        if cap is None:
            return

        prev_time   = time.monotonic()
        start_mono  = time.monotonic()
        log.info("CameraEngine started (device %d).", self._cfg.camera.device_index)

        while self._running:
            ret, frame = cap.read()
            if not ret:
                continue
            if not self._running:
                break
            try:
                prev_time = self._process_frame(frame, start_mono, prev_time)
            except RuntimeError:
                break

        cap.release()
        try:
            self._detector.close()
        except RuntimeError as e:
            log.debug("Detector close error (ignored): %s", e)
        log.info("CameraEngine stopped.")

    def stop(self):
        self._running = False
        self.wait()
