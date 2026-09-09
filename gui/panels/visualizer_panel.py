"""
gui/panels/visualizer_panel.py  —  Phase 11
=============================================
Real-time music visualizer using pyqtgraph.
Shows animated waveform bars and a frequency spectrum.
Falls back to a simple QPainter bar chart if pyqtgraph is unavailable.
"""
from __future__ import annotations
import math, random
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore    import Qt, QTimer, QRectF
from PySide6.QtGui     import QPainter, QColor, QLinearGradient
from gui.theme         import PALETTE as P
from gui.widgets.base_widgets import CardWidget, SectionHeader
_HAS_PG = False
try:
    import pyqtgraph as pg
    pg.setConfigOptions(antialias=True, background=P.bg_card, foreground=P.text_secondary)
    _HAS_PG = True
except ImportError:
    pass


class VisualizerPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bars   = [0.0] * 32
        self._energy = 0.0
        self._bpm    = 120.0
        self._beat   = False
        self._color  = (124, 58, 237)
        self._build()

        # Idle animation when no real data
        self._idle = QTimer(self)
        self._idle.timeout.connect(self._idle_tick)
        self._idle.start(80)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addWidget(SectionHeader("Music Visualizer"))

        card = CardWidget()
        inner = QVBoxLayout(card)
        inner.setContentsMargins(10, 8, 10, 8)
        inner.setSpacing(6)

        # Info row
        info = QHBoxLayout()
        self._bpm_lbl    = QLabel("BPM: --")
        self._energy_lbl = QLabel("Energy: --")
        self._beat_lbl   = QLabel("BEAT")
        for lbl in [self._bpm_lbl, self._energy_lbl]:
            lbl.setStyleSheet(f"color:{P.text_muted};font-size:9px;")
        self._beat_lbl.setStyleSheet(f"""
            color:{P.accent}; background:{P.accent}22;
            border:1px solid {P.accent}44; border-radius:6px;
            padding:1px 6px; font-size:9px; font-weight:700;
        """)
        self._beat_lbl.setVisible(False)
        info.addWidget(self._bpm_lbl)
        info.addWidget(self._energy_lbl)
        info.addStretch()
        info.addWidget(self._beat_lbl)
        inner.addLayout(info)

        # Visualizer canvas
        if _HAS_PG:
            self._plot = pg.PlotWidget()
            self._plot.setFixedHeight(110)
            self._plot.hideAxis("left")
            self._plot.hideAxis("bottom")
            self._plot.setMouseEnabled(False, False)
            x = list(range(32))
            self._bars_item = pg.BarGraphItem(
                x=x, height=[0.01]*32, width=0.7,
                brush=pg.mkBrush(124, 58, 237, 200),
            )
            self._plot.addItem(self._bars_item)
            self._plot.setYRange(0, 1.0)
            inner.addWidget(self._plot)
        else:
            self._canvas = _FallbackCanvas()
            self._canvas.setFixedHeight(110)
            inner.addWidget(self._canvas)

        root.addWidget(card)

    def _idle_tick(self):
        """Animate bars when no real audio data is flowing."""
        t = self._idle.property("t") or 0
        self._idle.setProperty("t", t + 1)
        bars = [
            0.1 + 0.5 * abs(math.sin(t * 0.15 + i * 0.4)) +
            0.2 * abs(math.sin(t * 0.07 + i * 0.9))
            for i in range(32)
        ]
        self._update_bars(bars)

    def _update_bars(self, bars: list[float]):
        self._bars = bars
        if _HAS_PG:
            self._bars_item.setOpts(height=bars)
            r, g, b = self._color
            self._bars_item.setOpts(brush=pg.mkBrush(r, g, b, 200))
        else:
            self._canvas.set_bars(bars, self._color)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_features(self, features: dict):
        self._idle.stop()
        energy = features.get("energy", 0.05)
        bpm    = features.get("bpm",    120.0)
        mfcc   = features.get("mfcc_vec", [])

        self._energy = energy
        self._bpm    = bpm
        self._bpm_lbl.setText(f"BPM: {int(bpm)}")
        self._energy_lbl.setText(f"Energy: {energy:.3f}")

        # Build bar heights from MFCC + noise
        if mfcc:
            raw = np.abs(mfcc)
            raw = raw / (np.max(raw) + 1e-9)
            # Upsample to 32 bars
            bars = np.interp(np.linspace(0, len(raw)-1, 32),
                             np.arange(len(raw)), raw).tolist()
        else:
            bars = [energy * 2 + random.uniform(0, 0.1) for _ in range(32)]

        self._update_bars(bars)
        self._idle.start(80)

    def set_ambient_color(self, r: int, g: int, b: int):
        self._color = (r, g, b)

    def set_beat(self, active: bool):
        self._beat_lbl.setVisible(active)


class _FallbackCanvas(QWidget):
    """Simple QPainter bar chart when pyqtgraph is unavailable."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bars  = [0.0] * 32
        self._color = (124, 58, 237)

    def set_bars(self, bars, color):
        self._bars  = bars
        self._color = color
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        n    = len(self._bars)
        bw   = W / n
        r, g, b = self._color

        for i, h_ratio in enumerate(self._bars):
            bh = max(2, int(H * h_ratio))
            x  = int(i * bw)
            y  = H - bh
            grad = QLinearGradient(x, y, x, H)
            grad.setColorAt(0, QColor(r, g, b, 220))
            grad.setColorAt(1, QColor(r//3, g//3, b//3, 80))
            p.setPen(Qt.NoPen)
            p.setBrush(grad)
            p.drawRoundedRect(QRectF(x+1, y, bw-2, bh), 2, 2)
