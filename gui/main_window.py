"""
gui/main_window.py  —  Phases 3-17 (fully wired)
==================================================
Main infotainment window.
All panels are connected to real engines via Qt signals.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QScrollArea, QTabWidget,
)
from PySide6.QtCore import Qt, Slot
from gui.theme  import PALETTE as P, get_stylesheet
from gui.panels.header_panel     import HeaderPanel
from gui.panels.music_panel      import MusicPanel
from gui.panels.camera_panel     import CameraPanel
from gui.panels.ai_panel         import AIPanel
from gui.panels.vehicle_panel    import VehiclePanel
from gui.panels.visualizer_panel import VisualizerPanel
from gui.panels.analytics_panel  import AnalyticsPanel
from gui.panels.gesture_info_panel import GestureInfoPanel
from core.constants import MOOD_DESCRIPTIONS, Mood
from core.logger    import get_logger

log = get_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, cfg=None):
        super().__init__()
        self._cfg = cfg
        self._setup_window()
        self._build_ui()
        log.info("MainWindow ready.")

    def _setup_window(self):
        self.setWindowTitle("AI Cabin Experience — Infotainment System")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(get_stylesheet())

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background:{P.bg_base};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header = HeaderPanel()
        root.addWidget(self._header)

        body = QWidget()
        body.setStyleSheet(f"background:{P.bg_base};")
        bl = QHBoxLayout(body)
        bl.setContentsMargins(10, 10, 10, 10)
        bl.setSpacing(10)

        # ── Left column ───────────────────────────────────────────────────────
        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        self._music_panel   = MusicPanel()
        self._vehicle_panel = VehiclePanel()   # kept for wiring, hidden from UI
        self._vehicle_panel.hide()
        self._gesture_info_panel = GestureInfoPanel()
        left_col.addWidget(self._music_panel,        3)
        left_col.addWidget(self._gesture_info_panel, 2)
        left_w = QWidget()
        left_w.setLayout(left_col)
        left_w.setFixedWidth(320)

        # ── Centre column ─────────────────────────────────────────────────────
        centre_col = QVBoxLayout()
        centre_col.setSpacing(8)
        self._camera_panel = CameraPanel()
        self._viz_panel    = VisualizerPanel()
        centre_col.addWidget(self._camera_panel, 3)
        centre_col.addWidget(self._viz_panel,    1)
        centre_w = QWidget()
        centre_w.setLayout(centre_col)
        centre_w.setMinimumWidth(380)

        # ── Right column ──────────────────────────────────────────────────────
        right_tabs = QTabWidget()
        right_tabs.setMinimumWidth(380)
        right_tabs.setMaximumWidth(420)
        right_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {P.border};
                border-radius: 8px;
                background: {P.bg_base};
            }}
            QTabBar::tab {{
                background: {P.bg_surface};
                color: {P.text_muted};
                padding: 6px 14px;
                font-size: 10px;
                border-radius: 4px;
                margin: 2px;
            }}
            QTabBar::tab:selected {{
                background: {P.accent_dim};
                color: {P.text_accent};
            }}
        """)

        ai_scroll = QScrollArea()
        ai_scroll.setWidgetResizable(True)
        ai_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        ai_scroll.setStyleSheet("border:none;background:transparent;")
        self._ai_panel = AIPanel()
        ai_scroll.setWidget(self._ai_panel)

        analytics_scroll = QScrollArea()
        analytics_scroll.setWidgetResizable(True)
        analytics_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        analytics_scroll.setStyleSheet("border:none;background:transparent;")
        self._analytics_panel = AnalyticsPanel()
        analytics_scroll.setWidget(self._analytics_panel)

        right_tabs.addTab(ai_scroll,        "AI Analysis")
        right_tabs.addTab(analytics_scroll, "Analytics")

        bl.addWidget(left_w)
        bl.addWidget(centre_w, 1)
        bl.addWidget(right_tabs)
        root.addWidget(body, 1)

    # ── Engine wiring ─────────────────────────────────────────────────────────

    def wire_music_engine(self, engine):
        engine.sig_song_changed.connect(self._on_song_changed)
        engine.sig_progress.connect(self._music_panel.update_progress)
        engine.sig_state_changed.connect(self._on_state_changed)
        engine.sig_volume_changed.connect(self._music_panel.set_volume)
        engine.sig_playlist_ready.connect(self._music_panel.set_playlist)
        engine.sig_playlist_updated.connect(self._music_panel.set_playlist)

        self._music_panel.sig_play_pause.connect(engine.pause_resume)
        self._music_panel.sig_next.connect(engine.next_song)
        self._music_panel.sig_previous.connect(engine.previous_song)
        self._music_panel.sig_shuffle.connect(engine.toggle_shuffle)
        self._music_panel.sig_repeat.connect(engine.toggle_repeat)
        self._music_panel.sig_volume.connect(engine.set_volume)
        self._music_panel.sig_seek.connect(engine.seek)
        self._music_panel.sig_seek_delta.connect(engine.seek_delta)
        self._music_panel.sig_song_select.connect(engine.select_song)
        self._music_panel.sig_add_song.connect(engine.add_song)
        self._music_engine = engine

    def wire_camera_engine(self, engine):
        engine.sig_frame.connect(self._camera_panel.update_frame)
        engine.sig_fps.connect(self._on_fps)
        engine.sig_hand_detected.connect(self._camera_panel.set_hand_detected)
        engine.sig_error.connect(lambda e: log.warning("Camera: %s", e))
        self._camera_engine = engine

    def wire_gesture_engine(self, engine):
        engine.sig_gesture.connect(self._on_gesture)
        engine.sig_fired.connect(self._dispatch_gesture)
        engine.sig_swipe_vol.connect(self._on_swipe_vol)
        engine.sig_hold_progress.connect(self._camera_panel.update_hold_progress)
        engine.sig_cooldown.connect(self._camera_panel.update_cooldown)
        self._gesture_engine = engine
        if hasattr(self, "_camera_engine"):
            self._camera_engine.sig_no_hand.connect(engine.on_no_hand)

    def wire_audio_engine(self, engine):
        engine.sig_features.connect(self._on_features)
        engine.sig_bpm.connect(self._on_bpm)
        engine.sig_energy.connect(self._on_energy)

    def wire_mood_engine(self, engine):
        engine.sig_mood.connect(self._on_mood)

    def wire_cabin_engine(self, engine):
        engine.sig_color.connect(self._on_cabin_color)
        engine.sig_mood_changed.connect(self._on_cabin_mood)

    def wire_vehicle_engine(self, engine):
        engine.sig_vehicle.connect(self._on_vehicle)

    def wire_car_window(self, car_win):
        self._car_win = car_win

    # ── Slots ─────────────────────────────────────────────────────────────────

    @Slot(int, str, float)
    def _on_song_changed(self, index: int, name: str, duration: float):
        self._current_song = name
        self._music_panel.update_song(name, "")
        self._music_panel.set_current_playlist_row(index)
        self._analytics_panel.increment_songs()
        self._header.set_component_status("AUDIO", True)
        if hasattr(self, "_audio_engine"):
            self._audio_engine.set_song(self._music_engine.current_path)
        if hasattr(self, "_car_win"):
            self._car_win.update_state(
                song=name,
                mood=getattr(self, "_current_mood", "Calm"),
                speed=0.0,
                drive_mode="COMFORT",
                volume=self._music_engine.volume,
                progress=0.0,
            )

    @Slot(str)
    def _on_state_changed(self, state: str):
        self._music_panel.set_playing(state == "PLAYING")

    @Slot(float)
    def _on_fps(self, fps: float):
        self._camera_panel.update_fps(fps)
        self._analytics_panel.update_fps(fps)

    @Slot(str, str, float, list)
    def _on_gesture(self, name: str, action: str, conf: float, fingers: list):
        self._camera_panel.update_gesture(name, action, conf, fingers)
        self._analytics_panel.update_confidence(conf)

    @Slot(float)
    def _on_swipe_vol(self, delta: float):
        if not hasattr(self, "_music_engine"):
            return
        m = self._music_engine
        new_vol = max(0.0, min(1.0, m.volume + delta))
        m.set_volume(new_vol)
        direction = "Up" if delta > 0 else "Down"
        log.debug("Swipe volume %s -> %.0f%%", direction, new_vol * 100)

    def _dispatch_gesture(self, name: str, action: str = ""):
        if not hasattr(self, "_music_engine"):
            return
        self._analytics_panel.increment_gesture()
        m = self._music_engine
        if name == "Open Hand":
            m.play()                   # resumes / starts, clears hard_stopped
        elif name == "Fist":
            m.stop()                   # hard stop — stays stopped
        elif name == "Rock":
            m.next_song()              # clears hard_stopped, plays next
        elif name == "Two Fingers":
            m.previous_song()          # clears hard_stopped, plays previous

    @Slot(dict)
    def _on_features(self, features: dict):
        self._viz_panel.update_features(features)
        bpm    = features.get("bpm",    120)
        energy = features.get("energy", 0.05)
        self._ai_panel.update_metric("BPM",       str(int(bpm)))
        self._ai_panel.update_metric("Energy",    f"{energy:.2f}")
        self._ai_panel.update_metric("Tempo",     str(int(bpm)))
        self._ai_panel.update_metric("ZCR",       f"{features.get('zcr',0):.2f}")
        self._ai_panel.update_metric("Centroid",  f"{features.get('centroid',0)/1000:.1f}k")
        self._ai_panel.update_metric("RMS",       f"{features.get('rms',0):.2f}")
        self._ai_panel.update_feature_bar("MFCC",      min(abs(features.get("mfcc_mean",0))/20,1))
        self._ai_panel.update_feature_bar("Chroma",    features.get("chroma_mean",0))
        self._ai_panel.update_feature_bar("Bandwidth", min(features.get("bandwidth",0)/5000,1))
        if hasattr(self, "_mood_engine"):
            self._mood_engine.classify(features)
        if hasattr(self, "_vehicle_engine"):
            self._vehicle_engine.set_energy(energy)

    @Slot(float)
    def _on_bpm(self, bpm: float):
        self._music_panel.update_bpm(bpm)
        self._analytics_panel.update_bpm(bpm)

    @Slot(float)
    def _on_energy(self, energy: float):
        self._analytics_panel.update_energy(energy)

    @Slot(str, float, tuple)
    def _on_mood(self, mood: str, conf: float, color: tuple):
        hex_c = "#{:02X}{:02X}{:02X}".format(*color)
        desc  = MOOD_DESCRIPTIONS.get(
            next((m for m in Mood if m.value == mood), Mood.UNKNOWN), "")
        self._ai_panel.update_mood(mood, desc, color, conf)
        self._music_panel.update_mood(mood, hex_c)
        self._analytics_panel.update_mood(mood)
        # Update playlist row mood tag
        if hasattr(self, "_music_engine"):
            self._music_panel.update_song_mood(self._music_engine._index, mood)
        if hasattr(self, "_cabin_engine"):
            self._cabin_engine.set_mood(mood)
        if hasattr(self, "_vehicle_engine"):
            self._vehicle_engine.set_mood(mood)

    @Slot(int, int, int, float)
    def _on_cabin_color(self, r: int, g: int, b: int, intensity: float):
        color = (r, g, b)
        self._vehicle_panel.update_cabin_lighting(
            getattr(self, "_current_mood", "Calm"),
            color, intensity,
            getattr(self, "_current_mood_desc", ""),
        )
        self._viz_panel.set_ambient_color(r, g, b)
        if hasattr(self, "_car_win"):
            self._car_win.set_ambient_color(color)

    @Slot(str, str)
    def _on_cabin_mood(self, mood: str, desc: str):
        self._current_mood      = mood
        self._current_mood_desc = desc
        if hasattr(self, "_car_win"):
            self._car_win.update_state(
                song=getattr(self, "_current_song", ""),
                mood=mood,
                speed=0.0,
                drive_mode="COMFORT",
                volume=getattr(self, "_music_engine", None) and self._music_engine.volume or 0.6,
                progress=0.0,
            )

    @Slot(float, float, str, str, bool)
    def _on_vehicle(self, speed, rpm, gear, mode, ignition):
        self._vehicle_panel.update_speed(speed)
        self._vehicle_panel.update_rpm(rpm)
        self._vehicle_panel.update_gear(gear)
        self._vehicle_panel.update_drive_mode(mode)
        if hasattr(self, "_car_win"):
            self._car_win.update_state(
                song=getattr(self, "_current_song", ""),
                mood=getattr(self, "_current_mood", "Calm"),
                speed=speed,
                drive_mode=mode,
                volume=getattr(self, "_music_engine", None) and
                       self._music_engine.volume or 0.6,
                progress=0.0,
            )

    # ── Store engine refs for cross-wiring ────────────────────────────────────

    def set_audio_engine(self, e):  self._audio_engine   = e
    def set_mood_engine(self, e):   self._mood_engine     = e
    def set_cabin_engine(self, e):  self._cabin_engine    = e
    def set_vehicle_engine(self, e):self._vehicle_engine  = e

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def music_panel(self):    return self._music_panel
    @property
    def camera_panel(self):   return self._camera_panel
    @property
    def ai_panel(self):       return self._ai_panel
    @property
    def vehicle_panel(self):  return self._vehicle_panel
    @property
    def analytics_panel(self):return self._analytics_panel
    @property
    def viz_panel(self):      return self._viz_panel
    @property
    def header(self):         return self._header
