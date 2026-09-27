"""Canvas overlays: stats box, toast notifications and the hint bar."""

from __future__ import annotations

from typing import Sequence, Tuple

import pygame

from gravbox.ui.theme import Colors
from gravbox.ui.widgets import blit_text


def text_box(lines: Sequence[Tuple[str, tuple]], theme, alpha: int = 200, font: str = "small") -> pygame.Surface:
    f = theme.font(font)
    pad = theme.px(8)
    lh = f.get_linesize()
    width = max((f.size(text)[0] for text, _ in lines), default=0) + 2 * pad
    height = lh * len(lines) + 2 * pad
    surf = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)
    radius = min(theme.px(12), height // 2)
    pygame.draw.rect(surf, (16, 18, 26, alpha), surf.get_rect(), border_radius=radius)
    pygame.draw.rect(surf, (*Colors.PANEL_EDGE, 255), surf.get_rect(), 1, border_radius=radius)
    y = pad
    for text, color in lines:
        blit_text(surf, f, text, color, (pad, y))
        y += lh
    return surf


def hint_bar(text: str, theme) -> pygame.Surface:
    return text_box([(text, Colors.MUTED)], theme, alpha=150, font="tiny")
