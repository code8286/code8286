"""2D and 3D cameras (pure math, no pygame/OpenGL dependency).

The 2D camera maps world units to pixels with a single uniform zoom factor,
so the simulation can never be stretched: resizing the window only changes
how much of the world is visible.
"""

from __future__ import annotations

import math

import numpy as np


def nice_step(raw: float) -> float:
    """Round ``raw`` up to 1, 2 or 5 times a power of ten (for grid spacing)."""
    if raw <= 0 or not math.isfinite(raw):
        return 1.0
    exp = math.floor(math.log10(raw))
    base = raw / 10 ** exp
    for m in (1.0, 2.0, 5.0, 10.0):
        if base <= m + 1e-9:
            return m * 10 ** exp
    return 10.0 ** (exp + 1)


class Camera2D:
    MIN_ZOOM = 1e-4
    MAX_ZOOM = 1e3

    def __init__(self) -> None:
        self.cx = 0.0
        self.cy = 0.0
        self.zoom = 1.0  # pixels per world unit
        self.w = 1
        self.h = 1

    def set_viewport(self, w: int, h: int) -> None:
        self.w, self.h = max(1, int(w)), max(1, int(h))

    def state(self) -> tuple:
        return (self.cx, self.cy, self.zoom, self.w, self.h)

    def world_to_screen(self, x: float, y: float):
        return (self.w * 0.5 + (x - self.cx) * self.zoom, self.h * 0.5 - (y - self.cy) * self.zoom)

    def world_to_screen_arr(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        sx = self.w * 0.5 + (x - self.cx) * self.zoom
        sy = self.h * 0.5 - (y - self.cy) * self.zoom
        return np.stack([sx, sy], axis=-1)

    def screen_to_world(self, sx: float, sy: float):
        return (self.cx + (sx - self.w * 0.5) / self.zoom, self.cy - (sy - self.h * 0.5) / self.zoom)

    def zoom_at(self, sx: float, sy: float, factor: float) -> None:
        """Zoom while keeping the world point under the cursor fixed."""
        wx, wy = self.screen_to_world(sx, sy)
        self.zoom = min(self.MAX_ZOOM, max(self.MIN_ZOOM, self.zoom * factor))
        self.cx = wx - (sx - self.w * 0.5) / self.zoom
        self.cy = wy + (sy - self.h * 0.5) / self.zoom

    def pan_pixels(self, dx: float, dy: float) -> None:
        self.cx -= dx / self.zoom
        self.cy += dy / self.zoom

    def fit(self, xmin: float, xmax: float, ymin: float, ymax: float, margin: float = 0.12) -> None:
        self.cx = 0.5 * (xmin + xmax)
        self.cy = 0.5 * (ymin + ymax)
        span_x = max(xmax - xmin, 1e-6) * (1 + 2 * margin)
        span_y = max(ymax - ymin, 1e-6) * (1 + 2 * margin)
        self.zoom = min(self.MAX_ZOOM, max(self.MIN_ZOOM, min(self.w / span_x, self.h / span_y)))


class Camera3D:
    """Orbit camera around a target point. World ``z`` is 'up'."""

    def __init__(self) -> None:
        self.yaw = -60.0
        self.pitch = 35.0
        self.dist = 800.0
        self.fov = 55.0
        self.target = np.zeros(3)

    def eye(self) -> np.ndarray:
        yaw, pitch = math.radians(self.yaw), math.radians(self.pitch)
        cp = math.cos(pitch)
        offset = np.array([cp * math.cos(yaw), cp * math.sin(yaw), math.sin(pitch)])
        return self.target + self.dist * offset

    def orbit(self, dx: float, dy: float, sensitivity: float = 0.35) -> None:
        self.yaw -= dx * sensitivity
        self.pitch = max(-89.0, min(89.0, self.pitch + dy * sensitivity))

    def zoom(self, factor: float) -> None:
        self.dist = max(1.0, min(1e6, self.dist / factor))

    def pan(self, dx: float, dy: float, viewport_h: int) -> None:
        forward = self.target - self.eye()
        forward /= np.linalg.norm(forward)
        right = np.cross(forward, np.array([0.0, 0.0, 1.0]))
        norm = np.linalg.norm(right)
        right = right / norm if norm > 1e-9 else np.array([1.0, 0.0, 0.0])
        up = np.cross(right, forward)
        scale = 2.0 * self.dist * math.tan(math.radians(self.fov) / 2) / max(1, viewport_h)
        self.target = self.target + (-dx * right + dy * up) * scale

    def fit(self, radius: float) -> None:
        self.target = np.zeros(3)
        self.dist = max(radius, 1.0) / math.sin(math.radians(self.fov) / 2) * 1.1
