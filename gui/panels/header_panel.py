"""
gui/panels/header_panel.py
==========================
Top header bar: app title, live clock, and quick-status indicators.
"""

from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from datetime import datetime, timezone
from gui.theme import PALETTE as P
from gui.widgets.base_widgets import LEDIndicator


class HeaderPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(64)
        self.setStyleSheet(f"""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {P.bg_deep},
                stop:0.5 #0F0F20,
                stop:1 {P.bg_deep}
            );
            border-bottom: 1px solid {P.border};
        """)
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        # ── Left: logo + title ────────────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(1)

        title = QLabel("AI CABIN EXPERIENCE")
        title.setStyleSheet(f"""
            color: {P.text_accent};
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 4px;
        """)

        subtitle = QLabel("Gesture-Controlled Automotive Infotainment System")
        subtitle.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 1px;")

        left.addWidget(title)
        left.addWidget(subtitle)

        # ── Centre: status indicators ─────────────────────────────────────────
        centre = QHBoxLayout()
        centre.setSpacing(16)
        centre.setAlignment(Qt.AlignCenter)

        self._status_items: dict[str, tuple[LEDIndicator, QLabel]] = {}
        for name, color in [
            ("CAMERA",  P.success),
            ("GESTURE", P.success),
            ("AUDIO",   P.success),
            ("AI",      P.success),
        ]:
            row = QHBoxLayout()
            row.setSpacing(5)
            led = LEDIndicator(color=color, size=8)
            lbl = QLabel(name)
            lbl.setStyleSheet(f"color: {P.text_secondary}; font-size: 9px; letter-spacing: 1px;")
            row.addWidget(led)
            row.addWidget(lbl)
            w = QWidget()
            w.setLayout(row)
            centre.addWidget(w)
            self._status_items[name] = (led, lbl)

        # ── Right: clock ──────────────────────────────────────────────────────
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._clock_lbl = QLabel()
        self._clock_lbl.setStyleSheet(f"""
            color: {P.text_primary};
            font-size: 20px;
            font-weight: 300;
            letter-spacing: 2px;
        """)
        self._date_lbl = QLabel()
        self._date_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px;")
        self._date_lbl.setAlignment(Qt.AlignRight)

        right.addWidget(self._clock_lbl)
        right.addWidget(self._date_lbl)

        layout.addLayout(left, 2)
        layout.addLayout(centre, 3)
        layout.addLayout(right, 2)

        # Clock timer
        self._tick()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

    def _tick(self) -> None:
        now = datetime.now(timezone.utc).astimezone()
        self._clock_lbl.setText(now.strftime("%H:%M:%S"))
        self._date_lbl.setText(now.strftime("%A, %d %B %Y"))

    def set_component_status(self, name: str, active: bool) -> None:
        if name in self._status_items:
            led, _ = self._status_items[name]
            led.set_color(P.success if active else P.error)
