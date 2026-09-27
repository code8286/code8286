"""Application settings with tolerant JSON persistence.

Settings are plain dataclasses so they are easy to test and serialise. Loading
never raises: unknown keys are ignored, bad values fall back to defaults and
everything is clamped to a safe range by :meth:`Settings.validate`.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

TARGET_FPS = 120
MIN_WINDOW_SIZE = (960, 600)
DEFAULT_ASPECT = 16 / 9

INTEGRATOR_LABELS = {"euler": "Euler", "leapfrog": "Leapfrog", "rk4": "RK4"}
SPAWN_MODE_LABELS = {"orbit": "Orbit", "random": "Random", "still": "Still"}


@dataclass
class SimConfig:
    """Physics and time-stepping parameters."""

    gravity: float = 1.0
    softening: float = 2.0
    timestep: float = 0.005
    substeps: int = 8
    damping: float = 1.0
    integrator: str = "leapfrog"
    merge_on_collision: bool = False
    auto_throttle: bool = True
    step_budget_ms: float = 10.0
    max_bodies: int = 400


@dataclass
class SpawnConfig:
    """How bodies placed with the mouse are created."""

    mass: float = 5.0
    speed: float = 10.0
    mode: str = "orbit"
    drag_scale: float = 0.1  # velocity per world unit of mouse drag


@dataclass
class ViewConfig:
    """Rendering toggles."""

    show_trails: bool = True
    trail_width: int = 1
    show_grid: bool = True
    show_stats: bool = True
    show_velocity: bool = False
    show_com: bool = False
    perturb_on_3d: bool = True
    panel_visible: bool = True


@dataclass
class WindowConfig:
    """Window geometry. A width/height of 0 means 'fit to the desktop'."""

    width: int = 0
    height: int = 0
    fullscreen: bool = False


def _coerce(value: Any, default: Any) -> Any:
    kind = type(default)
    try:
        if kind is bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "on")
            return default
        if kind is int:
            if isinstance(value, bool):
                return default
            return int(value)
        if kind is float:
            if isinstance(value, bool):
                return default
            out = float(value)
            return out if math.isfinite(out) else default
        if kind is str:
            return str(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return default


def _update_dataclass(obj: Any, data: Any) -> None:
    if not isinstance(data, dict):
        return
    for f in fields(obj):
        if f.name in data:
            setattr(obj, f.name, _coerce(data[f.name], getattr(obj, f.name)))


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@dataclass
class Settings:
    sim: SimConfig = field(default_factory=SimConfig)
    spawn: SpawnConfig = field(default_factory=SpawnConfig)
    view: ViewConfig = field(default_factory=ViewConfig)
    window: WindowConfig = field(default_factory=WindowConfig)

    def validate(self) -> Settings:
        s = self.sim
        s.gravity = _clamp(s.gravity, 1e-4, 1e4)
        s.softening = _clamp(s.softening, 0.01, 1000.0)
        s.timestep = _clamp(s.timestep, 1e-5, 1.0)
        s.substeps = int(_clamp(s.substeps, 1, 256))
        s.damping = _clamp(s.damping, 0.9, 1.0)
        s.step_budget_ms = _clamp(s.step_budget_ms, 1.0, 200.0)
        s.max_bodies = int(_clamp(s.max_bodies, 2, 5000))
        if s.integrator not in INTEGRATOR_LABELS:
            s.integrator = "leapfrog"

        sp = self.spawn
        sp.mass = _clamp(sp.mass, 1e-3, 1e7)
        sp.speed = _clamp(sp.speed, 0.0, 1e4)
        sp.drag_scale = _clamp(sp.drag_scale, 1e-4, 100.0)
        if sp.mode not in SPAWN_MODE_LABELS:
            sp.mode = "orbit"

        self.view.trail_width = int(_clamp(self.view.trail_width, 1, 8))
        self.window.width = max(0, int(self.window.width))
        self.window.height = max(0, int(self.window.height))
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Any) -> Settings:
        settings = cls()
        if isinstance(data, dict):
            for name in ("sim", "spawn", "view", "window"):
                _update_dataclass(getattr(settings, name), data.get(name))
        return settings.validate()

    @classmethod
    def load(cls, path: Path) -> Settings:
        try:
            with open(path, encoding="utf-8") as fh:
                return cls.from_dict(json.load(fh))
        except (OSError, ValueError):
            return cls()

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        tmp.replace(path)
