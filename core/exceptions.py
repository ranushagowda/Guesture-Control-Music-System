"""
core/exceptions.py
==================
Custom exception hierarchy for the AI Cabin Experience application.

Every subsystem raises a specific exception type so that callers can
catch exactly what they need without swallowing unrelated errors.

Hierarchy
---------
AICabinError (base)
├── ConfigurationError
├── CameraError
├── GestureEngineError
├── MusicEngineError
│   ├── SongNotFoundError
│   └── UnsupportedFormatError
├── AudioAnalysisError
├── MoodClassifierError
│   └── ModelNotFoundError
├── CabinEngineError
├── VehicleSimulatorError
└── GUIError
"""


class AICabinError(Exception):
    """Base exception for all AI Cabin Experience errors."""

    def __init__(self, message: str, details: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# ── Configuration ─────────────────────────────────────────────────────────────

class ConfigurationError(AICabinError):
    """Raised when the configuration file is missing, malformed or invalid."""


# ── Camera ────────────────────────────────────────────────────────────────────

class CameraError(AICabinError):
    """Raised when the webcam cannot be opened or a frame cannot be read."""


# ── Gesture Engine ────────────────────────────────────────────────────────────

class GestureEngineError(AICabinError):
    """Raised when gesture recognition encounters an unrecoverable error."""


# ── Music Engine ──────────────────────────────────────────────────────────────

class MusicEngineError(AICabinError):
    """Base class for music engine errors."""


class SongNotFoundError(MusicEngineError):
    """Raised when a requested song file does not exist on disk."""

    def __init__(self, path: str) -> None:
        super().__init__(
            message=f"Song file not found: {path}",
            details="Ensure the file exists in the Song/ directory.",
        )
        self.path = path


class UnsupportedFormatError(MusicEngineError):
    """Raised when an audio file has an unsupported format."""

    def __init__(self, path: str, supported: list[str]) -> None:
        super().__init__(
            message=f"Unsupported audio format: {path}",
            details=f"Supported formats: {', '.join(supported)}",
        )
        self.path = path
        self.supported = supported


class EmptyMusicLibraryError(MusicEngineError):
    """Raised when the Song/ directory contains no playable audio files."""

    def __init__(self, directory: str) -> None:
        super().__init__(
            message=f"No playable audio files found in: {directory}",
            details="Add .mp3, .wav, .ogg or .flac files to the Song/ folder.",
        )
        self.directory = directory


# ── Audio Analysis ────────────────────────────────────────────────────────────

class AudioAnalysisError(AICabinError):
    """Raised when Librosa audio feature extraction fails."""


# ── Mood Classifier ───────────────────────────────────────────────────────────

class MoodClassifierError(AICabinError):
    """Base class for mood classifier errors."""


class ModelNotFoundError(MoodClassifierError):
    """Raised when the trained ML model file is not found."""

    def __init__(self, path: str) -> None:
        super().__init__(
            message=f"ML model not found: {path}",
            details="Run the training script first or place the model file in data/models/.",
        )
        self.path = path


# ── Cabin Engine ──────────────────────────────────────────────────────────────

class CabinEngineError(AICabinError):
    """Raised when the cabin ambience engine encounters an error."""


# ── Vehicle Simulator ─────────────────────────────────────────────────────────

class VehicleSimulatorError(AICabinError):
    """Raised when the vehicle simulator encounters an error."""


# ── GUI ───────────────────────────────────────────────────────────────────────

class GUIError(AICabinError):
    """Raised when a GUI component fails to initialise or render."""
