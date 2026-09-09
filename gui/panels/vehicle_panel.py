"""
gui/panels/vehicle_panel.py
===========================
Vehicle simulator panel: speed, RPM, gear, drive mode, cabin lighting status.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout,
)
from PySide6.QtCore import Qt
from gui.theme import PALETTE as P
from gui.widgets.base_widgets import (
    CardWidget, SectionHeader, CircularGauge,
    MetricTile, GlowProgressBar, SeparatorLine,
)

class VehiclePanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        root.addWidget(SectionHeader("Vehicle Simulator"))
        root.addWidget(self._build_gauges())
        root.addWidget(self._build_vehicle_info())
        root.addWidget(SeparatorLine())
        root.addWidget(SectionHeader("Cabin Ambience"))
        root.addWidget(self._build_cabin_status())

    def _build_gauges(self) -> QWidget:
        card = CardWidget()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        self._speed_gauge = CircularGauge(
            label="Speed", min_val=0, max_val=180,
            unit="km/h", color=P.accent, size=130,
        )
        self._speed_gauge.set_value(0)

        self._rpm_gauge = CircularGauge(
            label="RPM", min_val=0, max_val=8000,
            unit="×1000", color=P.warning, size=130,
        )
        self._rpm_gauge.set_value(0)

        layout.addWidget(self._speed_gauge)
        layout.addWidget(self._rpm_gauge)
        return card

    def _build_vehicle_info(self) -> QWidget:
        card = CardWidget()
        layout = QGridLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        self._gear_tile  = MetricTile("Gear",       "P",       "",    P.accent)
        self._mode_tile  = MetricTile("Drive Mode", "COMFORT", "",    P.success)
        self._temp_tile  = MetricTile("Cabin Temp", "22°C",    "",    P.info)
        self._range_tile = MetricTile("Range",      "420",     "km",  P.warning)

        for tile in [self._gear_tile, self._mode_tile,
                     self._temp_tile, self._range_tile]:
            tile.setFixedHeight(80)

        layout.addWidget(self._gear_tile,  0, 0)
        layout.addWidget(self._mode_tile,  0, 1)
        layout.addWidget(self._temp_tile,  1, 0)
        layout.addWidget(self._range_tile, 1, 1)
        return card

    def _build_cabin_status(self) -> QWidget:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Lighting colour swatch
        swatch_row = QHBoxLayout()
        swatch_lbl = QLabel("AMBIENT COLOR")
        swatch_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 2px;")

        self._color_swatch = QLabel()
        self._color_swatch.setFixedSize(60, 20)
        self._color_swatch.setStyleSheet(f"""
            background-color: {P.mood_calm};
            border-radius: 4px;
            border: 1px solid {P.border_bright};
        """)
        swatch_row.addWidget(swatch_lbl)
        swatch_row.addStretch()
        swatch_row.addWidget(self._color_swatch)
        layout.addLayout(swatch_row)

        # Mood + mode labels
        info_rows = [
            ("MOOD",      "Calm",    "_cabin_mood_lbl"),
            ("LIGHTING",  "Soft Blue", "_cabin_light_lbl"),
        ]
        for key, val, attr in info_rows:
            row = QHBoxLayout()
            k = QLabel(key)
            k.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 2px;")
            v = QLabel(val)
            v.setStyleSheet(f"color: {P.text_primary}; font-size: 11px; font-weight: 600;")
            row.addWidget(k)
            row.addStretch()
            row.addWidget(v)
            layout.addLayout(row)
            setattr(self, attr, v)

        # Intensity bar
        int_row = QHBoxLayout()
        int_lbl = QLabel("INTENSITY")
        int_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 2px;")
        self._intensity_val = QLabel("60%")
        self._intensity_val.setStyleSheet(f"color: {P.text_secondary}; font-size: 10px;")
        int_row.addWidget(int_lbl)
        int_row.addStretch()
        int_row.addWidget(self._intensity_val)
        layout.addLayout(int_row)

        self._intensity_bar = GlowProgressBar(color=P.mood_calm, height=4)
        self._intensity_bar.set_value(0.6)
        layout.addWidget(self._intensity_bar)

        return card

    # ── Public update API ─────────────────────────────────────────────────────

    def update_speed(self, speed: float) -> None:
        self._speed_gauge.set_value(speed)

    def update_rpm(self, rpm: float) -> None:
        self._rpm_gauge.set_value(rpm)

    def update_gear(self, gear: str) -> None:
        self._gear_tile.set_value(gear)

    def update_drive_mode(self, mode: str) -> None:
        self._mode_tile.set_value(mode)

    def update_cabin_lighting(
        self,
        mood: str,
        color: tuple[int, int, int],
        intensity: float,
        description: str,
    ) -> None:
        hex_c = "#{:02X}{:02X}{:02X}".format(*color)
        self._color_swatch.setStyleSheet(f"""
            background-color: {hex_c};
            border-radius: 4px;
            border: 1px solid {P.border_bright};
        """)
        self._cabin_mood_lbl.setText(mood)
        self._cabin_light_lbl.setText(description)
        self._intensity_bar.set_color(hex_c)
        self._intensity_bar.set_value(intensity)
        self._intensity_val.setText(f"{int(intensity * 100)}%")
        self._rpm_gauge.set_color(hex_c)
