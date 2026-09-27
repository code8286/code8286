"""Colours, fonts and resolution-independent UI scaling."""

from __future__ import annotations

import pygame


class Colors:
    BG = (5, 6, 10)
    CANVAS = (6, 7, 12)
    PANEL = (14, 16, 23)
    PANEL_ALT = (24, 27, 37)
    PANEL_EDGE = (44, 48, 62)
    ACCENT = (30, 33, 45)
    ACCENT_HOVER = (48, 52, 68)
    HIGHLIGHT = (238, 240, 246)       # primary accent is white, per the GravBox design
    HIGHLIGHT_HOVER = (255, 255, 255)
    TEXT = (238, 240, 246)
    MUTED = (138, 144, 163)
    DISABLED = (20, 22, 30)
    SUCCESS = (126, 240, 184)
    SUCCESS_DIM = (38, 78, 62)
    WARN = (255, 195, 107)
    DANGER = (255, 122, 138)
    DANGER_DIM = (92, 36, 46)
    GRID = (14, 16, 24)
    GRID_MAJOR = (22, 25, 36)
    AXIS = (34, 38, 54)
    ON_ACCENT = (10, 11, 16)          # text drawn on white buttons


FONT_NAMES = "consolas,menlo,dejavusansmono,liberationmono,couriernew"
BASE_WIDTH = 1500
BASE_HEIGHT = 900


def ui_scale_for(width: int, height: int) -> float:
    """UI scale so widgets stay readable from laptops to 4K monitors."""
    return max(0.8, min(2.4, min(height / BASE_HEIGHT, width / BASE_WIDTH)))


class Theme:
    SIZES = {"tiny": 11, "small": 13, "normal": 14, "large": 17, "title": 19}

    def __init__(self, scale: float = 1.0) -> None:
        self.scale = scale
        self._fonts = {}

    def px(self, value: float) -> int:
        return max(1, int(round(value * self.scale)))

    def font(self, key: str = "normal", bold: bool = False) -> pygame.font.Font:
        size = self.px(self.SIZES.get(key, 14))
        cache_key = (size, bold)
        font = self._fonts.get(cache_key)
        if font is None:
            font = pygame.font.SysFont(FONT_NAMES, size, bold=bold)
            self._fonts[cache_key] = font
        return font
