"""
gui/widgets/base_widgets.py
===========================
Reusable custom Qt widgets used across all panels.

Widgets
-------
- CardWidget          : dark rounded card container
- SectionHeader       : labelled divider with accent line
- StatusBadge         : coloured pill badge (ACTIVE / ERROR / etc.)
- LEDIndicator        : small circular status LED
- MetricTile          : value + label tile for dashboards
- GlowProgressBar     : progress bar with accent glow
- CircularGauge       : arc-style gauge (speed, RPM, volume)
- SeparatorLine       : thin horizontal rule
"""

from __future__ import annotations
import math
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont,
    QLinearGradient, QPainterPath,
)
from gui.theme import PALETTE as P


# ── CardWidget ────────────────────────────────────────────────────────────────

class CardWidget(QFrame):
    """
    A dark rounded card that acts as a container for panel content.
    Optionally shows a coloured left-edge accent bar.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        accent_color: str | None = None,
        radius: int = 12,
    ) -> None:
        super().__init__(parent)
        self._accent = QColor(accent_color) if accent_color else None
        self._radius = radius
        self.setObjectName("cardWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            #cardWidget {{
                background-color: {P.bg_card};
                border: 1px solid {P.border};
                border-radius: {radius}px;
            }}
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._accent:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(self._accent)
            p.drawRoundedRect(0, 8, 3, self.height() - 16, 2, 2)


# ── SectionHeader ─────────────────────────────────────────────────────────────

class SectionHeader(QWidget):
    """Labelled section header with a violet accent underline."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(title.upper())
        lbl.setStyleSheet(f"""
            color: {P.text_accent};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
        """)
        layout.addWidget(lbl)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: qlineargradient("
                           f"x1:0, y1:0, x2:1, y2:0, "
                           f"stop:0 {P.accent}, stop:1 transparent);")
        layout.addWidget(line)


# ── StatusBadge ───────────────────────────────────────────────────────────────

_BADGE_COLORS = {
    "ACTIVE":       ("#10B981", "#052E16"),
    "INACTIVE":     ("#475569", "#1E293B"),
    "ERROR":        ("#EF4444", "#2D0A0A"),
    "WARNING":      ("#F59E0B", "#2D1A00"),
    "INITIALISING": ("#3B82F6", "#0A1628"),
}


class StatusBadge(QLabel):
    """Coloured pill badge showing a component state."""

    def __init__(self, status: str = "INACTIVE", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.set_status(status)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(20)

    def set_status(self, status: str) -> None:
        fg, bg = _BADGE_COLORS.get(status.upper(), ("#94A3B8", "#1E293B"))
        self.setText(status.upper())
        self.setStyleSheet(f"""
            color: {fg};
            background-color: {bg};
            border: 1px solid {fg}44;
            border-radius: 10px;
            padding: 0px 8px;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 1px;
        """)


# ── LEDIndicator ──────────────────────────────────────────────────────────────

class LEDIndicator(QWidget):
    """Small circular LED that can pulse when active."""

    def __init__(
        self,
        color: str = "#10B981",
        size: int = 10,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._size = size
        self._glow = 1.0
        self._direction = -0.05
        self.setFixedSize(size + 6, size + 6)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self._timer.start(50)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def _pulse(self) -> None:
        self._glow += self._direction
        if self._glow <= 0.4 or self._glow >= 1.0:
            self._direction *= -1
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = self.width() // 2
        cy = self.height() // 2
        r = self._size // 2

        # Glow halo
        glow_color = QColor(self._color)
        glow_color.setAlphaF(self._glow * 0.35)
        p.setPen(Qt.NoPen)
        p.setBrush(glow_color)
        p.drawEllipse(cx - r - 3, cy - r - 3, (r + 3) * 2, (r + 3) * 2)

        # Core dot
        p.setBrush(self._color)
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)


# ── MetricTile ────────────────────────────────────────────────────────────────

class MetricTile(QWidget):
    """
    A compact tile showing a large value and a small label below it.
    Used in the AI analytics and vehicle simulator panels.
    """

    def __init__(
        self,
        label: str,
        value: str = "—",
        unit: str = "",
        accent: str = P.accent,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._accent = accent
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        self._value_lbl = QLabel(value)
        self._value_lbl.setAlignment(Qt.AlignCenter)
        self._value_lbl.setStyleSheet(f"""
            color: {accent};
            font-size: 22px;
            font-weight: 700;
        """)

        unit_lbl = QLabel(unit)
        unit_lbl.setAlignment(Qt.AlignCenter)
        unit_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px;")

        self._label_lbl = QLabel(label.upper())
        self._label_lbl.setAlignment(Qt.AlignCenter)
        self._label_lbl.setStyleSheet(f"""
            color: {P.text_secondary};
            font-size: 9px;
            letter-spacing: 1px;
        """)

        layout.addWidget(self._value_lbl)
        if unit:
            layout.addWidget(unit_lbl)
        layout.addWidget(self._label_lbl)

        self.setStyleSheet(f"""
            background-color: {P.bg_card};
            border: 1px solid {P.border};
            border-radius: 10px;
        """)

    def set_value(self, value: str) -> None:
        self._value_lbl.setText(value)


# ── GlowProgressBar ───────────────────────────────────────────────────────────

class GlowProgressBar(QWidget):
    """
    A slim progress bar with a coloured glow effect.
    Used for song progress, volume, and energy levels.
    """

    def __init__(
        self,
        color: str = P.accent,
        height: int = 6,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._value = 0.0   # 0.0 – 1.0
        self.setFixedHeight(height + 8)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        bar_h = h - 8
        y = 4

        # Track
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(P.bg_raised))
        p.drawRoundedRect(0, y, w, bar_h, bar_h // 2, bar_h // 2)

        # Fill
        fill_w = int(w * self._value)
        if fill_w > 0:
            grad = QLinearGradient(0, 0, fill_w, 0)
            grad.setColorAt(0, self._color.darker(120))
            grad.setColorAt(1, self._color)
            p.setBrush(grad)
            p.drawRoundedRect(0, y, fill_w, bar_h, bar_h // 2, bar_h // 2)

            # Glow
            glow = QColor(self._color)
            glow.setAlpha(60)
            p.setBrush(glow)
            p.drawRoundedRect(0, y - 2, fill_w, bar_h + 4, bar_h // 2, bar_h // 2)


# ── CircularGauge ─────────────────────────────────────────────────────────────

class CircularGauge(QWidget):
    """
    Arc-style circular gauge for speed, RPM, volume, etc.
    Draws a background arc and a coloured value arc with a centre label.
    """

    def __init__(
        self,
        label: str = "",
        min_val: float = 0,
        max_val: float = 100,
        unit: str = "",
        color: str = P.accent,
        size: int = 120,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._label = label
        self._min = min_val
        self._max = max_val
        self._value = min_val
        self._unit = unit
        self._color = QColor(color)
        self.setFixedSize(size, size)

    def set_value(self, value: float) -> None:
        self._value = max(self._min, min(self._max, value))
        self.update()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def _draw_arc(self, p, rect, ratio, span_angle, start_angle):
        """Draw background and value arcs."""
        pen = QPen(QColor(P.bg_raised), 8, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, int(start_angle * 16), int(-span_angle * 16))
        value_span = span_angle * ratio
        pen.setColor(self._color)
        p.setPen(pen)
        p.drawArc(rect, int(start_angle * 16), int(-value_span * 16))
        return value_span

    def _draw_tip_glow(self, p, rect, ratio, value_span, start_angle):
        """Draw glowing dot at the arc tip."""
        if ratio <= 0:
            return
        tip_angle = math.radians(start_angle - value_span)
        cx = rect.center().x() + (rect.width() / 2) * math.cos(tip_angle)
        cy = rect.center().y() - (rect.height() / 2) * math.sin(tip_angle)
        glow = QColor(self._color)
        glow.setAlpha(80)
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(QRectF(cx - 6, cy - 6, 12, 12))
        p.setBrush(self._color)
        p.drawEllipse(QRectF(cx - 3, cy - 3, 6, 6))

    def _draw_labels(self, p, rect):
        """Draw centre value, unit, and label text."""
        p.setPen(QColor(P.text_primary))
        p.setFont(QFont("Segoe UI", 14, QFont.Bold))
        p.drawText(rect.adjusted(0, 8, 0, 0), Qt.AlignCenter, f"{int(self._value)}")
        if self._unit:
            p.setPen(QColor(P.text_muted))
            p.setFont(QFont("Segoe UI", 7))
            p.drawText(QRectF(rect.left(), rect.center().y() + 14, rect.width(), 16),
                       Qt.AlignCenter, self._unit)
        if self._label:
            p.setPen(QColor(P.text_secondary))
            p.setFont(QFont("Segoe UI", 7, QFont.Bold))
            p.drawText(QRectF(rect.left(), rect.bottom() - 4, rect.width(), 14),
                       Qt.AlignCenter, self._label.upper())

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h    = self.width(), self.height()
        margin  = 12
        rect    = QRectF(margin, margin, w - 2 * margin, h - 2 * margin)
        start_angle = 225
        span_angle  = 270
        ratio       = (self._value - self._min) / max(self._max - self._min, 1)
        value_span  = self._draw_arc(p, rect, ratio, span_angle, start_angle)
        self._draw_tip_glow(p, rect, ratio, value_span, start_angle)
        self._draw_labels(p, rect)


# ── SeparatorLine ─────────────────────────────────────────────────────────────

class SeparatorLine(QFrame):
    """Thin 1px horizontal separator."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background-color: {P.border}; border: none;")
