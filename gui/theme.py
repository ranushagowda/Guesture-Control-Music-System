"""
gui/theme.py
============
Dark automotive HMI theme.
Provides the QSS stylesheet and a typed colour palette used by all widgets.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    # Backgrounds
    bg_deep:    str = "#07070F"
    bg_base:    str = "#0D0D1A"
    bg_surface: str = "#12121F"
    bg_card:    str = "#16162A"
    bg_raised:  str = "#1C1C30"
    bg_input:   str = "#1A1A2E"

    # Borders
    border:        str = "#1E1E35"
    border_bright: str = "#2A2A45"

    # Accent / brand
    accent:        str = "#7C3AED"   # violet
    accent_light:  str = "#9D5FF5"
    accent_dim:    str = "#4C1D95"
    accent_glow:   str = "#7C3AED44"

    # Semantic
    success: str = "#10B981"
    warning: str = "#F59E0B"
    error:   str = "#EF4444"
    info:    str = "#3B82F6"

    # Text
    text_primary:   str = "#E2E8F0"
    text_secondary: str = "#94A3B8"
    text_muted:     str = "#475569"
    text_accent:    str = "#A78BFA"

    # Mood colours (used for ambient lighting)
    mood_calm:      str = "#1E50B4"
    mood_relaxed:   str = "#28A050"
    mood_happy:     str = "#FFC828"
    mood_energetic: str = "#A01EDC"
    mood_sad:       str = "#142878"
    mood_focus:     str = "#B4DCFF"


PALETTE = Palette()


def get_stylesheet() -> str:
    p = PALETTE
    return f"""
/* ── Global ──────────────────────────────────────────────── */
* {{
    font-family: "Segoe UI", "Inter", sans-serif;
    color: {p.text_primary};
    outline: none;
}}

QMainWindow, QDialog, QWidget {{
    background-color: {p.bg_base};
}}

/* ── Scroll bars ─────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {p.bg_surface};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {p.border_bright};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ── Labels ──────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {p.text_primary};
}}

/* ── Push Buttons ────────────────────────────────────────── */
QPushButton {{
    background-color: {p.bg_raised};
    color: {p.text_primary};
    border: 1px solid {p.border_bright};
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {p.accent_dim};
    border-color: {p.accent};
    color: {p.text_accent};
}}
QPushButton:pressed {{
    background-color: {p.accent};
    border-color: {p.accent_light};
}}
QPushButton:disabled {{
    background-color: {p.bg_surface};
    color: {p.text_muted};
    border-color: {p.border};
}}

/* ── Accent Button ───────────────────────────────────────── */
QPushButton#accentBtn {{
    background-color: {p.accent};
    border-color: {p.accent_light};
    color: #FFFFFF;
    font-weight: 600;
}}
QPushButton#accentBtn:hover {{
    background-color: {p.accent_light};
}}

/* ── Sliders ─────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    height: 4px;
    background: {p.bg_raised};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {p.accent};
    border: 2px solid {p.accent_light};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{
    background: {p.accent};
    border-radius: 2px;
}}
QSlider::groove:vertical {{
    width: 4px;
    background: {p.bg_raised};
    border-radius: 2px;
}}
QSlider::handle:vertical {{
    background: {p.accent};
    border: 2px solid {p.accent_light};
    width: 14px;
    height: 14px;
    margin: 0 -5px;
    border-radius: 7px;
}}
QSlider::sub-page:vertical {{
    background: {p.accent};
    border-radius: 2px;
}}

/* ── Progress Bar ────────────────────────────────────────── */
QProgressBar {{
    background-color: {p.bg_raised};
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {p.accent};
    border-radius: 3px;
}}

/* ── List Widget ─────────────────────────────────────────── */
QListWidget {{
    background-color: {p.bg_surface};
    border: 1px solid {p.border};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 6px 10px;
    border-radius: 5px;
    color: {p.text_secondary};
    font-size: 11px;
}}
QListWidget::item:hover {{
    background-color: {p.bg_raised};
    color: {p.text_primary};
}}
QListWidget::item:selected {{
    background-color: {p.accent_dim};
    color: {p.text_accent};
    border-left: 2px solid {p.accent};
}}

/* ── Combo Box ───────────────────────────────────────────── */
QComboBox {{
    background-color: {p.bg_input};
    border: 1px solid {p.border_bright};
    border-radius: 6px;
    padding: 5px 10px;
    color: {p.text_primary};
    font-size: 11px;
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {p.bg_card};
    border: 1px solid {p.border_bright};
    selection-background-color: {p.accent_dim};
    color: {p.text_primary};
}}

/* ── Tool Tips ───────────────────────────────────────────── */
QToolTip {{
    background-color: {p.bg_card};
    color: {p.text_primary};
    border: 1px solid {p.border_bright};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}}

/* ── Splitter ────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {p.border};
}}
"""
