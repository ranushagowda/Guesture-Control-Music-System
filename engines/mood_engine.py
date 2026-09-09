"""
engines/mood_engine.py  —  Phase 8
=====================================
Music mood classifier.

Strategy
--------
1. If a trained sklearn model exists at data/models/mood_classifier.pkl → use it.
2. Otherwise fall back to a deterministic rule-based heuristic that maps
   (tempo, energy, zcr, centroid) → one of 6 moods.
   This means the system works out-of-the-box with zero training data.

Moods: Calm | Relaxed | Happy | Energetic | Sad | Focus

Emits
-----
sig_mood(mood_str, confidence, color_rgb_tuple)
"""
from __future__ import annotations
import os
import numpy as np
from PySide6.QtCore import QObject, Signal
from core.constants import Mood, MOOD_COLORS
from core.logger    import get_logger

log = get_logger(__name__)


def _rule_based(features: dict) -> tuple[Mood, float]:
    """Hard decision tree — clear thresholds, no overlapping score ranges."""
    tempo    = features.get("tempo",    120.0)
    energy   = features.get("energy",  0.05)
    zcr      = features.get("zcr",     0.05)
    centroid = features.get("centroid", 2000.0)
    mfcc_1   = features.get("mfcc_1",  0.0)
    chroma_v = features.get("chroma_var", 0.01)

    log.info(
        "Classifying — tempo:%.1f energy:%.4f zcr:%.4f centroid:%.0f mfcc_1:%.2f chroma_var:%.4f",
        tempo, energy, zcr, centroid, mfcc_1, chroma_v,
    )

    # ── Tier 1: ENERGETIC — fast AND loud, no ambiguity ──────────────────────
    if tempo >= 128 and energy >= 0.08:
        return Mood.ENERGETIC, 0.92

    # ── Tier 2: HAPPY — upbeat + bright + danceable ───────────────────────────
    if tempo >= 108 and energy >= 0.05 and zcr >= 0.04:
        return Mood.HAPPY, 0.88

    # ── Tier 3: SAD — slow + dark timbre (mfcc_1 negative = darker sound) ────
    # mfcc_1 < 0 means darker/more minor-key timbre
    if tempo < 90 and mfcc_1 < 0 and energy < 0.12:
        return Mood.SAD, 0.87

    # ── Tier 4: CALM — slow + very quiet + low zcr ───────────────────────────
    if tempo < 95 and energy < 0.06 and zcr < 0.05:
        return Mood.CALM, 0.85

    # ── Tier 5: FOCUS — steady moderate tempo + low zcr + bright centroid ────
    if 88 <= tempo <= 130 and zcr < 0.05 and centroid > 2000:
        return Mood.FOCUS, 0.82

    # ── Tier 6: RELAXED — everything else that is moderate and not intense ───
    if energy < 0.12:
        return Mood.RELAXED, 0.78

    # Fallback
    return Mood.CALM, 0.60



class MoodEngine(QObject):
    sig_mood = Signal(str, float, tuple)   # mood_name, confidence, (r,g,b)

    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self._cfg   = cfg
        self._model = None
        self._scaler= None
        self._load_model()

    def _load_model(self):
        model_path  = self._cfg.mood.model_path
        scaler_path = self._cfg.mood.scaler_path
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                import joblib
                self._model  = joblib.load(model_path)
                self._scaler = joblib.load(scaler_path)
                log.info("Mood model loaded from %s", model_path)
            except Exception as e:
                log.warning("Could not load mood model: %s — using heuristic.", e)
        else:
            log.info("No mood model found — using rule-based heuristic.")

    def classify(self, features: dict):
        """Classify features and emit sig_mood."""
        try:
            if self._model and self._scaler:
                mood, conf = self._ml_classify(features)
            else:
                mood, conf = _rule_based(features)

            color = MOOD_COLORS.get(mood, (60, 60, 80))
            self.sig_mood.emit(mood.value, conf, color)
            log.debug("Mood: %s (%.0f%%)", mood.value, conf * 100)

        except Exception as e:
            log.warning("Mood classification error: %s", e)
            color = MOOD_COLORS[Mood.UNKNOWN]
            self.sig_mood.emit(Mood.UNKNOWN.value, 0.5, color)

    def _ml_classify(self, features: dict) -> tuple[Mood, float]:
        vec = np.array([
            features.get("mfcc_mean", 0),
            features.get("mfcc_std",  0),
            features.get("chroma_mean", 0),
            features.get("rms",       0),
            features.get("centroid",  0),
            features.get("bandwidth", 0),
            features.get("zcr",       0),
            features.get("tempo",     120),
            features.get("energy",    0),
        ]).reshape(1, -1)

        vec_scaled = self._scaler.transform(vec)
        label      = self._model.predict(vec_scaled)[0]
        proba      = self._model.predict_proba(vec_scaled)[0]
        conf       = float(np.max(proba))

        # Map label string → Mood enum
        for m in Mood:
            if m.value.lower() == str(label).lower():
                return m, conf
        return Mood.UNKNOWN, conf
