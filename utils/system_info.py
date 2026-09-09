"""
utils/system_info.py
====================
System diagnostics — checks Python version, installed packages,
camera availability and disk space at application startup.

Called once from main.py to give the engineer a clear picture of
the runtime environment before any engine is started.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
import importlib
import platform
import sys
from core.logger import get_logger

log = get_logger(__name__)


@dataclass
class SystemReport:
    python_version: str = ""
    platform_info: str = ""
    packages: Dict[str, str] = field(default_factory=dict)   # name → version / status
    camera_available: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if no critical errors were found."""
        return len(self.errors) == 0


# ── Required packages and their import names ─────────────────────────────────

_REQUIRED = {
    "PySide6":      "PySide6",
    "cv2":          "cv2",
    "numpy":        "numpy",
    "sounddevice":  "sounddevice",
    "soundfile":    "soundfile",
    "yaml":         "yaml",
}

_OPTIONAL = {
    "mediapipe":    "mediapipe",
    "librosa":      "librosa",
    "sklearn":      "sklearn",
    "pandas":       "pandas",
    "matplotlib":   "matplotlib",
    "torch":        "torch",
    "pyqtgraph":    "pyqtgraph",
    "speech_recognition": "speech_recognition",
}


def run_diagnostics() -> SystemReport:
    """
    Run all system checks and return a SystemReport.
    Logs a formatted summary automatically.
    """
    report = SystemReport()

    # ── Python version ────────────────────────────────────────────────────────
    report.python_version = sys.version
    report.platform_info  = f"{platform.system()} {platform.release()} ({platform.machine()})"

    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 10):
        report.errors.append(
            f"Python 3.10+ required, found {major}.{minor}. "
            "Please upgrade your Python installation."
        )

    # ── Required packages ─────────────────────────────────────────────────────
    for display_name, import_name in _REQUIRED.items():
        version = _check_package(import_name)
        report.packages[display_name] = version
        if version == "NOT INSTALLED":
            report.errors.append(
                f"Required package '{display_name}' is not installed. "
                f"Run: pip install {display_name}"
            )

    # ── Optional packages ─────────────────────────────────────────────────────
    for display_name, import_name in _OPTIONAL.items():
        version = _check_package(import_name)
        report.packages[f"{display_name} (optional)"] = version
        if version == "NOT INSTALLED":
            report.warnings.append(
                f"Optional package '{display_name}' not installed — "
                "some features will be disabled."
            )

    # ── Camera check ──────────────────────────────────────────────────────────
    report.camera_available = _check_camera()
    if not report.camera_available:
        report.warnings.append(
            "No camera detected at index 0. "
            "Gesture control will be unavailable."
        )

    # ── Log the report ────────────────────────────────────────────────────────
    _log_report(report)
    return report


def _check_package(import_name: str) -> str:
    """Try to import a package and return its version string or 'NOT INSTALLED'."""
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, "__version__", "installed")
        return str(version)
    except Exception:
        if import_name in sys.modules:
            mod = sys.modules[import_name]
            return str(getattr(mod, "__version__", "installed"))
        return "NOT INSTALLED"


def _check_camera() -> bool:
    """Skip live camera open — camera_engine will handle it."""
    return _check_package("cv2") != "NOT INSTALLED"


def _log_report(report: SystemReport) -> None:
    """Write a formatted diagnostics summary to the log."""
    sep = "-" * 56

    log.info(sep)
    log.info("  SYSTEM DIAGNOSTICS")
    log.info(sep)
    log.info("  Python  : %s", report.python_version.split()[0])
    log.info("  Platform: %s", report.platform_info)
    log.info("  Camera  : %s", "AVAILABLE" if report.camera_available else "NOT FOUND")
    log.info(sep)
    log.info("  PACKAGES")

    for name, status in report.packages.items():
        icon = "[OK]" if status not in ("NOT INSTALLED",) else "[--]"
        log.info("  %s  %-35s %s", icon, name, status)

    if report.warnings:
        log.info(sep)
        log.info("  WARNINGS")
        for w in report.warnings:
            log.warning("  [!]  %s", w)

    if report.errors:
        log.info(sep)
        log.info("  ERRORS")
        for e in report.errors:
            log.error("  [X]  %s", e)

    log.info(sep)
    status_str = "PASS" if report.ok else "FAIL - see errors above"
    log.info("  DIAGNOSTICS RESULT: %s", status_str)
    log.info(sep)
