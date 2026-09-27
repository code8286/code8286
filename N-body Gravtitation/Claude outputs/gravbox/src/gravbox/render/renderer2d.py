"""Top-down pygame renderer.

Background, grid and trails are baked into a cached layer. While the camera
is still, only the newest trail segments are drawn onto it each frame, so
trails of any length cost almost nothing. The layer is rebuilt from the
world-space trail history only when the view changes (pan, zoom, resize).
"""

from __future__ import annotations

import math
import random

import numpy as np
import pygame

from gravbox.render.camera import nice_step
from gravbox.ui.theme import Colors

COORD_LIMIT = 30000.0  # keep coordinates within what SDL can rasterise
VELOCITY_SCALE = 2.0   # velocity arrows show 2 time units of travel


def _starfield(surface, seed: int = 7) -> None:
    """Deterministic screen-space stars (drawn behind the grid and trails)."""
    w, h = surface.get_size()
    rng = random.Random(seed)
    for _ in range(max(1, w * h // 2600)):
        a = rng.random()
        c = int(40 + a * a * 170)
        x, y = rng.randrange(w), rng.randrange(h)
        if a > 0.97:
            pygame.draw.circle(surface, (c, c, min(255, c + 12)), (x, y), 1)
        else:
            surface.fill((c, c, min(255, c + 10)), (x, y, 1, 1))


def _shade(color, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def _lighten(color, amount=0.35):
    return tuple(int(c + (255 - c) * amount) for c in color)


class Renderer2D:
    def __init__(self) -> None:
        self.layer = None
        self._key = None
        self._drawn = {}
        self._force = True
        self.line_scale = 1
        self._glow = {}

    def invalidate(self) -> None:
        self._force = True

    # ---------------------------------------------------------------- frame
    def draw(self, target: pygame.Surface, cam, system, trails, view, line_scale: int = 1) -> None:
        size = target.get_size()
        if line_scale != self.line_scale:
            self.line_scale = line_scale
            self._force = True
        cam.set_viewport(*size)
        key = (size, cam.state(), trails.version, view.show_grid, view.show_trails, int(view.trail_width))
        if self.layer is None or self.layer.get_size() != size:
            self.layer = pygame.Surface(size)
            self._force = True
        if self._force or key != self._key:
            self._full_redraw(cam, trails, view)
            self._key = key
            self._force = False
        elif view.show_trails and not self._incremental(cam, trails, view):
            self._full_redraw(cam, trails, view)
        target.blit(self.layer, (0, 0))
        self._draw_bodies(target, cam, system, view)
        if view.show_com and system.n:
            self._draw_com(target, cam, system)

    # --------------------------------------------------------------- layers
    def _full_redraw(self, cam, trails, view) -> None:
        self.layer.fill(Colors.CANVAS)
        _starfield(self.layer)
        if view.show_grid:
            self._draw_grid(cam)
        self._drawn = {}
        if not view.show_trails:
            return
        width = max(1, int(view.trail_width)) * self.line_scale
        for uid, trail in trails.trails.items():
            if trail.count >= 2:
                self._draw_polyline(cam, trail, 0, trail.count, width)
            self._drawn[uid] = (trail.version, trail.count)

    def _incremental(self, cam, trails, view) -> bool:
        """Draw only new segments. Returns False if a full redraw is needed."""
        width = max(1, int(view.trail_width)) * self.line_scale
        for uid, trail in trails.trails.items():
            version, drawn = self._drawn.get(uid, (trail.version, 0))
            if version != trail.version:
                return False
            if trail.count > drawn:
                start = max(drawn - 1, 0)
                if trail.count - start >= 2:
                    self._draw_polyline(cam, trail, start, trail.count, width)
                self._drawn[uid] = (trail.version, trail.count)
        return True

    def _draw_polyline(self, cam, trail, start, end, width) -> None:
        pts = trail.points[start:end]
        screen = cam.world_to_screen_arr(pts[:, 0].astype(float), pts[:, 1].astype(float))
        np.clip(screen, -COORD_LIMIT, COORD_LIMIT, out=screen)
        color = _shade(trail.color, 0.7 if trail.alive else 0.4)
        pygame.draw.lines(self.layer, color, False, screen.tolist(), width)

    def _draw_grid(self, cam) -> None:
        step = nice_step(90.0 / cam.zoom)
        x0, y1 = cam.screen_to_world(0, 0)
        x1, y0 = cam.screen_to_world(cam.w, cam.h)
        nx, ny = (x1 - x0) / step, (y1 - y0) / step
        if nx > 400 or ny > 400:
            return
        i = math.floor(x0 / step)
        while i * step <= x1:
            sx, _ = cam.world_to_screen(i * step, 0)
            color = Colors.AXIS if i == 0 else (Colors.GRID_MAJOR if i % 5 == 0 else Colors.GRID)
            pygame.draw.line(self.layer, color, (sx, 0), (sx, cam.h))
            i += 1
        j = math.floor(y0 / step)
        while j * step <= y1:
            _, sy = cam.world_to_screen(0, j * step)
            color = Colors.AXIS if j == 0 else (Colors.GRID_MAJOR if j % 5 == 0 else Colors.GRID)
            pygame.draw.line(self.layer, color, (0, sy), (cam.w, sy))
            j += 1

    # --------------------------------------------------------------- bodies
    def _draw_bodies(self, target, cam, system, view) -> None:
        if system.n == 0:
            return
        w, h = target.get_size()
        screen = cam.world_to_screen_arr(system.pos[:, 0], system.pos[:, 1])
        radii = np.maximum(system.radii() * cam.zoom, 3.0 * self.line_scale)
        cap = 2.0 * max(w, h)
        if view.show_velocity:
            tips = cam.world_to_screen_arr(system.pos[:, 0] + system.vel[:, 0] * VELOCITY_SCALE,
                                           system.pos[:, 1] + system.vel[:, 1] * VELOCITY_SCALE)
            np.clip(tips, -COORD_LIMIT, COORD_LIMIT, out=tips)
        for i, ((sx, sy), r, color) in enumerate(zip(screen.tolist(), radii.tolist(), system.colors)):
            if sx < -r or sy < -r or sx > w + r or sy > h + r:
                continue
            center = (int(sx), int(sy))
            radius = int(min(r, cap))
            if view.show_velocity:
                pygame.draw.line(target, _lighten(color, 0.2), center, tips[i].tolist(), 1)
            if radius >= 4:
                glow = self._glow_sprite(color, radius)
                target.blit(glow, (center[0] - glow.get_width() // 2, center[1] - glow.get_height() // 2))
            pygame.draw.circle(target, _shade(color, 0.55), center, radius)
            if radius >= 3:  # lit hemisphere + specular highlight, GravBox planet style
                off = max(1, radius // 4)
                pygame.draw.circle(target, color, (center[0] - off // 2, center[1] - off // 2), max(1, radius - off))
                pygame.draw.circle(target, _lighten(color, 0.7), (center[0] - off, center[1] - off),
                                   max(1, radius // 3))

    def _glow_sprite(self, color, radius):
        """Cached soft halo: concentric translucent discs."""
        radius = min(radius, 160)
        key = (color, radius)
        sprite = self._glow.get(key)
        if sprite is None:
            size = radius * 6
            sprite = pygame.Surface((size, size), pygame.SRCALPHA)
            steps = 8
            for k in range(steps, 0, -1):
                rr = int(radius * (1 + 2.0 * k / steps))
                alpha = int(70 * (1 - k / (steps + 1)) ** 2)
                pygame.draw.circle(sprite, (*color, alpha), (size // 2, size // 2), rr)
            if len(self._glow) > 256:
                self._glow.clear()
            self._glow[key] = sprite
        return sprite

    def _draw_com(self, target, cam, system) -> None:
        com = system.center_of_mass()
        sx, sy = cam.world_to_screen(com[0], com[1])
        if -20 < sx < cam.w + 20 and -20 < sy < cam.h + 20:
            s = 7
            pygame.draw.line(target, Colors.HIGHLIGHT, (sx - s, sy), (sx + s, sy), 2)
            pygame.draw.line(target, Colors.HIGHLIGHT, (sx, sy - s), (sx, sy + s), 2)
            pygame.draw.circle(target, Colors.HIGHLIGHT, (int(sx), int(sy)), s + 3, 1)
