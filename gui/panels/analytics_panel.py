"""
gui/panels/analytics_panel.py  —  Phase 16
============================================
AI Engineering Analytics Dashboard.
Shows real-time system metrics: FPS, latency, gesture stats,
mood confidence, songs played, and the system architecture flow.
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
)
from PySide6.QtCore import Qt
from gui.theme import PALETTE as P
from gui.widgets.base_widgets import (
    CardWidget, SectionHeader, MetricTile, GlowProgressBar, SeparatorLine,
)

class AnalyticsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gesture_count = 0
        self._songs_played  = 0
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        root.addWidget(SectionHeader("AI Analytics Dashboard"))
        root.addWidget(self._build_metrics())
        root.addWidget(SeparatorLine())
        root.addWidget(SectionHeader("System Architecture"))
        root.addWidget(self._build_architecture())

    def _build_metrics(self):
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        grid = QGridLayout()
        grid.setSpacing(4)

        self._tiles: dict[str, MetricTile] = {}
        specs = [
            ("FPS",      "--", "",   P.success),
            ("Mood",     "--", "",   P.mood_happy),
            ("BPM",      "--", "",   P.warning),
            ("Energy",   "--", "",   P.info),
            ("Gestures", "0",  "",   P.accent_light),
            ("Songs",    "0",  "",   P.success),
        ]
        for i, (label, val, unit, color) in enumerate(specs):
            tile = MetricTile(label, val, unit, color)
            tile.setFixedHeight(58)
            grid.addWidget(tile, i // 3, i % 3)
            self._tiles[label] = tile

        # Confidence — full-width row below grid
        conf_row2 = QHBoxLayout()
        conf_row2.setSpacing(8)
        conf_lbl2 = QLabel("GESTURE CONFIDENCE")
        conf_lbl2.setStyleSheet(f"color:{P.text_muted};font-size:9px;letter-spacing:1px;")
        self._conf_pct_lbl = QLabel("-- %")
        self._conf_pct_lbl.setStyleSheet(f"color:{P.accent};font-size:14px;font-weight:700;")
        self._conf_pct_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        conf_row2.addWidget(conf_lbl2)
        conf_row2.addStretch()
        conf_row2.addWidget(self._conf_pct_lbl)
        layout.addLayout(conf_row2)

        layout.addLayout(grid)

        # Confidence progress bar
        self._conf_bar = GlowProgressBar(color=P.accent, height=4)
        layout.addWidget(self._conf_bar)

        return card

    def _build_architecture(self):
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        steps = [
            ("Camera",              P.info),
            ("Computer Vision",     P.info),
            ("Gesture Recognition", P.accent),
            ("Command Engine",      P.accent),
            ("Infotainment",        P.success),
            ("Audio Analysis",      P.warning),
            ("Mood Classification", P.warning),
            ("Cabin Ambience",      P.mood_energetic),
            ("Digital Car Interior",P.mood_energetic),
        ]
        self._arch_labels: dict[str, QLabel] = {}
        for i, (name, color) in enumerate(steps):
            row = QHBoxLayout()
            row.setSpacing(6)

            dot = QLabel("●")
            dot.setStyleSheet(f"color:{color};font-size:10px;")
            dot.setFixedWidth(14)

            lbl = QLabel(name)
            lbl.setStyleSheet(f"color:{P.text_secondary};font-size:9px;")

            status = QLabel("ACTIVE")
            status.setStyleSheet(f"""
                color:{color}; background:{color}22;
                border:1px solid {color}44; border-radius:5px;
                padding:1px 5px; font-size:7px; font-weight:700;
            """)
            status.setFixedWidth(46)

            row.addWidget(dot)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(status)
            layout.addLayout(row)
            self._arch_labels[name] = status

            if i < len(steps) - 1:
                arrow = QLabel("  |")
                arrow.setStyleSheet(f"color:{P.border_bright};font-size:8px;")
                arrow.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(arrow)

        return card

    # ── Public API ────────────────────────────────────────────────────────────

    def update_fps(self, fps: float):
        self._tiles["FPS"].set_value(f"{fps:.1f}")

    def update_confidence(self, conf: float):
        self._conf_pct_lbl.setText(f"{int(conf * 100)} %")
        self._conf_bar.set_value(conf)

    def update_mood(self, mood: str):
        self._tiles["Mood"].set_value(mood[:8])

    def update_bpm(self, bpm: float):
        self._tiles["BPM"].set_value(str(int(bpm)))

    def update_energy(self, energy: float):
        self._tiles["Energy"].set_value(f"{energy:.3f}")

    def increment_gesture(self):
        self._gesture_count += 1
        self._tiles["Gestures"].set_value(str(self._gesture_count))

    def increment_songs(self):
        self._songs_played += 1
        self._tiles["Songs"].set_value(str(self._songs_played))

    def update_latency(self, ms: float):
        pass  # Latency tile removed

    def set_component_active(self, name: str, active: bool):
        if name in self._arch_labels:
            lbl = self._arch_labels[name]
            color = P.success if active else P.error
            lbl.setText("ACTIVE" if active else "OFFLINE")
            lbl.setStyleSheet(f"""
                color:{color}; background:{color}22;
                border:1px solid {color}44; border-radius:6px;
                padding:1px 6px; font-size:8px; font-weight:700;
            """)
