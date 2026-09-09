"""
gui/panels/gesture_info_panel.py
=================================
Bottom-left info panel with two tabs:
  • Gesture Guide  — visual cheat-sheet of all gestures + actions
  • Mood Legend    — colour-coded mood descriptions
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
)
from gui.theme import PALETTE as P
from gui.widgets.base_widgets import CardWidget, SectionHeader


_GESTURES = [
    ("✋", "Open Hand",   "Start / Resume Music",  P.success),
    ("✊", "Fist",        "Stop Music",             "#EF4444"),
    ("🤘", "Rock",        "Next Song",              "#F59E0B"),
    ("✌", "Peace",       "Previous Song",          "#3B82F6"),
    ("☝", "Index Swipe", "L→R Vol+  /  R→L Vol−", "#A78BFA"),
]

_MOODS = [
    ("Calm",      "#1E50B4", "Slow, quiet, peaceful"),
    ("Relaxed",   "#28A050", "Gentle, warm, flowing"),
    ("Happy",     "#FFC828", "Upbeat, bright, danceable"),
    ("Energetic", "#A01EDC", "Fast, loud, driving beat"),
    ("Sad",       "#4466CC", "Slow, minor key, sparse"),
    ("Focus",     "#B4DCFF", "Steady, moderate tempo"),
]


def _row_label(text: str, color: str, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    weight = "700" if bold else "400"
    lbl.setStyleSheet(f"color:{color}; font-size:10px; font-weight:{weight}; background:transparent;")
    return lbl


class GestureInfoPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {P.border};
                border-radius: 8px;
                background: {P.bg_card};
            }}
            QTabBar::tab {{
                background: {P.bg_surface};
                color: {P.text_muted};
                padding: 5px 12px;
                font-size: 9px;
                border-radius: 4px;
                margin: 2px;
            }}
            QTabBar::tab:selected {{
                background: {P.accent_dim};
                color: {P.text_accent};
            }}
        """)

        tabs.addTab(self._build_gesture_tab(), "🖐 Gestures")
        tabs.addTab(self._build_mood_tab(),    "🎨 Moods")
        root.addWidget(tabs)

    def _build_gesture_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background:{P.bg_card};")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title = QLabel("Hold 3s to trigger  •  Swipe = instant")
        title.setStyleSheet(f"color:{P.text_muted}; font-size:8px; font-style:italic;")
        layout.addWidget(title)

        for icon, name, action, color in _GESTURES:
            row = QHBoxLayout()
            row.setSpacing(8)

            icon_lbl = QLabel(icon)
            icon_lbl.setFixedWidth(22)
            icon_lbl.setStyleSheet("font-size:14px; background:transparent;")

            name_lbl = QLabel(name)
            name_lbl.setFixedWidth(80)
            name_lbl.setStyleSheet(f"color:{color}; font-size:10px; font-weight:700; background:transparent;")

            arrow = QLabel("→")
            arrow.setStyleSheet(f"color:{P.text_muted}; font-size:10px; background:transparent;")
            arrow.setFixedWidth(12)

            action_lbl = QLabel(action)
            action_lbl.setStyleSheet(f"color:{P.text_secondary}; font-size:10px; background:transparent;")

            row.addWidget(icon_lbl)
            row.addWidget(name_lbl)
            row.addWidget(arrow)
            row.addWidget(action_lbl)
            row.addStretch()
            layout.addLayout(row)

        layout.addStretch()
        return w

    def _build_mood_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background:{P.bg_card};")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title = QLabel("Cabin lighting changes with detected mood")
        title.setStyleSheet(f"color:{P.text_muted}; font-size:8px; font-style:italic;")
        layout.addWidget(title)

        for mood, color, desc in _MOODS:
            row = QHBoxLayout()
            row.setSpacing(8)

            # Colour dot
            dot = QLabel("●")
            dot.setFixedWidth(14)
            dot.setStyleSheet(f"color:{color}; font-size:12px; background:transparent;")

            mood_lbl = QLabel(mood)
            mood_lbl.setFixedWidth(68)
            mood_lbl.setStyleSheet(f"color:{color}; font-size:10px; font-weight:700; background:transparent;")

            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"color:{P.text_muted}; font-size:9px; background:transparent;")

            row.addWidget(dot)
            row.addWidget(mood_lbl)
            row.addWidget(desc_lbl)
            row.addStretch()
            layout.addLayout(row)

        layout.addStretch()
        return w
