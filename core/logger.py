"""
core/logger.py
==============
Structured logging system for the AI Cabin Experience application.

Features
--------
- Colour-coded console output (DEBUG=cyan, INFO=green, WARNING=yellow,
  ERROR=red, CRITICAL=bold red)
- Rotating file handler (10 MB per file, 5 backups)
- Per-module named loggers
- Single initialisation call from main.py

Usage
-----
from core.logger import get_logger
log = get_logger(__name__)
log.info("System started")
log.debug("Camera frame received")
log.error("Audio file not found: %s", path)
"""

from __future__ import annotations
from pathlib import Path
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# ── ANSI colour codes ─────────────────────────────────────────────────────────
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_CYAN   = "\033[36m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_BRED   = "\033[1;31m"

_LEVEL_COLORS = {
    logging.DEBUG:    _CYAN,
    logging.INFO:     _GREEN,
    logging.WARNING:  _YELLOW,
    logging.ERROR:    _RED,
    logging.CRITICAL: _BRED,
}


class _ColorFormatter(logging.Formatter):
    """Console formatter that adds ANSI colour to the level name."""

    FMT = "{asctime} | {color}{levelname:<8}{reset} | {name:<30} | {message}"
    DATEFMT = "%H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, _RESET)
        fmt = self.FMT.format(
            asctime="%(asctime)s",
            color=color,
            levelname="%(levelname)s",
            reset=_RESET,
            name="%(name)s",
            message="%(message)s",
        )
        formatter = logging.Formatter(fmt, datefmt=self.DATEFMT, style="%")
        return formatter.format(record)


class _PlainFormatter(logging.Formatter):
    """Plain formatter for file output (no ANSI codes)."""

    FMT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
    DATEFMT = "%Y-%m-%d %H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self.FMT, datefmt=self.DATEFMT)


# ── Initialisation ────────────────────────────────────────────────────────────

_initialized: list[bool] = [False]  # use list to avoid global mutation warning


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_dir: str = "logs",
) -> None:
    if _initialized[0]:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Remove any default handlers
    root.handlers.clear()

    # ── Console handler ───────────────────────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(numeric_level)
    # Always use plain ASCII formatter to avoid cp1252 encoding issues on Windows
    console.setFormatter(_PlainFormatter())
    root.addHandler(console)

    # ── File handler ──────────────────────────────────────────────────────────
    if log_to_file:
        log_path = Path(log_dir).resolve()
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=str(log_path / "ai_cabin.log"),
            maxBytes=10 * 1024 * 1024,   # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(_PlainFormatter())
        root.addHandler(file_handler)

    # Suppress noisy third-party loggers
    for noisy in ("PIL", "matplotlib", "urllib3", "mediapipe", "absl"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _initialized[0] = True

    # First log entry
    log = logging.getLogger("core.logger")
    log.info("=" * 60)
    log.info("AI Cabin Experience — Logging Initialised")
    log.info("Level: %s | File logging: %s | Log dir: %s", level, log_to_file, log_dir)
    log.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.  Always use this instead of logging.getLogger()
    directly so that the module name is consistently formatted.

    Parameters
    ----------
    name : Typically __name__ of the calling module
    """
    return logging.getLogger(name)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ansi_supported() -> bool:
    """Check if the Windows terminal supports ANSI escape codes."""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        # Enable VIRTUAL_TERMINAL_PROCESSING (0x0004)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        return True
    except Exception:
        return False
