"""
utils/file_utils.py
===================
File system helpers used across the application.
"""

from __future__ import annotations
from pathlib import Path
from typing import List
from core.logger import get_logger

log = get_logger(__name__)

_ALLOWED_AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".aac"}


def scan_audio_files(directory: str, extensions: list[str]) -> List[Path]:
    folder = Path(directory).resolve()
    if not folder.exists():
        log.warning("Music directory does not exist: %s", folder)
        return []

    exts = {e.lower() for e in extensions} & _ALLOWED_AUDIO_EXTS
    found: List[Path] = []
    for p in folder.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            if str(p.resolve()).startswith(str(folder)):
                found.append(p)

    found.sort()
    log.info("Found %d audio file(s) in '%s'", len(found), folder)
    return found


def ensure_directory(path: str | Path) -> Path:
    """Create *path* (and parents) if it does not exist. Returns the Path."""
    p = Path(path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def file_size_mb(path: str | Path) -> float:
    """Return the size of *path* in megabytes, or 0.0 if not found."""
    try:
        return Path(path).resolve().stat().st_size / (1024 * 1024)
    except OSError:
        return 0.0


def short_name(path: str | Path, max_len: int = 40) -> str:
    """Return the stem of *path*, truncated to *max_len* chars if necessary."""
    stem = Path(path).stem
    if len(stem) > max_len:
        return stem[: max_len - 2] + "…"
    return stem
