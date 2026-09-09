"""
gui/panels/music_panel.py
=========================
Music player panel: now-playing, progress, controls, volume, playlist.
Phase 2 uses dummy data; Phase 3 wires it to the real MusicEngine.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QListWidget, QListWidgetItem,
    QSizePolicy, QFileDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from gui.theme import PALETTE as P
from gui.widgets.base_widgets import (
    CardWidget, SectionHeader, GlowProgressBar, SeparatorLine,
)


class MusicPanel(QWidget):
    # Signals emitted to the main window / music engine (Phase 3)
    sig_play_pause  = Signal()
    sig_next        = Signal()
    sig_previous    = Signal()
    sig_shuffle     = Signal()
    sig_repeat      = Signal()
    sig_volume      = Signal(float)
    sig_seek        = Signal(float)   # 0.0–1.0 ratio
    sig_seek_delta  = Signal(float)   # seconds to skip (+/-)
    sig_song_select = Signal(int)
    sig_add_song    = Signal(str)    # absolute path of file chosen by user

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._shuffle_on = False
        self._repeat_on  = False
        self._build()
        self._load_dummy_data()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        root.addWidget(SectionHeader("Music Player"))
        root.addWidget(self._build_now_playing())
        root.addWidget(self._build_controls())
        root.addWidget(SeparatorLine())
        root.addWidget(self._build_playlist())

    def _build_now_playing(self) -> QWidget:
        card = CardWidget(accent_color=P.accent)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Song title
        self._title_lbl = QLabel("Sunroof")
        self._title_lbl.setStyleSheet(f"""
            color: {P.text_primary};
            font-size: 16px;
            font-weight: 700;
        """)
        self._title_lbl.setWordWrap(True)

        # Artist / file
        self._artist_lbl = QLabel("Nicky Youre & Dazy")
        self._artist_lbl.setStyleSheet(f"color: {P.text_secondary}; font-size: 11px;")

        # Mood badge row
        mood_row = QHBoxLayout()
        mood_row.setSpacing(8)
        self._mood_badge = QLabel("HAPPY")
        self._mood_badge.setStyleSheet(f"""
            color: {P.mood_happy};
            background: {P.mood_happy}22;
            border: 1px solid {P.mood_happy}55;
            border-radius: 8px;
            padding: 2px 10px;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        self._bpm_lbl = QLabel("BPM: 128")
        self._bpm_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 10px;")
        self._energy_lbl = QLabel("Energy: High")
        self._energy_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 10px;")
        mood_row.addWidget(self._mood_badge)
        mood_row.addWidget(self._bpm_lbl)
        mood_row.addWidget(self._energy_lbl)
        mood_row.addStretch()

        # Progress bar + time
        self._progress_bar = GlowProgressBar(color=P.accent, height=5)
        self._progress_bar.set_value(0.35)
        self._progress_bar.setCursor(Qt.PointingHandCursor)
        self._progress_bar.mousePressEvent = self._on_seek_click
        self._duration_sec = 0.0

        time_row = QHBoxLayout()
        self._elapsed_lbl = QLabel("1:08")
        self._elapsed_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px;")
        self._duration_lbl = QLabel("3:12")
        self._duration_lbl.setStyleSheet(f"color: {P.text_muted}; font-size: 9px;")
        time_row.addWidget(self._elapsed_lbl)
        time_row.addStretch()
        time_row.addWidget(self._duration_lbl)

        layout.addWidget(self._title_lbl)
        layout.addWidget(self._artist_lbl)
        layout.addLayout(mood_row)
        layout.addWidget(self._progress_bar)
        layout.addLayout(time_row)
        return card

    def _build_controls(self) -> QWidget:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Playback buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        btn_row.setAlignment(Qt.AlignCenter)

        self._shuffle_btn = self._ctrl_btn("⇄",   tooltip="Shuffle",      checkable=True, size=28)
        self._prev_btn    = self._ctrl_btn("⏮",   tooltip="Previous Song", size=28)
        self._rew_btn     = self._ctrl_btn("<<",  tooltip="Back 5 sec",    size=36, small_text=True)
        self._play_btn    = self._ctrl_btn("▶",    tooltip="Play / Pause",  large=True, accent=True)
        self._fwd_btn     = self._ctrl_btn(">>",  tooltip="Forward 5 sec", size=36, small_text=True)
        self._next_btn    = self._ctrl_btn("⏭",   tooltip="Next Song",     size=28)
        self._repeat_btn  = self._ctrl_btn("↺",   tooltip="Repeat",        checkable=True, size=28)

        self._shuffle_btn.clicked.connect(self._on_shuffle)
        self._prev_btn.clicked.connect(self.sig_previous)
        self._rew_btn.clicked.connect(lambda: self.sig_seek_delta.emit(-5.0))
        self._play_btn.clicked.connect(self.sig_play_pause)
        self._fwd_btn.clicked.connect(lambda: self.sig_seek_delta.emit(5.0))
        self._next_btn.clicked.connect(self.sig_next)
        self._repeat_btn.clicked.connect(self._on_repeat)

        for btn in [self._shuffle_btn, self._prev_btn, self._rew_btn, self._play_btn,
                    self._fwd_btn, self._next_btn, self._repeat_btn]:
            btn_row.addWidget(btn)

        # Volume row
        vol_row = QHBoxLayout()
        vol_row.setSpacing(8)
        vol_icon = QLabel("🔊")
        vol_icon.setStyleSheet("font-size: 12px;")
        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(60)
        self._vol_slider.setFixedHeight(20)
        self._vol_slider.valueChanged.connect(
            lambda v: self.sig_volume.emit(v / 100.0)
        )
        self._vol_value_lbl = QLabel("60%")
        self._vol_value_lbl.setStyleSheet(f"color: {P.text_secondary}; font-size: 10px;")
        self._vol_value_lbl.setFixedWidth(32)
        self._vol_slider.valueChanged.connect(
            lambda v: self._vol_value_lbl.setText(f"{v}%")
        )
        vol_row.addWidget(vol_icon)
        vol_row.addWidget(self._vol_slider)
        vol_row.addWidget(self._vol_value_lbl)

        layout.addLayout(btn_row)
        layout.addLayout(vol_row)
        return card

    def _build_playlist(self) -> QWidget:
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        hdr = QHBoxLayout()
        hdr.addWidget(SectionHeader("Playlist"))
        self._playlist_count = QLabel("3 songs")
        self._playlist_count.setStyleSheet(f"color: {P.text_muted}; font-size: 9px;")
        add_btn = QPushButton("+ Add Song")
        add_btn.setFixedHeight(22)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {P.accent_dim};
                color: {P.text_accent};
                border: 1px solid {P.accent};
                border-radius: 4px;
                font-size: 9px;
                padding: 0 8px;
            }}
            QPushButton:hover {{ background: {P.accent}; color: white; }}
        """)
        add_btn.clicked.connect(self._on_add_song)
        hdr.addStretch()
        hdr.addWidget(self._playlist_count)
        hdr.addWidget(add_btn)
        layout.addLayout(hdr)

        self._playlist = QListWidget()
        self._playlist.setMaximumHeight(160)
        self._playlist.itemDoubleClicked.connect(
            lambda item: self.sig_song_select.emit(self._playlist.row(item))
        )
        layout.addWidget(self._playlist)
        return card

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _ctrl_btn(
        self,
        text: str,
        tooltip: str = "",
        large: bool = False,
        accent: bool = False,
        checkable: bool = False,
        size: int = 34,
        small_text: bool = False,
    ) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setCheckable(checkable)
        size = 44 if large else size
        btn.setFixedSize(size, size)
        font_size = "10px" if small_text else ("16px" if large else "14px")
        if accent:
            btn.setObjectName("accentBtn")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {P.accent};
                    color: white;
                    border: none;
                    border-radius: {size // 2}px;
                    font-size: {font_size};
                    font-weight: 700;
                }}
                QPushButton:hover {{ background-color: {P.accent_light}; }}
                QPushButton:pressed {{ background-color: {P.accent_dim}; }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {P.bg_raised};
                    color: {P.text_primary};
                    border: 1px solid {P.border_bright};
                    border-radius: {size // 2}px;
                    font-size: {font_size};
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {P.accent_dim};
                    color: {P.text_accent};
                    border-color: {P.accent};
                }}
                QPushButton:checked {{
                    background-color: {P.accent_dim};
                    color: {P.accent_light};
                    border-color: {P.accent};
                }}
            """)
        return btn

    def _on_add_song(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Add Song",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.aac)"
        )
        if path:
            self.sig_add_song.emit(path)

    def _on_shuffle(self) -> None:
        self._shuffle_on = self._shuffle_btn.isChecked()
        self.sig_shuffle.emit()

    def _on_repeat(self) -> None:
        self._repeat_on = self._repeat_btn.isChecked()
        self.sig_repeat.emit()

    # mood colour map (matches core/constants.py MOOD_COLORS)
    _MOOD_HEX: dict[str, str] = {
        "Calm":      "#1E50B4",
        "Relaxed":   "#28A050",
        "Happy":     "#FFC828",
        "Energetic": "#A01EDC",
        "Sad":       "#142878",
        "Focus":     "#B4DCFF",
        "Unknown":   "#475569",
    }

    def _load_dummy_data(self) -> None:
        dummy_songs = [
            "Sunroof - Nicky Youre & Dazy",
            "Slow Acoustic Guitar - Quiet Place",
            "1 Minute Workout Countdown",
        ]
        self._song_moods: dict[int, str] = {}   # index → mood string
        for i, name in enumerate(dummy_songs):
            self._playlist.addItem(self._make_playlist_item(i, name, None))
        self._playlist.setCurrentRow(0)
        self._playlist_count.setText(f"{len(dummy_songs)} songs")

    def _make_playlist_item(self, index: int, name: str, mood: str | None) -> QListWidgetItem:
        mood_tag = f"  [{mood}]" if mood else "  […]"
        item = QListWidgetItem(f"  {index+1:02d}.  {name}{mood_tag}")
        if mood and mood in self._MOOD_HEX:
            item.setForeground(QColor(self._MOOD_HEX[mood]))
        else:
            item.setForeground(QColor(P.text_secondary))
        return item

    # ── Public update API (called by main window / engine) ────────────────────

    def update_song(self, title: str, artist: str) -> None:
        self._title_lbl.setText(title)
        self._artist_lbl.setText(artist)

    def update_progress(self, elapsed_sec: float, duration_sec: float) -> None:
        self._duration_sec = duration_sec
        ratio = elapsed_sec / max(duration_sec, 1)
        self._progress_bar.set_value(ratio)
        self._elapsed_lbl.setText(_fmt_time(elapsed_sec))
        self._duration_lbl.setText(_fmt_time(duration_sec))

    def _on_seek_click(self, event) -> None:
        w = self._progress_bar.width()
        if w > 0:
            ratio = max(0.0, min(1.0, event.position().x() / w))
            self.sig_seek.emit(ratio)

    def update_mood(self, mood: str, color: str) -> None:
        safe_mood  = mood.upper()[:20].replace("<", "").replace(">", "").replace("\"", "")
        safe_color = color if color.startswith("#") and len(color) <= 9 else P.text_muted
        self._mood_badge.setText(safe_mood)
        self._mood_badge.setStyleSheet(f"""
            color: {safe_color};
            background: {safe_color}22;
            border: 1px solid {safe_color}55;
            border-radius: 8px;
            padding: 2px 10px;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 1px;
        """)

    def update_bpm(self, bpm: float) -> None:
        self._bpm_lbl.setText(f"BPM: {int(bpm)}")

    def set_playing(self, playing: bool) -> None:
        self._play_btn.setText("⏸" if playing else "▶")

    def set_volume(self, volume: float) -> None:
        self._vol_slider.blockSignals(True)
        self._vol_slider.setValue(int(volume * 100))
        self._vol_slider.blockSignals(False)
        self._vol_value_lbl.setText(f"{int(volume * 100)}%")

    def set_playlist(self, songs: list[str]) -> None:
        self._playlist.clear()
        if not hasattr(self, "_song_moods"):
            self._song_moods = {}
        for i, name in enumerate(songs):
            mood = self._song_moods.get(i)
            self._playlist.addItem(self._make_playlist_item(i, name, mood))
        self._playlist_count.setText(f"{len(songs)} songs")

    def set_current_playlist_row(self, index: int) -> None:
        self._playlist.setCurrentRow(index)

    def update_song_mood(self, index: int, mood: str) -> None:
        """Called when audio analysis finishes for the song at `index`."""
        if not hasattr(self, "_song_moods"):
            self._song_moods = {}
        self._song_moods[index] = mood
        item = self._playlist.item(index)
        if item is None:
            return
        # Rewrite the item text with the new mood tag
        raw = item.text().strip()
        # Strip old mood tag if present
        if "  [" in raw:
            raw = raw[:raw.rfind("  [")]
        item.setText(f"{raw}  [{mood}]")
        color = self._MOOD_HEX.get(mood, P.text_secondary)
        item.setForeground(QColor(color))


def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"
