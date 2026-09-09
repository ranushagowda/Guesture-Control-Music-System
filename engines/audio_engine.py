"""
engines/audio_engine.py  —  Phase 7
=====================================
Librosa-based audio feature extraction.
Runs in a QThread so heavy FFT work never blocks the GUI.

Emits
-----
sig_features(dict)   — full feature dict every update_interval seconds
sig_bpm(float)
sig_energy(float)
"""
from __future__ import annotations
import time
import numpy as np
import soundfile as sf
from PySide6.QtCore import QThread, Signal
from core.logger import get_logger
log = get_logger(__name__)

# Import librosa once at module level to avoid 3-4s delay on first analysis
try:
    import librosa as _librosa
    _LIBROSA_OK = True
except ImportError:
    _librosa = None
    _LIBROSA_OK = False


class AudioEngine(QThread):
    sig_features = Signal(dict)
    sig_bpm      = Signal(float)
    sig_energy   = Signal(float)
    sig_error    = Signal(str)

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self._cfg      = cfg
        self._path     = ""
        self._running  = False
        self._trigger  = False
        self._interval = float(cfg.audio_analysis.update_interval_sec)

    def set_song(self, path: str):
        self._path = path
        self._trigger = True   # force immediate re-analysis on next loop tick

    def run(self):
        self._running = True
        self._trigger = False
        log.info("AudioEngine started.")
        while self._running:
            if self._path:
                self._analyse()
                self._trigger = False
            # sleep in small chunks so _trigger is noticed quickly
            for _ in range(int(self._interval / 0.1)):
                if not self._running or self._trigger:
                    break
                time.sleep(0.1)
        log.info("AudioEngine stopped.")

    def _extract_window(self, y: np.ndarray, sr: int, cfg) -> tuple[dict, float]:
        """Extract features from a single audio window. Returns (feature_dict, tempo)."""
        librosa = _librosa
        mfcc      = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=cfg.n_mfcc)
        chroma    = librosa.feature.chroma_stft(y=y, sr=sr)
        rms       = librosa.feature.rms(y=y)
        centroid  = librosa.feature.spectral_centroid(y=y, sr=sr)
        bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        zcr       = librosa.feature.zero_crossing_rate(y)
        mel       = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=cfg.n_mels)

        t60,  b60  = librosa.beat.beat_track(y=y, sr=sr, start_bpm=60,  tightness=80)
        t120, b120 = librosa.beat.beat_track(y=y, sr=sr, start_bpm=120, tightness=80)
        t60  = float(np.atleast_1d(t60)[0])
        t120 = float(np.atleast_1d(t120)[0])
        tempo = t60 if len(b60) >= len(b120) else t120
        energy_now = float(np.mean(rms))
        if tempo > 110 and energy_now < 0.06:
            tempo /= 2.0

        feats = {
            "mfcc_mean":   float(np.mean(mfcc)),
            "mfcc_std":    float(np.std(mfcc)),
            "mfcc_1":      float(np.mean(mfcc[1])),
            "chroma_mean": float(np.mean(chroma)),
            "chroma_var":  float(np.var(chroma)),
            "rms":         energy_now,
            "centroid":    float(np.mean(centroid)),
            "bandwidth":   float(np.mean(bandwidth)),
            "zcr":         float(np.mean(zcr)),
            "mel_mean":    float(np.mean(mel)),
            "mfcc_vec":    np.mean(mfcc, axis=1).tolist(),
        }
        return feats, tempo

    def _build_features(self, agg: dict, tempos: list) -> dict:
        """Aggregate per-window features into final feature dict."""
        def _avg(k): return float(np.mean(agg[k]))
        tempo  = float(np.median(tempos))
        energy = _avg("rms")
        return {
            "mfcc_mean":   _avg("mfcc_mean"),
            "mfcc_std":    _avg("mfcc_std"),
            "mfcc_1":      _avg("mfcc_1"),
            "mfcc_vec":    np.mean(agg["mfcc_vec"], axis=0).tolist(),
            "chroma_mean": _avg("chroma_mean"),
            "chroma_var":  _avg("chroma_var"),
            "rms":         energy,
            "centroid":    _avg("centroid"),
            "bandwidth":   _avg("bandwidth"),
            "zcr":         _avg("zcr"),
            "tempo":       tempo,
            "bpm":         tempo,
            "energy":      energy,
            "mel_mean":    _avg("mel_mean"),
        }

    def _analyse(self):
        if not _LIBROSA_OK:
            log.warning("librosa not installed — audio analysis skipped.")
            return
        try:
            cfg = self._cfg.audio_analysis
            sr  = cfg.sample_rate
            win = 20

            info    = sf.SoundFile(self._path)
            total_s = info.frames / info.samplerate
            offsets = list(dict.fromkeys([
                max(0.0, total_s * 0.20),
                max(0.0, total_s * 0.50 - win / 2),
                max(0.0, total_s * 0.80 - win),
            ]))

            agg: dict[str, list] = {}
            tempos: list[float] = []
            for offset in offsets:
                y, _ = _librosa.load(self._path, sr=sr, offset=offset, duration=win, mono=True)
                if len(y) < 512:
                    continue
                feats, tempo = self._extract_window(y, sr, cfg)
                tempos.append(tempo)
                for k, v in feats.items():
                    agg.setdefault(k, []).append(v)

            if not agg:
                return

            features = self._build_features(agg, tempos)
            log.info(
                "Audio features — tempo:%.1f  energy:%.4f  zcr:%.4f  "
                "centroid:%.0f  mfcc_1:%.2f  chroma_var:%.4f",
                features["tempo"], features["energy"], features["zcr"],
                features["centroid"], features["mfcc_1"], features["chroma_var"],
            )
            self.sig_features.emit(features)
            self.sig_bpm.emit(features["tempo"])
            self.sig_energy.emit(features["energy"])

        except Exception as e:
            log.warning("Audio analysis error: %s", e)
            self.sig_error.emit(str(e))

    def stop(self):
        self._running = False
        self.wait(3000)
