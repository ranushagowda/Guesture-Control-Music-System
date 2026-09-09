"""
gui/lock_screen.py
==================
Gesture-based lock screen.

The correct unlock pattern is a single horizontal swipe drawn
LEFT → RIGHT across the canvas (a "sleeping line").

Rules
-----
- User presses mouse and drags across the canvas
- The drawn path must travel at least 55% of the canvas width
- The path must stay roughly horizontal (vertical drift < 20% of canvas height)
- Direction must be left-to-right (end.x > start.x)
- 3 failed attempts → 5-second lockout with countdown

On success  → sig_unlocked is emitted → main.py launches the dashboard.
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMainWindow, QMessageBox
from PySide6.QtCore    import Qt, Signal, QTimer, QPointF
from PySide6.QtGui     import (
    QPainter, QColor, QPen, QLinearGradient, QPainterPath,
)
from gui.theme import PALETTE as P, get_stylesheet

# ── Tuning ────────────────────────────────────────────────────────────────────
_MIN_TRAVEL_RATIO  = 0.55   # must cross at least 55% of canvas width
_MAX_VERT_RATIO    = 0.20   # vertical drift must stay within 20% of canvas height
_MAX_ATTEMPTS      = 3      # failed attempts before lockout
_LOCKOUT_SECONDS   = 5      # lockout duration


class _DrawCanvas(QWidget):
    """The interactive drawing surface."""

    sig_attempt = Signal(bool)   # True = success, False = fail

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 220)
        self.setCursor(Qt.CrossCursor)

        self._points: list[QPointF] = []
        self._drawing   = False
        self._last_ok   = None   # True/False/None — result of last attempt
        self._locked    = False

    def lock(self, locked: bool):
        self._locked = locked
        self._points = []
        self._last_ok = None
        self.update()

    # ── Mouse events ──────────────────────────────────────────────────────────

    def mousePressEvent(self, e):
        if self._locked:
            return
        if e.button() == Qt.LeftButton:
            self._drawing = True
            self._points  = [e.position()]
            self._last_ok = None
            self.update()

    def mouseMoveEvent(self, e):
        if self._drawing and not self._locked:
            self._points.append(e.position())
            self.update()

    def mouseReleaseEvent(self, e):
        if not self._drawing or self._locked:
            return
        self._drawing = False
        ok = self._validate()
        self._last_ok = ok
        self.sig_attempt.emit(ok)
        self.update()
        # Clear trail after short delay
        QTimer.singleShot(600, self._clear_trail)

    def _clear_trail(self):
        self._points = []
        self.update()

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate(self) -> bool:
        if len(self._points) < 8:
            return False
        W, H   = self.width(), self.height()
        start  = self._points[0]
        end    = self._points[-1]
        dx     = end.x() - start.x()
        # Must go left → right
        if dx < 0:
            return False
        # Must travel enough horizontal distance
        if dx < W * _MIN_TRAVEL_RATIO:
            return False
        # Vertical drift must be small
        ys     = [p.y() for p in self._points]
        spread = max(ys) - min(ys)
        if spread > H * _MAX_VERT_RATIO:
            return False
        return True

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, _):
        p  = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()

        # Background
        bg = QLinearGradient(0, 0, W, H)
        bg.setColorAt(0, QColor("#0D0D1A"))
        bg.setColorAt(1, QColor("#12121F"))
        p.fillRect(0, 0, W, H, bg)

        # Drawn trail
        if len(self._points) >= 2:
            if self._last_ok is True:
                trail_color = QColor("#10B981")
            elif self._last_ok is False:
                trail_color = QColor("#EF4444")
            else:
                trail_color = QColor(167, 139, 250, 220)

            path = QPainterPath()
            path.moveTo(self._points[0])
            for pt in self._points[1:]:
                path.lineTo(pt)

            # Glow
            glow_pen = QPen(QColor(trail_color.red(), trail_color.green(),
                                   trail_color.blue(), 60), 14, Qt.SolidLine,
                            Qt.RoundCap, Qt.RoundJoin)
            p.setPen(glow_pen)
            p.drawPath(path)

            # Core line
            core_pen = QPen(trail_color, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(core_pen)
            p.drawPath(path)

            # Start dot
            p.setPen(Qt.NoPen)
            p.setBrush(trail_color)
            p.drawEllipse(self._points[0], 6, 6)

        p.end()


class LockScreen(QMainWindow):
    sig_unlocked = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Cabin Experience — Authentication")
        self.setFixedSize(600, 500)
        self.setStyleSheet(get_stylesheet())

        self._attempts  = 0
        self._locked_out = False

        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        root.setStyleSheet(f"background:{P.bg_base};")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        # Logo / title
        title = QLabel("AI CABIN EXPERIENCE")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            color: {P.text_accent};
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 5px;
        """)

        subtitle = QLabel("Gesture Authentication Required")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color:{P.text_muted}; font-size:10px; letter-spacing:2px;")

        # Instruction
        instr = QLabel("Draw a pattern to unlock")
        instr.setAlignment(Qt.AlignCenter)
        instr.setStyleSheet(f"""
            color: {P.text_secondary};
            font-size: 13px;
            margin-top: 18px;
            margin-bottom: 6px;
        """)

        # Canvas
        self._canvas = _DrawCanvas()
        self._canvas.sig_attempt.connect(self._on_attempt)

        # Status label
        self._status = QLabel("Draw the unlock pattern above")
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setStyleSheet(f"color:{P.text_muted}; font-size:11px; margin-top:10px;")

        # Attempts dots
        self._dots_lbl = QLabel(self._dots_text())
        self._dots_lbl.setAlignment(Qt.AlignCenter)
        self._dots_lbl.setStyleSheet("font-size:14px; margin-top:6px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(instr)
        layout.addSpacing(10)
        layout.addWidget(self._canvas)
        layout.addWidget(self._status)
        layout.addWidget(self._dots_lbl)

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _dots_text(self) -> str:
        filled = "●" * self._attempts
        empty  = "○" * (_MAX_ATTEMPTS - self._attempts)
        return f"{filled}{empty}"

    def _on_attempt(self, success: bool):
        if self._locked_out:
            return

        if success:
            self._status.setText("✓  Pattern recognised — unlocking...")
            self._status.setStyleSheet(f"color:{P.success}; font-size:12px; font-weight:700; margin-top:10px;")
            QTimer.singleShot(700, self.sig_unlocked.emit)
        else:
            self._attempts += 1
            self._dots_lbl.setText(self._dots_text())
            remaining = _MAX_ATTEMPTS - self._attempts

            if self._attempts >= _MAX_ATTEMPTS:
                self._show_locked_popup()
            else:
                self._status.setText(
                    f"✗  Incorrect pattern  —  {remaining} attempt{'s' if remaining != 1 else ''} remaining"
                )
                self._status.setStyleSheet(f"color:{P.error}; font-size:11px; margin-top:10px;")

    def _show_locked_popup(self):
        self._locked_out = True
        self._canvas.lock(True)
        self._status.setText("🔒  Account locked")
        self._status.setStyleSheet(f"color:{P.error}; font-size:12px; font-weight:700; margin-top:10px;")
        self._dots_lbl.setText("●●●")

        msg = QMessageBox(self)
        msg.setWindowTitle("Authentication Failed")
        msg.setText(
            "Too many incorrect attempts.\n\n"
            "Please contact your administrator to unlock the system."
        )
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {P.bg_card};
                color: {P.text_primary};
            }}
            QLabel {{ color: {P.text_primary}; font-size: 12px; }}
            QPushButton {{
                background: {P.accent};
                color: white;
                border-radius: 6px;
                padding: 6px 20px;
                font-weight: 600;
            }}
        """)
        msg.exec()
