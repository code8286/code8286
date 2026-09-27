"""Vertical flow layout that places widgets and computes their rects."""

from __future__ import annotations

from typing import Callable, List, Sequence

import pygame

from gravbox.ui.theme import Colors
from gravbox.ui.widgets import (
    Button,
    Graph,
    Header,
    KeyValue,
    Label,
    Paragraph,
    Segmented,
    Slider,
    Toggle,
    Widget,
    wrap_text,
)


class LayoutBuilder:
    def __init__(self, x: int, y: int, width: int, theme) -> None:
        self.x = x
        self.y = y
        self.w = width
        self.theme = theme
        self.gap = theme.px(7)
        self.row_h = theme.px(30)
        self.widgets: List[Widget] = []

    def _take(self, height: int) -> pygame.Rect:
        rect = pygame.Rect(self.x, self.y, self.w, height)
        self.y += height + self.gap
        return rect

    def add(self, widget: Widget) -> Widget:
        self.widgets.append(widget)
        return widget

    # ---------------------------------------------------------------- items
    def header(self, text: str) -> None:
        if self.widgets:
            self.y += self.theme.px(6)
        self.add(Header(self._take(self.theme.px(20)), text))

    def button(self, text, on_click, style="normal", active=None, enabled=None) -> None:
        self.add(Button(self._take(self.row_h), text, on_click, style, active, enabled))

    def row(self, items: Sequence[dict]) -> None:
        """A row of equally sized buttons. Each item: dict(text, on_click, style?, active?, enabled?)."""
        self.grid(items, cols=len(items))

    def grid(self, items: Sequence[dict], cols: int = 2) -> None:
        gap = self.theme.px(6)
        cell_w = (self.w - gap * (cols - 1)) / cols
        for index, item in enumerate(items):
            col = index % cols
            if col == 0 and index:
                self.y += self.row_h + gap
            x0 = int(self.x + col * (cell_w + gap))
            x1 = int(self.x + col * (cell_w + gap) + cell_w)
            rect = pygame.Rect(x0, self.y, x1 - x0, self.row_h)
            self.add(Button(rect, item["text"], item["on_click"], item.get("style", "normal"),
                            item.get("active"), item.get("enabled")))
        if items:
            self.y += self.row_h + self.gap

    def toggle(self, label, get, set_) -> None:
        self.add(Toggle(self._take(self.theme.px(26)), label, get, set_))

    def slider(self, label, get, set_, lo, hi, fmt="{:.3f}", log=False, integer=False,
               on_change: Callable = None) -> None:
        height = self.theme.font("small").get_linesize() + self.theme.px(20)
        self.add(Slider(self._take(height), label, get, set_, lo, hi, fmt, log, integer, on_change))

    def segmented(self, options, get, set_) -> None:
        self.add(Segmented(self._take(self.theme.px(28)), options, get, set_))

    def label(self, lines, color=Colors.MUTED, font="small") -> None:
        lines = lines if isinstance(lines, (list, tuple)) else [lines]
        height = self.theme.font(font).get_linesize() * len(lines)
        self.add(Label(self._take(height), list(lines), color, font))

    def paragraph(self, text, color=Colors.MUTED, font="small", max_lines: int = 0) -> None:
        """Word-wrapped text. Callables are re-wrapped every frame within ``max_lines``."""
        f = self.theme.font(font)
        if callable(text):
            lines = max(1, max_lines or 2)
            self.add(Paragraph(self._take(f.get_linesize() * lines), text, color, font, lines))
        else:
            self.label(wrap_text(f, text, self.w, max_lines) or [""], color, font)

    def kv(self, name: str, value, color=Colors.TEXT) -> None:
        self.add(KeyValue(self._take(self.theme.px(20)), name, value, color))

    def graph(self, title, data, color=Colors.HIGHLIGHT, height=90, fmt="{:+.2e}") -> None:
        self.add(Graph(self._take(self.theme.px(height)), title, data, color, fmt))

    def spacer(self, height: int) -> None:
        self.y += self.theme.px(height)
