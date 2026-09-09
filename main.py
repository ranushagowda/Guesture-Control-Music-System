"""
main.py
=======
AI-Powered Gesture-Controlled Automotive Infotainment & Adaptive Cabin System
COMPLETE — Phases 1-17

Run
---
    python main.py
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── 1. Logging ────────────────────────────────────────────────────────────────
from core.logger import setup_logging, get_logger
setup_logging(level="INFO", log_to_file=True, log_dir=str(ROOT / "logs"))
log = get_logger(__name__)

# ── 2. Configuration ──────────────────────────────────────────────────────────
from config.config_manager import get_config
try:
    cfg = get_config()
    log.info("Config: %s v%s", cfg.app.name, cfg.app.version)
except Exception as exc:
    log.critical("Config failed: %s", exc)
    sys.exit(1)

# ── 3. Diagnostics ────────────────────────────────────────────────────────────
from utils.system_info import run_diagnostics
report = run_diagnostics()
if not report.ok:
    log.critical("Diagnostics failed.")
    sys.exit(1)

# ── 4. Qt Application ─────────────────────────────────────────────────────────
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)
app.setApplicationName("AI Cabin Experience")
app.setApplicationVersion("1.0.0")

# ── 5. Lock Screen ────────────────────────────────────────────────────────────
from gui.lock_screen import LockScreen

lock = LockScreen()

def _launch_dashboard():
    lock.close()

    # ── Windows ───────────────────────────────────────────────────────────────
    from gui.main_window import MainWindow
    from gui.car_window  import CarWindow

    main_win = MainWindow(cfg)
    car_win  = CarWindow()
    car_win.move(main_win.x() + main_win.width() + 8, main_win.y())
    main_win.wire_car_window(car_win)

    # ── Music Engine ──────────────────────────────────────────────────────────
    from engines.music_engine import MusicEngine
    music_engine = MusicEngine(cfg)
    main_win.wire_music_engine(music_engine)

    # ── Camera Engine ─────────────────────────────────────────────────────────
    from engines.camera_engine import CameraEngine
    camera_engine = CameraEngine(cfg)
    main_win.wire_camera_engine(camera_engine)

    # ── Gesture Engine ────────────────────────────────────────────────────────
    from engines.gesture_engine import GestureEngine
    gesture_engine = GestureEngine(cfg)
    camera_engine.sig_landmarks.connect(gesture_engine.process_landmarks)
    camera_engine.sig_no_hand.connect(gesture_engine.on_no_hand)
    main_win.wire_gesture_engine(gesture_engine)

    # ── Audio Engine ──────────────────────────────────────────────────────────
    from engines.audio_engine import AudioEngine
    audio_engine = AudioEngine(cfg)
    main_win.wire_audio_engine(audio_engine)
    main_win.set_audio_engine(audio_engine)

    # ── Mood Engine ───────────────────────────────────────────────────────────
    from engines.mood_engine import MoodEngine
    mood_engine = MoodEngine(cfg)
    main_win.wire_mood_engine(mood_engine)
    main_win.set_mood_engine(mood_engine)

    # ── Cabin Engine ──────────────────────────────────────────────────────────
    from engines.cabin_engine import CabinEngine
    cabin_engine = CabinEngine(cfg)
    main_win.wire_cabin_engine(cabin_engine)
    main_win.set_cabin_engine(cabin_engine)

    # ── Vehicle Engine ────────────────────────────────────────────────────────
    from engines.vehicle_engine import VehicleEngine
    vehicle_engine = VehicleEngine(cfg)
    main_win.wire_vehicle_engine(vehicle_engine)
    main_win.set_vehicle_engine(vehicle_engine)

    # ── Cross-wiring ──────────────────────────────────────────────────────────
    def _on_song_changed(_index, name, _duration):
        audio_engine.set_song(music_engine.current_path)
        log.info("Now playing: %s", name)
    music_engine.sig_song_changed.connect(_on_song_changed)

    def _on_cabin_color(r, g, b, _intensity):
        car_win.set_ambient_color((r, g, b))
    cabin_engine.sig_color.connect(_on_cabin_color)

    def _on_vehicle(speed, _rpm, _gear, mode, _ignition):
        car_win.update_state(
            song=getattr(music_engine, "_songs", [None])[
                getattr(music_engine, "_index", 0)
            ].stem if getattr(music_engine, "_songs", []) else "",
            mood=getattr(cabin_engine, "_mood",
                         type("", (), {"value": "Calm"})()).value
                 if hasattr(cabin_engine._mood, "value") else "Calm",
            speed=speed,
            drive_mode=mode,
            volume=music_engine.volume,
        )
    vehicle_engine.sig_vehicle.connect(_on_vehicle)

    # ── Start ─────────────────────────────────────────────────────────────────
    main_win.show()
    car_win.show()
    music_engine.load_library()
    camera_engine.start()
    audio_engine.start()

    log.info("=" * 60)
    log.info("  AI CABIN EXPERIENCE — ALL SYSTEMS ACTIVE")
    log.info("=" * 60)

    # Keep references alive
    app._refs = (main_win, car_win, music_engine, camera_engine,
                 gesture_engine, audio_engine, mood_engine,
                 cabin_engine, vehicle_engine)

lock.sig_unlocked.connect(_launch_dashboard)
lock.show()

sys.exit(app.exec())
