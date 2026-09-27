"""Filesystem locations for settings, exports, screenshots and saves.

Defaults to the per-user application data folder of the current OS. Set the
``GRAVBOX_DATA_DIR`` environment variable (or pass ``--data-dir``) to override.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

APP_DIR_NAME = "GravBox"


def data_dir() -> Path:
    override = os.environ.get("GRAVBOX_DATA_DIR")
    if override:
        base = Path(override).expanduser()
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / APP_DIR_NAME
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "gravbox"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _subdir(name: str) -> Path:
    path = data_dir() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def exports_dir() -> Path:
    return _subdir("exports")


def screenshots_dir() -> Path:
    return _subdir("screenshots")


def saves_dir() -> Path:
    return _subdir("saves")


def settings_file() -> Path:
    return data_dir() / "settings.json"


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def open_in_file_manager(path: Path) -> bool:
    """Reveal a folder in Explorer / Finder / the desktop file manager."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return True
    except (OSError, AttributeError):
        return False
