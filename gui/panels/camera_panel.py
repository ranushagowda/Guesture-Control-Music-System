"""
gui/panels/camera_panel.py
==========================
Camera feed panel: live frame display, gesture name, confidence bar,
hand landmark status, and FPS counter.
Phase 2 shows a placeholder; Phase 4 wires it to the real camera worker.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QColor, QPainter, QFont, QPen
from gui.theme import PALETTE as P
from gui.widgets.base_widgets import (
    CardWidget, SectionHeader, GlowProgressBar, StatusBadge,
)


class CameraPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        root.addWidget(SectionHeader("Camera Feed & Gesture Recognition"))
        root.addWidget(self._build_feed())
        root.addWidget(self._build_gesture_status())

    def _build_feed(self) -> QWidget:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Feed label
        self._feed_lbl = QLabel()
        self._feed_lbl.setAlignment(Qt.AlignCenter)
        self._feed_lbl.setMinimumSize(320, 240)
        self._feed_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._feed_lbl.setStyleSheet(f"""
            background-color: {P.bg_deep};
            border-radius: 8px;
            color: {P.text_muted};
            font-size: 12px;
        """)
        self._feed_lbl.setText("Camera initialising...")
        self._show_placeholder()

        # FPS + hand status row
        info_row = QHBoxLayout()
        self._fps_lbl = QLabel("FPS: --")
        self._fps_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px;")
        self._hand_status = StatusBadge("INACTIVE")
        self._res_lbl = QLabel("640 × 480")
        self._res_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px;")
        info_row.addWidget(self._fps_lbl)
        info_row.addStretch()
        info_row.addWidget(QLabel("Hand:"))
        info_row.addWidget(self._hand_status)
        info_row.addStretch()
        info_row.addWidget(self._res_lbl)
        for lbl in info_row.children():
            if isinstance(lbl, QLabel):
                lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px;")

        layout.addWidget(self._feed_lbl)
        layout.addLayout(info_row)
        return card

    def _build_gesture_status(self) -> QWidget:
        card = CardWidget(accent_color=P.accent)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Detected gesture
        gest_row = QHBoxLayout()
        gest_icon_lbl = QLabel("GESTURE")
        gest_icon_lbl.setStyleSheet(f"""
            color: {P.text_muted};
            font-size: 9px;
            letter-spacing: 2px;
            font-weight: 600;
        """)
        self._gesture_lbl = QLabel("No Hand Detected")
        self._gesture_lbl.setStyleSheet(f"""
            color: {P.text_accent};
            font-size: 18px;
            font-weight: 700;
        """)
        gest_row.addWidget(gest_icon_lbl)
        gest_row.addStretch()
        gest_row.addWidget(self._gesture_lbl)

        # Action label
        action_row = QHBoxLayout()
        action_lbl = QLabel("ACTION")
        action_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 2px;")
        self._action_lbl = QLabel("—")
        self._action_lbl.setStyleSheet(f"color: {P.text_secondary}; font-size: 12px;")
        action_row.addWidget(action_lbl)
        action_row.addStretch()
        action_row.addWidget(self._action_lbl)

        # Confidence bar
        conf_row = QHBoxLayout()
        conf_lbl = QLabel("CONFIDENCE")
        conf_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 2px;")
        self._conf_value_lbl = QLabel("0%")
        self._conf_value_lbl.setStyleSheet(f"color: {P.text_secondary}; font-size: 10px;")
        conf_row.addWidget(conf_lbl)
        conf_row.addStretch()
        conf_row.addWidget(self._conf_value_lbl)

        self._conf_bar = GlowProgressBar(color=P.success, height=5)
        self._conf_bar.set_value(0.0)

        # Finger states row
        finger_row = QHBoxLayout()
        finger_row.setSpacing(6)
        finger_lbl = QLabel("FINGERS")
        finger_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 2px;")
        finger_row.addWidget(finger_lbl)
        finger_row.addStretch()

        self._finger_lbls: list[QLabel] = []
        for name in ["T", "I", "M", "R", "P"]:
            lbl = QLabel(name)
            lbl.setFixedSize(22, 22)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"""
                background: {P.bg_raised};
                color: {P.text_muted};
                border-radius: 11px;
                font-size: 9px;
                font-weight: 700;
            """)
            finger_row.addWidget(lbl)
            self._finger_lbls.append(lbl)

        # Hold / cooldown status label + progress bar
        hold_header = QHBoxLayout()
        hold_title = QLabel("HOLD 3s")
        hold_title.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; letter-spacing: 2px;")
        self._hold_state_lbl = QLabel("READY")
        self._hold_state_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; font-weight: 700;")
        hold_header.addWidget(hold_title)
        hold_header.addStretch()
        hold_header.addWidget(self._hold_state_lbl)

        self._hold_bar = GlowProgressBar(color=P.warning, height=7)
        self._hold_bar.set_value(0.0)

        # Gesture guide
        guide_lbl = QLabel(
            "\u270b Open Hand = Start/Resume  \u2502  "
            "\u270a Fist = Stop  \u2502  "
            "\U0001f918 Rock = Next  \u2502  "
            "\u270c Peace = Prev  \u2502  "
            "\u261d Swipe L\u2192R = Vol+  /  R\u2192L = Vol\u2212"
        )
        guide_lbl.setWordWrap(True)
        guide_lbl.setStyleSheet(f"color:{P.text_muted};font-size:8px;padding:4px 0;")

        layout.addLayout(gest_row)
        layout.addLayout(action_row)
        layout.addLayout(conf_row)
        layout.addWidget(self._conf_bar)
        layout.addLayout(finger_row)
        layout.addLayout(hold_header)
        layout.addWidget(self._hold_bar)
        layout.addWidget(guide_lbl)
        return card

    # ── Placeholder frame ─────────────────────────────────────────────────────

    def _show_placeholder(self) -> None:
        w, h = 320, 240
        img = QImage(w, h, QImage.Format_RGB888)
        img.fill(QColor(P.bg_deep))
        p = QPainter(img)
        p.setPen(QPen(QColor(P.border_bright), 1))
        # Grid lines
        for x in range(0, w, 40):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, 40):
            p.drawLine(0, y, w, y)
        # Centre text
        p.setPen(QColor(P.text_muted))
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(img.rect(), Qt.AlignCenter, "Camera Feed\nInitialising...")
        p.end()
        self._feed_lbl.setPixmap(QPixmap.fromImage(img))

    # ── Public update API ─────────────────────────────────────────────────────

    def update_frame(self, qimage: QImage) -> None:
        """Called by the camera worker thread with each new frame."""
        pixmap = QPixmap.fromImage(qimage)
        scaled = pixmap.scaled(
            self._feed_lbl.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._feed_lbl.setPixmap(scaled)

    def update_gesture(
        self,
        gesture: str,
        action: str,
        confidence: float,
        finger_states: list[bool] | None = None,
    ) -> None:
        self._gesture_lbl.setText(gesture)
        self._action_lbl.setText(action)
        self._conf_value_lbl.setText(f"{int(confidence * 100)}%")
        self._conf_bar.set_value(confidence)

        # Colour confidence bar by level
        if confidence >= 0.8:
            self._conf_bar.set_color(P.success)
        elif confidence >= 0.5:
            self._conf_bar.set_color(P.warning)
        else:
            self._conf_bar.set_color(P.error)

        if finger_states:
            for i, (lbl, state) in enumerate(zip(self._finger_lbls, finger_states)):
                if state:
                    lbl.setStyleSheet(f"""
                        background: {P.accent};
                        color: white;
                        border-radius: 11px;
                        font-size: 9px;
                        font-weight: 700;
                    """)
                else:
                    lbl.setStyleSheet(f"""
                        background: {P.bg_raised};
                        color: {P.text_muted};
                        border-radius: 11px;
                        font-size: 9px;
                        font-weight: 700;
                    """)

    def update_hold_progress(self, value: float) -> None:
        self._hold_bar.set_value(value)
        if value >= 1.0:
            self._hold_bar.set_color(P.success)
            self._hold_state_lbl.setText("FIRED \u2713")
            self._hold_state_lbl.setStyleSheet(f"color: {P.success}; font-size: 9px; font-weight: 700;")
        elif value > 0.01:
            pct = int(value * 100)
            self._hold_bar.set_color(P.warning)
            self._hold_state_lbl.setText(f"SCANNING {pct}%")
            self._hold_state_lbl.setStyleSheet(f"color: {P.warning}; font-size: 9px; font-weight: 700;")
        else:
            self._hold_bar.set_color(P.warning)
            self._hold_state_lbl.setText("READY")
            self._hold_state_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; font-weight: 700;")

    def update_cooldown(self, remaining: float) -> None:
        """remaining: 1.0 = just fired, 0.0 = cooldown done."""
        if remaining > 0.01:
            self._hold_bar.set_value(remaining)
            self._hold_bar.set_color(P.error)
            pct = int(remaining * 100)
            self._hold_state_lbl.setText(f"COOLDOWN {pct}%")
            self._hold_state_lbl.setStyleSheet(f"color: {P.error}; font-size: 9px; font-weight: 700;")
        else:
            self._hold_bar.set_value(0.0)
            self._hold_bar.set_color(P.warning)
            self._hold_state_lbl.setText("READY")
            self._hold_state_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px; font-weight: 700;")

    def update_fps(self, fps: float) -> None:
        self._fps_lbl.setText(f"FPS: {fps:.1f}")

    def set_hand_detected(self, detected: bool) -> None:
        self._hand_status.set_status("ACTIVE" if detected else "INACTIVE")
