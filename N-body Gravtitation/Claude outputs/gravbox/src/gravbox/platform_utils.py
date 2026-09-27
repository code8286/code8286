"""OS-specific setup that must run before the display is created."""

from __future__ import annotations

import os
import sys


def enable_high_dpi() -> None:
    """Make the process DPI-aware on Windows.

    Without this, Windows bitmap-scales the window at 125%/150% display
    scaling: it comes out blurry and larger than the requested size, which
    pushes it off-screen and distorts the apparent aspect ratio.
    """
    if sys.platform != "win32":
        return
    os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS", "permonitorv2")
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor aware
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:  # pragma: no cover - best effort only
        pass
