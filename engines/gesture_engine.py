"""
engines/gesture_engine.py
==========================
Robust gesture engine.

Detection method
----------------
Each finger is checked with TWO independent tests — both must agree:
  1. tip.y < pip.y        (tip above PIP in image = extended)
  2. tip.y < dip.y        (tip above DIP = not curled)
This kills false positives from tilted hands.

Thumb uses distance from INDEX_MCP (works for left + right hand).

Anti-flicker: a rolling vote buffer of _VOTE_WINDOW frames.
The gesture with the majority vote wins. Only a gesture that holds
the majority for _STABLE consecutive frames enters the hold phase.

Pipeline
--------
  IDLE      — no valid gesture held yet
  SCANNING  — same gesture stable for _STABLE frames, hold bar fills
  FIRED     — action dispatched, enter COOLDOWN immediately
  COOLDOWN  — _COOLDOWN_FRAMES lockout, nothing scanned

Gestures
--------
  ✋ OPEN_HAND    all 5 up           → Play / Resume
  ✊ FIST         all 4 fingers down  → Stop (stays stopped until Open Hand / Rock / Peace)
  🤘 ROCK         index + pinky up    → Next Song
  ✌  TWO_FINGERS  index + middle up   → Previous Song
  ☝  INDEX_FINGER index only          → swipe L↔R = Vol+/−
"""
from __future__ import annotations
import math
from collections import deque
from PySide6.QtCore import QObject, Signal
from core.constants import (
    Gesture, GESTURE_ACTIONS,
    WRIST,
    THUMB_TIP, THUMB_IP,
    INDEX_TIP,  INDEX_PIP,  INDEX_DIP,  INDEX_MCP,
    MIDDLE_TIP, MIDDLE_PIP, MIDDLE_DIP,
    RING_TIP,   RING_PIP,   RING_DIP,
    PINKY_TIP,  PINKY_PIP,  PINKY_DIP,
)
from core.logger import get_logger

log = get_logger(__name__)

# ── Tuning ────────────────────────────────────────────────────────────────────
_VOTE_WINDOW     = 15   # rolling window for majority-vote anti-flicker
_STABLE          = 20   # consecutive majority frames before hold starts (0.67s)
_HOLD_FRAMES     = 60   # frames to hold → fire  (2s @ 30 fps)
_COOLDOWN_FRAMES = 30   # frames of lockout after fire (1 s @ 30 fps)

_SWIPE_WINDOW    = 12   # frames of index-tip X to measure
_SWIPE_THRESHOLD = 0.07 # normalised X travel for a swipe
_SWIPE_COOLDOWN  = 15   # frames between swipe fires


# ── Finger detection ──────────────────────────────────────────────────────────

def _up(lm, tip: int, pip: int, dip: int) -> bool:
    """
    Finger extended = tip is farther from wrist than both PIP and DIP.
    Distance-based: works at any hand orientation/angle.
    """
    w = WRIST
    tip_d = math.hypot(lm[tip].x - lm[w].x, lm[tip].y - lm[w].y)
    pip_d = math.hypot(lm[pip].x - lm[w].x, lm[pip].y - lm[w].y)
    dip_d = math.hypot(lm[dip].x - lm[w].x, lm[dip].y - lm[w].y)
    return tip_d > pip_d and tip_d > dip_d


def _thumb_up(lm) -> bool:
    """
    Thumb extended = tip is further from INDEX_MCP than IP joint is.
    Works for both left and right hands.
    """
    return (math.hypot(lm[THUMB_TIP].x - lm[INDEX_MCP].x, lm[THUMB_TIP].y - lm[INDEX_MCP].y) >
            math.hypot(lm[THUMB_IP].x  - lm[INDEX_MCP].x, lm[THUMB_IP].y  - lm[INDEX_MCP].y) * 1.15)


def _finger_states(lm) -> list[bool]:
    """Returns [thumb, index, middle, ring, pinky] — True = extended."""
    return [
        _thumb_up(lm),
        _up(lm, INDEX_TIP,  INDEX_PIP,  INDEX_DIP),
        _up(lm, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_DIP),
        _up(lm, RING_TIP,   RING_PIP,   RING_DIP),
        _up(lm, PINKY_TIP,  PINKY_PIP,  PINKY_DIP),
    ]


# ── Gesture classification ────────────────────────────────────────────────────

def _classify(lm) -> Gesture:
    thumb, idx, mid, ring, pinky = _finger_states(lm)

    # FIST — all 4 fingers closed (thumb irrelevant)
    if not idx and not mid and not ring and not pinky:
        return Gesture.FIST

    # OPEN HAND — all 4 fingers AND thumb up
    if idx and mid and ring and pinky and thumb:
        return Gesture.OPEN_HAND

    # ROCK — index + pinky up, middle + ring down (thumb relaxed — don't require it down)
    if idx and pinky and not mid and not ring:
        return Gesture.ROCK

    # TWO FINGERS (Peace) — index + middle up, ring + pinky down (thumb relaxed)
    if idx and mid and not ring and not pinky:
        return Gesture.TWO_FINGERS

    # INDEX ONLY — for swipe
    if idx and not mid and not ring and not pinky:
        return Gesture.INDEX_FINGER

    return Gesture.UNKNOWN


_HOLDABLE = frozenset({Gesture.OPEN_HAND, Gesture.FIST, Gesture.ROCK, Gesture.TWO_FINGERS})


# ── Engine ────────────────────────────────────────────────────────────────────

class GestureEngine(QObject):
    sig_gesture       = Signal(str, str, float, list)  # name, action, conf, fingers
    sig_fired         = Signal(str, str)               # name, action  (once per fire)
    sig_swipe_vol     = Signal(float)                  # volume delta
    sig_hold_progress = Signal(float)                  # 0.0–1.0 fill bar
    sig_cooldown      = Signal(float)                  # 0.0–1.0 remaining cooldown

    def __init__(self, cfg, parent=None):
        super().__init__(parent)

        # Read from config, fall back to module constants
        self._hold_frames    = int(getattr(cfg.gesture, "stabilization_frames", _HOLD_FRAMES))
        self._cooldown_max   = int(getattr(cfg.gesture, "cooldown_frames",       _COOLDOWN_FRAMES))

        # Vote buffer — rolling window of raw classified gestures
        self._vote_buf: deque[Gesture] = deque(maxlen=_VOTE_WINDOW)

        # State machine
        self._phase          = "idle"   # "idle" | "scanning" | "cooldown"
        self._stable_gesture = Gesture.NONE
        self._stable_count   = 0
        self._hold_count     = 0
        self._cooldown_count = 0
        self._last_fired     = Gesture.NONE
        self._hand_present   = False    # True only when a hand is actively detected

        # Swipe
        self._swipe_buf:      deque[float] = deque(maxlen=_SWIPE_WINDOW)
        self._swipe_cooldown  = 0

        # UI throttle — only emit sig_gesture when label actually changes
        self._last_emitted_gesture = Gesture.NONE

    # ── Main entry ────────────────────────────────────────────────────────────

    def on_no_hand(self) -> None:
        """Called every frame when NO hand is detected — resets scan state."""
        self._hand_present = False
        if self._phase != "cooldown":   # don't interrupt active cooldown
            self._reset_scan()
            self._vote_buf.clear()
            self._swipe_buf.clear()
            self._last_emitted_gesture = Gesture.NONE

    def _handle_swipe(self, landmarks, states) -> None:
        _, idx, mid, ring, pinky = states
        if idx and not mid and not ring and not pinky:
            self._swipe_buf.append(landmarks[INDEX_TIP].x)
            if self._swipe_cooldown > 0:
                self._swipe_cooldown -= 1
            elif len(self._swipe_buf) == _SWIPE_WINDOW:
                dx = self._swipe_buf[-1] - self._swipe_buf[0]
                if abs(dx) >= _SWIPE_THRESHOLD:
                    delta = 0.05 if dx > 0 else -0.05
                    self.sig_swipe_vol.emit(delta)
                    log.info("Swipe %s  dx=%.3f", "Vol+" if dx > 0 else "Vol-", dx)
                    self._swipe_buf.clear()
                    self._swipe_cooldown = _SWIPE_COOLDOWN
        else:
            self._swipe_buf.clear()

    def _handle_cooldown(self) -> bool:
        self._cooldown_count -= 1
        remaining = max(0.0, self._cooldown_count / self._cooldown_max)
        self.sig_hold_progress.emit(0.0)
        self.sig_cooldown.emit(remaining)
        if self._cooldown_count <= 0:
            self._phase = "idle"
            self._reset_scan()
            self._last_emitted_gesture = Gesture.NONE
            self.sig_cooldown.emit(0.0)
            log.debug("Cooldown done — idle.")
            return False
        return True

    def _handle_scanning(self, voted: Gesture) -> None:
        if voted == self._stable_gesture:
            self._stable_count += 1
        else:
            self._stable_gesture = voted
            self._stable_count   = 1
            self._hold_count     = 0
            self._phase          = "idle"
            self.sig_hold_progress.emit(0.0)
            return
        if self._stable_count < _STABLE:
            self.sig_hold_progress.emit(0.0)
            return
        self._phase       = "scanning"
        self._hold_count += 1
        self.sig_hold_progress.emit(min(self._hold_count / self._hold_frames, 1.0))
        if self._hold_count >= self._hold_frames:
            self._fire(voted)

    def process_landmarks(self, landmarks) -> None:
        self._hand_present = True
        raw    = _classify(landmarks)
        states = _finger_states(landmarks)

        self._vote_buf.append(raw)
        voted = self._majority_vote()

        if voted != self._last_emitted_gesture:
            self._last_emitted_gesture = voted
            conf = 0.97 if voted in _HOLDABLE else (0.95 if voted == Gesture.INDEX_FINGER else 0.30)
            self.sig_gesture.emit(voted.value, GESTURE_ACTIONS[voted], conf, states)

        self._handle_swipe(landmarks, states)

        if self._phase == "cooldown":
            self._handle_cooldown()
            return

        if voted not in _HOLDABLE:
            self._reset_scan()
            return

        self._handle_scanning(voted)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _majority_vote(self) -> Gesture:
        """Return the gesture that appears most in the vote buffer."""
        if not self._vote_buf:
            return Gesture.UNKNOWN
        counts: dict[Gesture, int] = {}
        for g in self._vote_buf:
            counts[g] = counts.get(g, 0) + 1
        winner = max(counts, key=lambda g: counts[g])
        # Only accept winner if it has clear majority (> half the window)
        if counts[winner] > len(self._vote_buf) // 2:
            return winner
        return Gesture.UNKNOWN

    def _fire(self, gesture: Gesture):
        self._last_fired     = gesture
        self._phase          = "cooldown"
        self._cooldown_count = self._cooldown_max
        self._hold_count     = 0
        self._stable_gesture = Gesture.NONE
        self._stable_count   = 0
        self._vote_buf.clear()
        log.info("Gesture FIRED: %s", gesture.value)
        self.sig_fired.emit(gesture.value, GESTURE_ACTIONS[gesture])
        self.sig_hold_progress.emit(0.0)

    def _reset_scan(self):
        self._stable_gesture = Gesture.NONE
        self._stable_count   = 0
        self._hold_count     = 0
        self._phase          = "idle"
        self.sig_hold_progress.emit(0.0)

    def reset(self):
        """External reset — called by main window if needed."""
        self._phase          = "idle"
        self._cooldown_count = 0
        self._reset_scan()
        self._vote_buf.clear()
        self._swipe_buf.clear()
        self._swipe_cooldown  = 0
        self._last_emitted_gesture = Gesture.NONE
        self.sig_hold_progress.emit(0.0)
        self.sig_cooldown.emit(0.0)

    @property
    def last_fired(self) -> Gesture:
        return self._last_fired
