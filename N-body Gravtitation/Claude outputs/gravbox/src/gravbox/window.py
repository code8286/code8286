"""Window creation, sizing and fullscreen handling.

* The initial window is the largest 16:9 rectangle that fits in ~88% of the
  desktop, so it never opens off-screen or with a distorted aspect ratio.
* The window is resizable; the 2D and 3D views adapt with a uniform scale.
* Fullscreen uses the native desktop resolution (no display mode change).
* Switching between software (2D) and OpenGL (3D) rendering re-creates the
  display surface with the right flags.
"""

from __future__ import annotations

import pygame

from gravbox.config import DEFAULT_ASPECT, MIN_WINDOW_SIZE, WindowConfig


class Window:
    def __init__(self, cfg: WindowConfig) -> None:
        self.gl = False
        self.fullscreen = bool(cfg.fullscreen)
        dw, dh = self.desktop_size()
        min_w, min_h = MIN_WINDOW_SIZE
        if min_w <= cfg.width <= dw and min_h <= cfg.height <= dh:
            self.windowed_size = (cfg.width, cfg.height)
        else:
            self.windowed_size = self.default_size()

    @staticmethod
    def desktop_size():
        try:
            sizes = pygame.display.get_desktop_sizes()
            if sizes:
                return tuple(sizes[0])
        except (AttributeError, pygame.error):
            pass
        info = pygame.display.Info()
        if info.current_w > 0 and info.current_h > 0:
            return (info.current_w, info.current_h)
        return (1600, 900)

    def default_size(self):
        dw, dh = self.desktop_size()
        w = min(dw * 0.88, dh * 0.85 * DEFAULT_ASPECT)
        h = w / DEFAULT_ASPECT
        min_w, min_h = MIN_WINDOW_SIZE
        return (max(min(min_w, dw), min(int(w), dw)), max(min(min_h, dh), min(int(h), dh)))

    def open(self, gl=None) -> pygame.Surface:
        if gl is not None:
            self.gl = bool(gl)
        flags = (pygame.OPENGL | pygame.DOUBLEBUF) if self.gl else 0
        if self.fullscreen:
            size = self.desktop_size()
            flags |= pygame.FULLSCREEN
        else:
            size = self.windowed_size
            flags |= pygame.RESIZABLE
        try:
            return pygame.display.set_mode(size, flags)
        except pygame.error:
            if self.fullscreen:  # fall back to a window rather than crash
                self.fullscreen = False
                return self.open()
            raise

    def size(self):
        surface = pygame.display.get_surface()
        return surface.get_size() if surface is not None else self.windowed_size

    def remember_size(self) -> None:
        if not self.fullscreen:
            w, h = self.size()
            if w > 0 and h > 0:
                self.windowed_size = (w, h)

    def toggle_fullscreen(self) -> pygame.Surface:
        if not self.fullscreen:
            self.remember_size()
        self.fullscreen = not self.fullscreen
        return self.open()

    def export(self, cfg: WindowConfig) -> None:
        cfg.width, cfg.height = self.windowed_size
        cfg.fullscreen = self.fullscreen
