"""
gui/panels/ai_panel.py
======================
AI Analysis panel: mood indicator, audio features, system status grid.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont, QRadialGradient
from gui.theme import PALETTE as P
from gui.widgets.base_widgets import (
    CardWidget, SectionHeader, GlowProgressBar,
    MetricTile, StatusBadge, LEDIndicator, SeparatorLine,
)


# ── Mood Orb ──────────────────────────────────────────────────────────────────

class MoodOrb(QWidget):
    """
    A glowing circular orb that changes colour to represent the detected mood.
    The colour transitions smoothly via QTimer interpolation (Phase 9).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(30, 80, 180)   # default: Calm blue
        self._mood  = "CALM"
        self.setFixedSize(100, 100)

    def set_mood(self, mood: str, color: tuple[int, int, int]) -> None:
        self._mood  = mood.upper()
        self._color = QColor(*color)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy, r = self.width() // 2, self.height() // 2, 38

        # Outer glow
        grad = QRadialGradient(cx, cy, r + 20)
        glow = QColor(self._color)
        glow.setAlpha(60)
        grad.setColorAt(0, glow)
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(grad)
        p.drawEllipse(cx - r - 20, cy - r - 20, (r + 20) * 2, (r + 20) * 2)

        # Core orb
        core_grad = QRadialGradient(cx - r // 3, cy - r // 3, r)
        light = QColor(self._color).lighter(160)
        core_grad.setColorAt(0, light)
        core_grad.setColorAt(1, self._color)
        p.setBrush(core_grad)
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Mood text
        p.setPen(QColor(255, 255, 255, 200))
        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        p.drawText(self.rect(), Qt.AlignCenter, self._mood)


# ── AI Panel ──────────────────────────────────────────────────────────────────

class AIPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        root.addWidget(SectionHeader("AI Music Analysis"))
        root.addWidget(self._build_mood_section())
        root.addWidget(self._build_features_section())
        root.addWidget(SeparatorLine())
        root.addWidget(SectionHeader("System Status"))
        root.addWidget(self._build_system_status())

    def _build_mood_section(self) -> QWidget:
        card = CardWidget(accent_color=P.mood_calm)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(16)

        # Mood orb
        self._orb = MoodOrb()
        layout.addWidget(self._orb)

        # Mood details
        details = QVBoxLayout()
        details.setSpacing(4)

        mood_title = QLabel("DETECTED MOOD")
        mood_title.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 2px;")

        self._mood_name_lbl = QLabel("Calm")
        self._mood_name_lbl.setStyleSheet(f"""
            color: {P.mood_calm};
            font-size: 22px;
            font-weight: 700;
        """)

        self._mood_desc_lbl = QLabel("Soft Blue — Calm & Peaceful")
        self._mood_desc_lbl.setStyleSheet(f"color: {P.text_secondary}; font-size: 10px;")
        self._mood_desc_lbl.setWordWrap(True)

        # Mood confidence bar
        conf_lbl = QLabel("MOOD CONFIDENCE")
        conf_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 1px;")
        self._mood_conf_bar = GlowProgressBar(color=P.mood_calm, height=4)
        self._mood_conf_bar.set_value(0.82)

        details.addWidget(mood_title)
        details.addWidget(self._mood_name_lbl)
        details.addWidget(self._mood_desc_lbl)
        details.addWidget(conf_lbl)
        details.addWidget(self._mood_conf_bar)

        layout.addLayout(details, 1)
        return card

    def _build_features_section(self) -> QWidget:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        feat_title = QLabel("AUDIO FEATURES")
        feat_title.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 2px;")
        layout.addWidget(feat_title)

        # Metric tiles grid
        grid = QGridLayout()
        grid.setSpacing(6)

        self._metrics: dict[str, MetricTile] = {}
        tiles = [
            ("BPM",       "128",   "",    P.accent),
            ("Energy",    "0.74",  "",    P.warning),
            ("Tempo",     "128",   "bpm", P.success),
            ("ZCR",       "0.08",  "",    P.info),
            ("Centroid",  "2.4k",  "Hz",  P.accent_light),
            ("RMS",       "0.12",  "",    P.mood_happy),
        ]
        for i, (label, value, unit, color) in enumerate(tiles):
            tile = MetricTile(label, value, unit, color)
            tile.setFixedHeight(72)
            grid.addWidget(tile, i // 3, i % 3)
            self._metrics[label] = tile

        layout.addLayout(grid)

        # Feature bars
        bars_lbl = QLabel("FEATURE LEVELS")
        bars_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 2px; margin-top: 4px;")
        layout.addWidget(bars_lbl)

        self._feature_bars: dict[str, GlowProgressBar] = {}
        for feat, val, color in [
            ("MFCC",      0.65, P.accent),
            ("Chroma",    0.72, P.success),
            ("Bandwidth", 0.48, P.warning),
        ]:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(feat)
            lbl.setFixedWidth(72)
            lbl.setStyleSheet(f"color: {P.text_secondary}; font-size: 9px;")
            bar = GlowProgressBar(color=color, height=4)
            bar.set_value(val)
            val_lbl = QLabel(f"{int(val*100)}%")
            val_lbl.setFixedWidth(30)
            val_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px;")
            row.addWidget(lbl)
            row.addWidget(bar)
            row.addWidget(val_lbl)
            layout.addLayout(row)
            self._feature_bars[feat] = bar

        return card

    def _build_system_status(self) -> QWidget:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        components = [
            ("Camera",              "ACTIVE"),
            ("Hand Tracking",       "ACTIVE"),
            ("Gesture Recognition", "ACTIVE"),
            ("Audio Analysis",      "ACTIVE"),
            ("Mood Classification", "ACTIVE"),
            ("Cabin Engine",        "ACTIVE"),
        ]

        self._status_badges: dict[str, StatusBadge] = {}
        self._status_leds:   dict[str, LEDIndicator] = {}

        for name, status in components:
            row = QHBoxLayout()
            row.setSpacing(8)

            led = LEDIndicator(color=P.success, size=8)
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(f"color: {P.text_secondary}; font-size: 10px;")
            badge = StatusBadge(status)
            badge.setFixedWidth(90)

            row.addWidget(led)
            row.addWidget(name_lbl)
            row.addStretch()
            row.addWidget(badge)
            layout.addLayout(row)

            self._status_badges[name] = badge
            self._status_leds[name]   = led

        return card

    # ── Public update API ─────────────────────────────────────────────────────

    def update_mood(
        self,
        mood: str,
        description: str,
        color: tuple[int, int, int],
        confidence: float,
    ) -> None:
        hex_color = "#{:02X}{:02X}{:02X}".format(*color)
        self._orb.set_mood(mood, color)
        self._mood_name_lbl.setText(mood)
        self._mood_name_lbl.setStyleSheet(f"color: {hex_color}; font-size: 22px; font-weight: 700;")
        self._mood_desc_lbl.setText(description)
        self._mood_conf_bar.set_color(hex_color)
        self._mood_conf_bar.set_value(confidence)

    def update_metric(self, name: str, value: str) -> None:
        if name in self._metrics:
            self._metrics[name].set_value(value)

    def update_feature_bar(self, name: str, value: float) -> None:
        if name in self._feature_bars:
            self._feature_bars[name].set_value(value)

    def set_component_status(self, name: str, status: str) -> None:
        if name in self._status_badges:
            self._status_badges[name].set_status(status)
            color = P.success if status == "ACTIVE" else P.error
            self._status_leds[name].set_color(color)
