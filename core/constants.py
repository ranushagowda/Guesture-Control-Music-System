"""
core/constants.py
=================
All application-wide enumerations and constants.
Import from here — never hardcode strings across modules.
"""

from __future__ import annotations

from enum import Enum, auto


# ── Gesture Types ─────────────────────────────────────────────────────────────

class Gesture(Enum):
    NONE         = "None"
    OPEN_HAND    = "Open Hand"       # all 5 up            → Start Music
    FIST         = "Fist"            # all closed          → Stop Music
    INDEX_FINGER = "Index Finger"    # index only + swipe  → Vol Down/Up
    ROCK         = "Rock"            # index + pinky       → Previous Song
    TWO_FINGERS  = "Two Fingers"     # index + middle      → Next Song
    UNKNOWN      = "Unknown"


GESTURE_ACTIONS: dict[Gesture, str] = {
    Gesture.OPEN_HAND:    "Start / Resume Music",
    Gesture.FIST:         "Stop Music",
    Gesture.INDEX_FINGER: "Swipe R→L=Vol−  L→R=Vol+",
    Gesture.ROCK:         "Next Song",
    Gesture.TWO_FINGERS:  "Previous Song",
    Gesture.NONE:         "—",
    Gesture.UNKNOWN:      "—",
}


# ── Music Mood Categories ─────────────────────────────────────────────────────

class Mood(Enum):
    CALM      = "Calm"
    RELAXED   = "Relaxed"
    HAPPY     = "Happy"
    ENERGETIC = "Energetic"
    SAD       = "Sad"
    FOCUS     = "Focus"
    UNKNOWN   = "Unknown"


# ── Mood → Ambient RGB colour ─────────────────────────────────────────────────
# These are the target RGB values for the cabin lighting.
# The cabin engine interpolates smoothly between them.

MOOD_COLORS: dict[Mood, tuple[int, int, int]] = {
    Mood.CALM:      (30,  80,  180),   # soft blue
    Mood.RELAXED:   (40,  160, 80),    # soft green
    Mood.HAPPY:     (255, 200, 40),    # warm yellow
    Mood.ENERGETIC: (160, 30,  220),   # purple
    Mood.SAD:       (20,  40,  120),   # dim blue
    Mood.FOCUS:     (180, 220, 255),   # soft white-blue
    Mood.UNKNOWN:   (60,  60,  80),    # neutral grey-blue
}

MOOD_DESCRIPTIONS: dict[Mood, str] = {
    Mood.CALM:      "Soft Blue — Calm & Peaceful",
    Mood.RELAXED:   "Soft Green — Relaxed & Easy",
    Mood.HAPPY:     "Warm Yellow — Happy & Bright",
    Mood.ENERGETIC: "Purple — High Energy",
    Mood.SAD:       "Dim Blue — Melancholic",
    Mood.FOCUS:     "White-Blue — Focus Mode",
    Mood.UNKNOWN:   "Neutral — Analysing...",
}


# ── Playback States ───────────────────────────────────────────────────────────

class PlaybackState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED  = auto()
    LOADING = auto()


# ── System Component States ───────────────────────────────────────────────────

class ComponentState(Enum):
    INACTIVE    = "INACTIVE"
    INITIALISING = "INITIALISING"
    ACTIVE      = "ACTIVE"
    ERROR       = "ERROR"
    WARNING     = "WARNING"


# ── Drive Modes ───────────────────────────────────────────────────────────────

class DriveMode(Enum):
    ECO     = "ECO"
    COMFORT = "COMFORT"
    SPORT   = "SPORT"
    SPORT_PLUS = "SPORT+"


# ── Audio Feature Keys ────────────────────────────────────────────────────────
# Used as dictionary keys when passing feature vectors between modules.

class AudioFeature(Enum):
    MFCC              = "mfcc"
    MEL_SPECTROGRAM   = "mel_spectrogram"
    RMS_ENERGY        = "rms_energy"
    SPECTRAL_CENTROID = "spectral_centroid"
    SPECTRAL_BANDWIDTH= "spectral_bandwidth"
    ZERO_CROSSING_RATE= "zero_crossing_rate"
    CHROMA            = "chroma"
    TEMPO             = "tempo"
    BPM               = "bpm"
    ENERGY            = "energy"


# ── Application-wide numeric constants ───────────────────────────────────────

MIN_VOLUME: float = 0.0
MAX_VOLUME: float = 1.0
VOLUME_STEP: float = 0.05

MIN_GESTURE_CONFIDENCE: float = 0.0
MAX_GESTURE_CONFIDENCE: float = 1.0

# MediaPipe landmark indices
WRIST          = 0
THUMB_CMC      = 1
THUMB_MCP      = 2
THUMB_IP       = 3
THUMB_TIP      = 4
INDEX_MCP      = 5
INDEX_PIP      = 6
INDEX_DIP      = 7
INDEX_TIP      = 8
MIDDLE_MCP     = 9
MIDDLE_PIP     = 10
MIDDLE_DIP     = 11
MIDDLE_TIP     = 12
RING_MCP       = 13
RING_PIP       = 14
RING_DIP       = 15
RING_TIP       = 16
PINKY_MCP      = 17
PINKY_PIP      = 18
PINKY_DIP      = 19
PINKY_TIP      = 20
