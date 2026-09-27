"""GravBox: an interactive N-body gravity simulator.

An interactive, isolated-system N-body gravity sandbox with a tabbed control
panel, persistent orbit trails, live energy diagnostics, CSV export and an
OpenGL 3D view.
"""

import os as _os

# Must be set before pygame is imported anywhere in the package.
_os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
_os.environ.setdefault("SDL_VIDEO_CENTERED", "1")

__version__ = "1.0.0"
__app_name__ = "GravBox"

__all__ = ["__version__", "__app_name__"]
