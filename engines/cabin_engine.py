"""
engines/cabin_engine.py  —  Phase 9
=====================================
Adaptive Cabin Ambience Engine.

Receives a mood → looks up target RGB → smoothly interpolates
the current cabin colour over N steps at ~60 fps.

Emits
-----
sig_color(r, g, b, intensity)   — every transition tick
sig_mood_changed(mood, desc)
"""
from __future__ import annotations
from PySide6.QtCore import QObject, Signal, QTimer
from core.constants import Mood, MOOD_COLORS, MOOD_DESCRIPTIONS
from core.logger    import get_logger

log = get_logger(__name__)


class CabinEngine(QObject):
    sig_color        = Signal(int, int, int, float)   # r, g, b, intensity
    sig_mood_changed = Signal(str, str)               # mood_name, description

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self._cfg       = cfg
        self._current   = [30.0, 80.0, 180.0]
        self._target    = [30.0, 80.0, 180.0]
        self._step      = [0.0, 0.0, 0.0]
        self._intensity = float(cfg.cabin.default_intensity)
        self._steps_left= 0
        self._mood      = Mood.CALM
        self._active    = False   # only emit after first mood is set

        self._timer = QTimer(self)
        self._timer.setInterval(cfg.cabin.transition_interval_ms)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_mood(self, mood_name: str):
        try:
            mood = Mood(mood_name)
        except ValueError:
            mood = Mood.UNKNOWN

        self._mood   = mood
        self._active = True
        target_rgb   = MOOD_COLORS.get(mood, (60, 60, 80))
        self._target = [float(c) for c in target_rgb]
        steps        = self._cfg.cabin.transition_steps

        for i in range(3):
            self._step[i] = (self._target[i] - self._current[i]) / max(steps, 1)
        self._steps_left = steps

        desc = MOOD_DESCRIPTIONS.get(mood, "")
        self.sig_mood_changed.emit(mood.value, desc)
        log.debug("Cabin mood → %s", mood.value)

    def set_intensity(self, v: float):
        self._intensity = max(0.0, min(1.0, v))

    def _tick(self):
        if not self._active:
            return
        if self._steps_left > 0:
            for i in range(3):
                self._current[i] += self._step[i]
            self._steps_left -= 1
        else:
            self._current = list(self._target)

        r, g, b = [max(0, min(255, int(c))) for c in self._current]
        self.sig_color.emit(r, g, b, self._intensity)

    @property
    def current_color(self) -> tuple[int, int, int]:
        return tuple(max(0, min(255, int(c))) for c in self._current)
