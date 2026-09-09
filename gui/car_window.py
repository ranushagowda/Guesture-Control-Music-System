"""
gui/car_window.py
=================
Digital Car Interior Window.

Renders a stylised automotive cabin using QPainter:
  - Windshield / headliner
  - Dashboard with infotainment screen
  - Steering wheel
  - Speedometer + tachometer arcs
  - Driver & passenger seats
  - Door panels
  - Ambient lighting strips (react to mood/music)
  - HUD overlay: song, mood, speed, drive mode

The ambient colour transitions smoothly via a QTimer interpolation loop.
"""

from __future__ import annotations
import math
from PySide6.QtWidgets import QMainWindow, QWidget
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont,
    QLinearGradient, QRadialGradient, QPainterPath,
)
from gui.theme import PALETTE as P
from core.logger import get_logger

log = get_logger(__name__)

# Transition speed: steps per tick, tick = 16 ms (~60 fps)
_TRANSITION_STEPS = 60


class CarCanvas(QWidget):
    """The actual drawing surface for the car interior."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(900, 580)

        # Current and target ambient colour
        self._current_rgb: list[float] = [30.0, 80.0, 180.0]
        self._target_rgb:  list[float] = [30.0, 80.0, 180.0]
        self._step_rgb:    list[float] = [0.0, 0.0, 0.0]
        self._transitioning = False

        # Display data
        self._song_name  = "Sunroof — Nicky Youre & Dazy"
        self._mood       = "Calm"
        self._speed      = 0.0
        self._drive_mode = "COMFORT"
        self._volume     = 0.6
        self._intensity  = 0.6
        self._progress   = 0.35

        # Transition timer (~60 fps)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._transition_step)
        self._timer.start(16)

    # ── Colour transition ─────────────────────────────────────────────────────

    def set_ambient_color(self, rgb: tuple[int, int, int]) -> None:
        self._target_rgb = [float(c) for c in rgb]
        for i in range(3):
            self._step_rgb[i] = (
                (self._target_rgb[i] - self._current_rgb[i]) / _TRANSITION_STEPS
            )
        self._transitioning = True

    def _transition_step(self) -> None:
        if not self._transitioning:
            return
        done = True
        for i in range(3):
            diff = self._target_rgb[i] - self._current_rgb[i]
            if abs(diff) > 0.5:
                self._current_rgb[i] += self._step_rgb[i]
                done = False
            else:
                self._current_rgb[i] = self._target_rgb[i]
        if done:
            self._transitioning = False
        self.update()

    def _ambient(self, alpha: int = 255) -> QColor:
        r, g, b = [max(0, min(255, int(c))) for c in self._current_rgb]
        return QColor(r, g, b, alpha)

    # ── Update API ────────────────────────────────────────────────────────────

    def update_state(
        self,
        song: str,
        mood: str,
        speed: float,
        drive_mode: str,
        volume: float,
        progress: float,
    ) -> None:
        self._song_name  = song
        self._mood       = mood
        self._speed      = speed
        self._drive_mode = drive_mode
        self._volume     = volume
        self._progress   = progress

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        W, H = self.width(), self.height()
        amb = self._ambient()

        self._draw_background(p, W, H, amb)
        self._draw_headliner(p, W, H, amb)
        self._draw_windshield(p, W, H)
        self._draw_dashboard(p, W, H, amb)
        self._draw_steering_wheel(p, W, H, amb)
        self._draw_gauges(p, W, H, amb)
        self._draw_infotainment_screen(p, W, H, amb)
        self._draw_seats(p, W, H, amb)
        self._draw_door_panels(p, W, H, amb)
        self._draw_ambient_strips(p, W, H, amb)
        self._draw_hud(p, W, H, amb)

    def _draw_background(self, p, W, H, amb):
        grad = QLinearGradient(0, 0, 0, H)
        grad.setColorAt(0, QColor(8, 8, 18))
        grad.setColorAt(1, QColor(15, 12, 10))
        p.fillRect(0, 0, W, H, grad)

    def _draw_headliner(self, p, W, H, amb):
        """Roof / headliner with ambient glow."""
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(W, 0)
        path.lineTo(W, H * 0.28)
        path.quadTo(W * 0.5, H * 0.32, 0, H * 0.28)
        path.closeSubpath()

        grad = QLinearGradient(0, 0, 0, H * 0.3)
        dark = QColor(amb)
        dark.setAlpha(30)
        grad.setColorAt(0, dark)
        grad.setColorAt(1, QColor(10, 10, 18, 200))
        p.setPen(Qt.NoPen)
        p.fillPath(path, grad)

        # Ambient glow on headliner
        glow_grad = QRadialGradient(W * 0.5, 0, W * 0.6)
        glow = QColor(amb)
        glow.setAlpha(40)
        glow_grad.setColorAt(0, glow)
        glow_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillPath(path, glow_grad)

    def _draw_windshield(self, p, W, H):
        """Windshield glass with reflection."""
        path = QPainterPath()
        path.moveTo(W * 0.12, H * 0.02)
        path.lineTo(W * 0.88, H * 0.02)
        path.lineTo(W * 0.82, H * 0.28)
        path.quadTo(W * 0.5, H * 0.31, W * 0.18, H * 0.28)
        path.closeSubpath()

        grad = QLinearGradient(0, 0, 0, H * 0.3)
        grad.setColorAt(0, QColor(140, 180, 220, 18))
        grad.setColorAt(0.5, QColor(100, 140, 200, 8))
        grad.setColorAt(1, QColor(60, 80, 120, 4))
        p.setPen(QPen(QColor(80, 100, 140, 40), 1))
        p.fillPath(path, grad)
        p.drawPath(path)

        # A-pillars
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(20, 18, 16))
        left_pillar = QPainterPath()
        left_pillar.moveTo(W * 0.0, H * 0.0)
        left_pillar.lineTo(W * 0.12, H * 0.02)
        left_pillar.lineTo(W * 0.18, H * 0.28)
        left_pillar.lineTo(W * 0.0, H * 0.35)
        left_pillar.closeSubpath()
        p.fillPath(left_pillar, QColor(18, 16, 14))

        right_pillar = QPainterPath()
        right_pillar.moveTo(W * 1.0, H * 0.0)
        right_pillar.lineTo(W * 0.88, H * 0.02)
        right_pillar.lineTo(W * 0.82, H * 0.28)
        right_pillar.lineTo(W * 1.0, H * 0.35)
        right_pillar.closeSubpath()
        p.fillPath(right_pillar, QColor(18, 16, 14))

    def _draw_dashboard(self, p, W, H, amb):
        """Main dashboard surface."""
        dash_top = H * 0.52
        path = QPainterPath()
        path.moveTo(0, dash_top)
        path.quadTo(W * 0.25, H * 0.48, W * 0.5, H * 0.50)
        path.quadTo(W * 0.75, H * 0.52, W, dash_top)
        path.lineTo(W, H)
        path.lineTo(0, H)
        path.closeSubpath()

        grad = QLinearGradient(0, dash_top, 0, H)
        grad.setColorAt(0, QColor(28, 24, 20))
        grad.setColorAt(0.3, QColor(22, 18, 15))
        grad.setColorAt(1, QColor(12, 10, 8))
        p.setPen(Qt.NoPen)
        p.fillPath(path, grad)

        # Dashboard top trim with ambient glow
        trim_path = QPainterPath()
        trim_path.moveTo(0, dash_top)
        trim_path.quadTo(W * 0.25, H * 0.48, W * 0.5, H * 0.50)
        trim_path.quadTo(W * 0.75, H * 0.52, W, dash_top)
        trim_path.lineTo(W, dash_top + 6)
        trim_path.quadTo(W * 0.75, H * 0.525, W * 0.5, H * 0.505)
        trim_path.quadTo(W * 0.25, H * 0.485, 0, dash_top + 6)
        trim_path.closeSubpath()

        glow = QColor(amb)
        glow.setAlpha(120)
        p.fillPath(trim_path, glow)

    def _draw_steering_wheel(self, p, W, H, amb):
        """Steering wheel with spokes and hub."""
        cx = W * 0.28
        cy = H * 0.72
        outer_r = W * 0.095
        inner_r = W * 0.022

        # Shadow
        shadow_grad = QRadialGradient(cx, cy + 8, outer_r + 10)
        shadow_grad.setColorAt(0, QColor(0, 0, 0, 80))
        shadow_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(shadow_grad)
        p.drawEllipse(QRectF(cx - outer_r - 10, cy - outer_r + 8,
                             (outer_r + 10) * 2, (outer_r + 10) * 2))

        # Outer ring
        ring_pen = QPen(QColor(35, 30, 25), int(outer_r * 0.18), Qt.SolidLine, Qt.RoundCap)
        p.setPen(ring_pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2))

        # Ambient ring highlight
        amb_pen = QPen(QColor(amb), 2)
        p.setPen(amb_pen)
        p.drawArc(QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2),
                  30 * 16, 120 * 16)

        # Spokes
        spoke_pen = QPen(QColor(40, 35, 30), int(outer_r * 0.08), Qt.SolidLine, Qt.RoundCap)
        p.setPen(spoke_pen)
        for angle_deg in [90, 210, 330]:
            rad = math.radians(angle_deg)
            x2 = cx + outer_r * 0.75 * math.cos(rad)
            y2 = cy - outer_r * 0.75 * math.sin(rad)
            p.drawLine(QPointF(cx, cy), QPointF(x2, y2))

        # Hub
        hub_grad = QRadialGradient(cx - inner_r * 0.3, cy - inner_r * 0.3, inner_r * 1.5)
        hub_grad.setColorAt(0, QColor(60, 55, 50))
        hub_grad.setColorAt(1, QColor(25, 22, 18))
        p.setPen(Qt.NoPen)
        p.setBrush(hub_grad)
        p.drawEllipse(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2))

        # Hub ambient dot
        p.setBrush(QColor(amb))
        dot_r = inner_r * 0.4
        p.drawEllipse(QRectF(cx - dot_r, cy - dot_r, dot_r * 2, dot_r * 2))

    def _draw_gauges(self, p, W, H, amb):
        pass

    def _draw_infotainment_screen(self, p, W, H, amb):
        """Centre infotainment screen on the dashboard."""
        sx = W * 0.42
        sy = H * 0.54
        sw = W * 0.22
        sh = H * 0.16
        radius = 8

        # Screen bezel
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(15, 13, 11))
        p.drawRoundedRect(QRectF(sx - 3, sy - 3, sw + 6, sh + 6), radius + 2, radius + 2)

        # Screen background
        screen_grad = QLinearGradient(sx, sy, sx, sy + sh)
        screen_grad.setColorAt(0, QColor(12, 14, 22))
        screen_grad.setColorAt(1, QColor(8, 10, 18))
        p.setBrush(screen_grad)
        p.drawRoundedRect(QRectF(sx, sy, sw, sh), radius, radius)

        # Ambient glow on screen border
        glow_pen = QPen(QColor(amb), 1)
        glow_pen.setColor(QColor(amb).lighter(120))
        p.setPen(glow_pen)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(sx, sy, sw, sh), radius, radius)

        # Song name on screen
        p.setPen(QColor(P.text_primary))
        p.setFont(QFont("Segoe UI", int(W * 0.009), QFont.Bold))
        song_short = self._song_name[:28] + ".." if len(self._song_name) > 28 else self._song_name
        p.drawText(QRectF(sx + 8, sy + 8, sw - 16, sh * 0.35),
                   Qt.AlignLeft | Qt.AlignVCenter, song_short)

        # Mood on screen
        p.setPen(QColor(amb).lighter(150))
        p.setFont(QFont("Segoe UI", int(W * 0.008)))
        p.drawText(QRectF(sx + 8, sy + sh * 0.38, sw - 16, sh * 0.28),
                   Qt.AlignLeft | Qt.AlignVCenter, f"Mood: {self._mood}")

        # Progress bar on screen
        pb_y = sy + sh * 0.72
        pb_h = 3
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(40, 40, 60))
        p.drawRoundedRect(QRectF(sx + 8, pb_y, sw - 16, pb_h), 1, 1)
        p.setBrush(QColor(amb))
        p.drawRoundedRect(QRectF(sx + 8, pb_y, (sw - 16) * self._progress, pb_h), 1, 1)

        # Volume indicator
        p.setPen(QColor(P.text_muted))
        p.setFont(QFont("Segoe UI", int(W * 0.007)))
        p.drawText(QRectF(sx + 8, sy + sh * 0.82, sw - 16, sh * 0.18),
                   Qt.AlignLeft | Qt.AlignVCenter,
                   f"VOL {int(self._volume * 100)}%   {self._drive_mode}")

    def _draw_seats(self, p, W, H, amb):
        """Driver and passenger seat silhouettes."""
        for sx_ratio, is_driver in [(0.08, True), (0.62, False)]:
            sx = W * sx_ratio
            sy = H * 0.62
            sw = W * 0.26
            sh = H * 0.40

            # Seat back
            path = QPainterPath()
            path.moveTo(sx + sw * 0.1, sy)
            path.lineTo(sx + sw * 0.9, sy)
            path.quadTo(sx + sw, sy + sh * 0.1, sx + sw, sy + sh * 0.5)
            path.lineTo(sx + sw * 0.95, sy + sh)
            path.lineTo(sx + sw * 0.05, sy + sh)
            path.lineTo(sx, sy + sh * 0.5)
            path.quadTo(sx, sy + sh * 0.1, sx + sw * 0.1, sy)
            path.closeSubpath()

            seat_grad = QLinearGradient(sx, sy, sx + sw, sy + sh)
            seat_grad.setColorAt(0, QColor(38, 33, 28))
            seat_grad.setColorAt(0.5, QColor(30, 26, 22))
            seat_grad.setColorAt(1, QColor(20, 17, 14))
            p.setPen(Qt.NoPen)
            p.fillPath(path, seat_grad)

            # Seat stitching / ambient trim
            trim_pen = QPen(QColor(amb), 1)
            trim_pen.setColor(QColor(amb).darker(150))
            p.setPen(trim_pen)
            p.setBrush(Qt.NoBrush)
            # Just draw the outline as trim
            p.drawPath(path)

            # Ambient strip on seat side
            strip_x = sx + (sw * 0.92 if not is_driver else sw * 0.02)
            strip_grad = QLinearGradient(strip_x, sy, strip_x, sy + sh * 0.7)
            amb_strip = QColor(amb)
            amb_strip.setAlpha(60)
            strip_grad.setColorAt(0, amb_strip)
            strip_grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(strip_grad)
            p.drawRoundedRect(QRectF(strip_x - 2, sy, 4, sh * 0.7), 2, 2)

    def _draw_door_panels(self, p, W, H, amb):
        """Left and right door panel strips."""
        for x, w_ratio in [(0, 0.07), (W * 0.93, 0.07)]:
            panel_w = W * w_ratio
            grad = QLinearGradient(x, H * 0.3, x + panel_w, H * 0.3)
            grad.setColorAt(0, QColor(22, 18, 15))
            grad.setColorAt(1, QColor(15, 12, 10))
            p.setPen(Qt.NoPen)
            p.setBrush(grad)
            p.drawRect(QRectF(x, H * 0.3, panel_w, H * 0.7))

            # Door ambient strip
            strip_grad = QLinearGradient(0, H * 0.55, 0, H * 0.85)
            amb_c = QColor(amb)
            amb_c.setAlpha(80)
            strip_grad.setColorAt(0, amb_c)
            strip_grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(strip_grad)
            strip_x = x + panel_w * 0.3 if x == 0 else x + panel_w * 0.1
            p.drawRoundedRect(QRectF(strip_x, H * 0.55, 3, H * 0.3), 1, 1)

    def _draw_ambient_strips(self, p, W, H, amb):
        """Footwell and dashboard ambient lighting strips."""
        # Dashboard strip
        strip_grad = QLinearGradient(0, H * 0.52, 0, H * 0.56)
        amb_bright = QColor(amb).lighter(130)
        amb_bright.setAlpha(100)
        strip_grad.setColorAt(0, amb_bright)
        strip_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(strip_grad)
        p.drawRect(QRectF(W * 0.05, H * 0.52, W * 0.9, H * 0.04))

        # Footwell glow (left)
        fw_grad = QRadialGradient(W * 0.2, H * 0.95, W * 0.15)
        fw_c = QColor(amb)
        fw_c.setAlpha(50)
        fw_grad.setColorAt(0, fw_c)
        fw_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(fw_grad)
        p.drawEllipse(QRectF(W * 0.05, H * 0.80, W * 0.30, H * 0.30))

        # Footwell glow (right)
        fw_grad2 = QRadialGradient(W * 0.8, H * 0.95, W * 0.15)
        fw_grad2.setColorAt(0, fw_c)
        fw_grad2.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(fw_grad2)
        p.drawEllipse(QRectF(W * 0.65, H * 0.80, W * 0.30, H * 0.30))

    def _draw_hud(self, p, W, H, amb):
        """Heads-up display overlay: song, mood, speed, drive mode."""
        # Semi-transparent HUD bar at bottom
        hud_h = H * 0.06
        hud_y = H - hud_h - 4
        hud_bg = QColor(10, 8, 6, 180)
        p.setPen(Qt.NoPen)
        p.setBrush(hud_bg)
        p.drawRoundedRect(QRectF(W * 0.05, hud_y, W * 0.9, hud_h), 6, 6)

        # HUD border
        p.setPen(QPen(QColor(amb), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(W * 0.05, hud_y, W * 0.9, hud_h), 6, 6)

        font_size = max(7, int(W * 0.009))
        p.setFont(QFont("Segoe UI", font_size))

        items = [
            (W * 0.08,  f"♪  {self._song_name[:30]}",  P.text_primary),
            (W * 0.52,  f"Mood: {self._mood}",          "#{:02X}{:02X}{:02X}".format(
                *[max(0, min(255, int(c))) for c in self._current_rgb])),
            (W * 0.75,  f"Mode: {self._drive_mode}",    P.text_secondary),
        ]
        for x, text, color in items:
            p.setPen(QColor(color))
            p.drawText(QRectF(x, hud_y, W * 0.18, hud_h),
                       Qt.AlignLeft | Qt.AlignVCenter, text)


class CarWindow(QMainWindow):
    """The top-level window that hosts the CarCanvas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Digital Car Interior — AI Cabin Experience")
        self.resize(900, 580)
        self.setMinimumSize(700, 450)
        self.setStyleSheet(f"background-color: {P.bg_deep};")

        self._canvas = CarCanvas()
        self.setCentralWidget(self._canvas)
        log.info("CarWindow initialised.")

    # ── Public API ────────────────────────────────────────────────────────────

    def set_ambient_color(self, rgb: tuple[int, int, int]) -> None:
        self._canvas.set_ambient_color(rgb)

    def update_state(
        self,
        song: str = "",
        mood: str = "",
        speed: float = 0,
        drive_mode: str = "COMFORT",
        volume: float = 0.6,
        progress: float = 0.0,
    ) -> None:
        self._canvas.update_state(song, mood, speed, drive_mode, volume, progress)
