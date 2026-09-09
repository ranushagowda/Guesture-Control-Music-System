"""
engines/vehicle_engine.py  —  Phase 14
========================================
Vehicle simulator.
Generates plausible speed / RPM / gear / drive-mode values
that react to the current music energy and mood.

Emits
-----
sig_vehicle(speed, rpm, gear, drive_mode, ignition)
"""
from __future__ import annotations
import math, random
from PySide6.QtCore import QObject, Signal, QTimer
from core.logger import get_logger
log = get_logger(__name__)

_GEAR_THRESHOLDS = [0, 20, 45, 75, 110, 145]   # km/h boundaries


def _speed_to_gear(speed: float) -> str:
    if speed < 5:
        return "P"
    for i, threshold in enumerate(_GEAR_THRESHOLDS):
        if speed < threshold:
            return str(i)
    return "6"


class VehicleEngine(QObject):
    sig_vehicle = Signal(float, float, str, str, bool)
    # speed, rpm, gear, drive_mode, ignition

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self._cfg        = cfg
        self._speed      = 0.0
        self._rpm        = 800.0
        self._energy     = 0.05
        self._mood       = "Calm"
        self._drive_mode = cfg.vehicle.default_drive_mode
        self._ignition   = True
        self._t          = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(cfg.vehicle.update_interval_ms)
        self._timer.timeout.connect(self._tick)
        # Timer starts only when music is playing

    def set_energy(self, energy: float):
        self._energy = energy
        if not self._timer.isActive():
            self._timer.start()

    def set_mood(self, mood: str):
        self._mood = mood
        # Auto-select drive mode from mood
        mode_map = {
            "Energetic": "SPORT+",
            "Happy":     "SPORT",
            "Calm":      "COMFORT",
            "Relaxed":   "ECO",
            "Sad":       "ECO",
            "Focus":     "COMFORT",
        }
        self._drive_mode = mode_map.get(mood, "COMFORT")

    def _tick(self):
        self._t += 0.5
        # Base speed oscillates with energy influence
        energy_boost = self._energy * 80
        base_speed   = 55 + energy_boost
        self._speed  = base_speed + 25 * math.sin(self._t * 0.18) + random.uniform(-2, 2)
        self._speed  = max(0.0, min(self._cfg.vehicle.max_speed, self._speed))

        # RPM proportional to speed + energy
        self._rpm = 800 + (self._speed / self._cfg.vehicle.max_speed) * 6000
        self._rpm += self._energy * 1000 + random.uniform(-100, 100)
        self._rpm = max(800, min(self._cfg.vehicle.max_rpm, self._rpm))

        gear = _speed_to_gear(self._speed)
        self.sig_vehicle.emit(
            self._speed, self._rpm, gear, self._drive_mode, self._ignition
        )
