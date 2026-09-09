"""
config/config_manager.py
========================
Loads settings.yaml and exposes a typed, dot-accessible configuration object.
Validates required keys and provides safe defaults for optional ones.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml


class _DotDict(dict):
    """A dict subclass that allows attribute-style access (cfg.key.subkey)."""

    def __getattr__(self, key: str) -> Any:
        try:
            val = self[key]
            return _DotDict(val) if isinstance(val, dict) else val
        except KeyError:
            raise AttributeError(f"Configuration key '{key}' not found.")

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


class ConfigManager:
    """
    Singleton configuration manager.

    Usage
    -----
    from config.config_manager import get_config
    cfg = get_config()
    print(cfg.app.name)
    print(cfg.camera.width)
    """

    _instance: ConfigManager | None = None
    _config: _DotDict | None = None

    # Default config path relative to project root
    _DEFAULT_PATH = Path(__file__).parent / "settings.yaml"

    def __new__(cls) -> ConfigManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, path: str | Path | None = None) -> _DotDict:
        """Load and validate the YAML config file."""
        config_path = Path(path) if path else self._DEFAULT_PATH

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                "Ensure settings.yaml exists in the config/ directory."
            )

        with open(config_path, "r", encoding="utf-8") as fh:
            raw: dict = yaml.safe_load(fh) or {}

        self._config = _DotDict(raw)
        self._validate()
        self._resolve_paths()
        return self._config

    def get(self) -> _DotDict:
        """Return the loaded config. Loads default if not yet loaded."""
        if self._config is None:
            self.load()
        return self._config

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate(self) -> None:
        required_sections = ["app", "music", "camera", "hand_tracking",
                              "gesture", "audio_analysis", "mood",
                              "cabin", "vehicle", "gui"]
        for section in required_sections:
            if section not in self._config:
                raise ValueError(
                    f"Missing required config section: '{section}'. "
                    "Check config/settings.yaml."
                )

        # Volume range
        vol = self._config["music"].get("default_volume", 0.6)
        if not (0.0 <= vol <= 1.0):
            raise ValueError(f"music.default_volume must be 0.0–1.0, got {vol}")

        # Confidence thresholds
        for key in ("min_detection_confidence", "min_tracking_confidence"):
            val = self._config["hand_tracking"].get(key, 0.75)
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"hand_tracking.{key} must be 0.0–1.0, got {val}")

    # ── Path Resolution ───────────────────────────────────────────────────────

    def _resolve_paths(self) -> None:
        """Convert relative paths in config to absolute paths from project root."""
        root = Path(__file__).parent.parent.resolve()

        _ALLOWED_SUBDIRS = {"Song", "data", "logs"}

        def _safe_join(base: Path, rel: str) -> str:
            resolved = (base / rel).resolve()
            if not str(resolved).startswith(str(base)):
                raise ValueError(f"Path '{rel}' escapes project root.")
            return str(resolved)

        music_cfg = self._config["music"]
        music_cfg["song_dir"] = _safe_join(root, music_cfg.get("song_dir", "Song"))

        mood_cfg = self._config["mood"]
        mood_cfg["model_path"]  = _safe_join(root, mood_cfg.get("model_path",  "data/models/mood_classifier.pkl"))
        mood_cfg["scaler_path"] = _safe_join(root, mood_cfg.get("scaler_path", "data/models/feature_scaler.pkl"))

        app_cfg = self._config["app"]
        app_cfg["log_dir"] = _safe_join(root, app_cfg.get("log_dir", "logs"))


# ── Module-level convenience accessor ────────────────────────────────────────

_manager = ConfigManager()


def get_config() -> _DotDict:
    """Return the global configuration object (loads on first call)."""
    return _manager.get()


def reload_config(path: str | Path | None = None) -> _DotDict:
    """Force-reload the configuration from disk."""
    return _manager.load(path)
