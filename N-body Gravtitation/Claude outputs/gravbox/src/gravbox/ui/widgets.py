"""Panel widgets.

Every widget owns a ``rect`` in *content coordinates*. ``draw`` receives a
vertical offset (for scrolling) and the mouse position in the same content
coordinates (for hover effects). Text, colours and states may be given as
plain values or zero-argument callables, so labels stay live without
rebuilding the layout.
"""

from __future__ import annotations

import math
from typing import Callable, Optional, Sequence

import pygame

from gravbox.ui.theme import Colors


def value_of(v):
    return v() if callable(v) else v


def blit_text(surf, font, text, color, pos, anchor="topleft") -> pygame.Rect:
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    setattr(rect, anchor, (int(pos[0]), int(pos[1])))
    surf.blit(image, rect)
    return rect


def fit_text(font, text: str, max_w: int) -> str:
    text = str(text)
    if font.size(text)[0] <= max_w:
        return text
    while text and font.size(text + "..")[0] > max_w:
        text = text[:-1]
    return text + ".."


class Widget:
    captures = False  # True if the widget keeps receiving motion while dragged

    def __init__(self, rect) -> None:
        self.rect = pygame.Rect(rect)

    def draw(self, surf, theme, dy, mouse) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def handle(self, ev, pos) -> bool:
        return False

    def drag(self, pos) -> None:
        pass

    def hovered(self, mouse) -> bool:
        return mouse is not None and self.rect.collidepoint(mouse)


class Header(Widget):
    def __init__(self, rect, text: str) -> None:
        super().__init__(rect)
        self.text = text.upper()

    def draw(self, surf, theme, dy, mouse) -> None:
        r = self.rect.move(0, dy)
        tr = blit_text(surf, theme.font("tiny"), " ".join(self.text), Colors.MUTED, (r.x, r.centery), "midleft")
        x0 = tr.right + theme.px(8)
        if x0 < r.right:
            pygame.draw.line(surf, Colors.PANEL_EDGE, (x0, r.centery), (r.right, r.centery), 1)


class Label(Widget):
    def __init__(self, rect, lines, color=Colors.MUTED, font: str = "small") -> None:
        super().__init__(rect)
        self.lines = lines if isinstance(lines, (list, tuple)) else [lines]
        self.color = color
        self.font = font

    def draw(self, surf, theme, dy, mouse) -> None:
        r = self.rect.move(0, dy)
        f = theme.font(self.font)
        y = r.y
        color = value_of(self.color)
        for line in self.lines:
            blit_text(surf, f, fit_text(f, value_of(line), r.w), color, (r.x, y))
            y += f.get_linesize()


def wrap_text(font, text: str, max_w: int, max_lines: int = 0):
    """Greedy word wrap; the last allowed line is truncated with '..'."""
    lines, current = [], ""
    for word in str(text).split():
        trial = f"{current} {word}".strip()
        if font.size(trial)[0] <= max_w or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = fit_text(font, lines[-1] + " ...", max_w)
    return lines


class Paragraph(Widget):
    """Word-wrapped text whose content may change at runtime."""

    def __init__(self, rect, text, color=Colors.MUTED, font: str = "small", max_lines: int = 2) -> None:
        super().__init__(rect)
        self.text = text
        self.color = color
        self.font = font
        self.max_lines = max_lines

    def draw(self, surf, theme, dy, mouse) -> None:
        r = self.rect.move(0, dy)
        f = theme.font(self.font)
        y = r.y
        for line in wrap_text(f, value_of(self.text), r.w, self.max_lines):
            blit_text(surf, f, line, value_of(self.color), (r.x, y))
            y += f.get_linesize()


class KeyValue(Widget):
    def __init__(self, rect, name: str, value, color=Colors.TEXT) -> None:
        super().__init__(rect)
        self.name = name
        self.value = value
        self.color = color

    def draw(self, surf, theme, dy, mouse) -> None:
        r = self.rect.move(0, dy)
        f = theme.font("small")
        blit_text(surf, f, self.name, Colors.MUTED, (r.x, r.centery), "midleft")
        text = fit_text(f, value_of(self.value), r.w // 2 + theme.px(30))
        blit_text(surf, f, text, value_of(self.color), (r.right, r.centery), "midright")


class Button(Widget):
    STYLES = {
        "normal": (Colors.ACCENT, Colors.ACCENT_HOVER, Colors.TEXT),
        "primary": (Colors.HIGHLIGHT, Colors.HIGHLIGHT_HOVER, Colors.ON_ACCENT),
        "success": (Colors.SUCCESS_DIM, Colors.SUCCESS, (255, 255, 255)),
        "danger": (Colors.DANGER_DIM, Colors.DANGER, (255, 255, 255)),
    }

    def __init__(self, rect, text, on_click: Callable[[], None], style="normal",
                 active: Optional[Callable[[], bool]] = None,
                 enabled: Optional[Callable[[], bool]] = None, font: str = "small") -> None:
        super().__init__(rect)
        self.text = text
        self.on_click = on_click
        self.style = style
        self.active = active
        self.enabled = enabled
        self.font = font

    def is_enabled(self) -> bool:
        return True if self.enabled is None else bool(self.enabled())

    def is_active(self) -> bool:
        return False if self.active is None else bool(self.active())

    def draw(self, surf, theme, dy, mouse) -> None:
        r = self.rect.move(0, dy)
        enabled, active = self.is_enabled(), self.is_active()
        base, hover, fg = self.STYLES.get(value_of(self.style), self.STYLES["normal"])
        if active:
            base, hover, fg = self.STYLES["primary"]
        color = hover if enabled and self.hovered(mouse) else base
        if not enabled:
            color, fg = Colors.DISABLED, Colors.MUTED
        radius = r.h // 2
        pygame.draw.rect(surf, color, r, border_radius=radius)
        pygame.draw.rect(surf, Colors.HIGHLIGHT if active else Colors.PANEL_EDGE, r, 1, border_radius=radius)
        f = theme.font(self.font)
        blit_text(surf, f, fit_text(f, value_of(self.text), r.w - theme.px(8)), fg, r.center, "center")

    def handle(self, ev, pos) -> bool:
        if (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
                and self.rect.collidepoint(pos) and self.is_enabled()):
            self.on_click()
            return True
        return False


class Toggle(Widget):
    def __init__(self, rect, label, get: Callable[[], bool], set_: Callable[[bool], None]) -> None:
        super().__init__(rect)
        self.label = label
        self.get = get
        self.set = set_

    def draw(self, surf, theme, dy, mouse) -> None:
        r = self.rect.move(0, dy)
        if self.hovered(mouse):
            pygame.draw.rect(surf, Colors.PANEL_ALT, r.inflate(theme.px(6), 0), border_radius=theme.px(4))
        on = bool(self.get())
        sw, sh = theme.px(34), theme.px(18)
        track = pygame.Rect(r.right - sw, r.centery - sh // 2, sw, sh)
        f = theme.font("small")
        blit_text(surf, f, fit_text(f, value_of(self.label), r.w - sw - theme.px(8)), Colors.TEXT,
                  (r.x, r.centery), "midleft")
        pygame.draw.rect(surf, Colors.HIGHLIGHT if on else Colors.ACCENT, track, border_radius=sh // 2)
        knob_x = track.right - sh // 2 if on else track.x + sh // 2
        knob = Colors.ON_ACCENT if on else (200, 204, 216)
        pygame.draw.circle(surf, knob, (knob_x, track.centery), sh // 2 - theme.px(3))

    def handle(self, ev, pos) -> bool:
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(pos):
            self.set(not bool(self.get()))
            return True
        return False


class Slider(Widget):
    captures = True

    def __init__(self, rect, label, get, set_, lo: float, hi: float, fmt: str = "{:.3f}",
                 log: bool = False, integer: bool = False,
                 on_change: Optional[Callable[[float], None]] = None) -> None:
        super().__init__(rect)
        self.label = label
        self.get = get
        self.set = set_
        self.lo, self.hi = float(lo), float(hi)
        self.fmt = fmt
        self.log = log and lo > 0
        self.integer = integer
        self.on_change = on_change
        self._track = None

    def _fraction(self) -> float:
        v = float(self.get())
        if self.log:
            v = max(v, self.lo)
            t = (math.log(v) - math.log(self.lo)) / (math.log(self.hi) - math.log(self.lo))
        else:
            t = (v - self.lo) / (self.hi - self.lo)
        return max(0.0, min(1.0, t))

    def _value_at(self, t: float) -> float:
        if self.log:
            v = math.exp(math.log(self.lo) + t * (math.log(self.hi) - math.log(self.lo)))
        else:
            v = self.lo + t * (self.hi - self.lo)
        return int(round(v)) if self.integer else v

    def draw(self, surf, theme, dy, mouse) -> None:
        f = theme.font("small")
        th = theme.px(6)
        self._track = pygame.Rect(self.rect.x + theme.px(7), self.rect.bottom - theme.px(9) - th // 2,
                                  self.rect.w - theme.px(14), th)
        r = self.rect.move(0, dy)
        track = self._track.move(0, dy)
        blit_text(surf, f, value_of(self.label), Colors.TEXT, (r.x, r.y))
        blit_text(surf, f, self.fmt.format(self.get()), Colors.HIGHLIGHT, (r.right, r.y), "topright")
        pygame.draw.rect(surf, Colors.ACCENT, track, border_radius=th // 2)
        t = self._fraction()
        filled = track.copy()
        filled.w = max(th, int(track.w * t))
        pygame.draw.rect(surf, Colors.HIGHLIGHT if self.hovered(mouse) else (170, 176, 196), filled,
                         border_radius=th // 2)
        pygame.draw.circle(surf, (245, 245, 250), (track.x + int(track.w * t), track.centery), theme.px(7))

    def _set_from_x(self, x: float) -> None:
        track = self._track or self.rect
        t = max(0.0, min(1.0, (x - track.x) / max(1, track.w)))
        value = self._value_at(t)
        if value != self.get():
            self.set(value)
            if self.on_change:
                self.on_change(value)

    def handle(self, ev, pos) -> bool:
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(pos):
            self._set_from_x(pos[0])
            return True
        return False

    def drag(self, pos) -> None:
        self._set_from_x(pos[0])


class Segmented(Widget):
    def __init__(self, rect, options: Sequence, get, set_) -> None:
        super().__init__(rect)
        self.options = list(options)  # [(value, label), ...]
        self.get = get
        self.set = set_

    def _segments(self, r):
        n = len(self.options)
        w = r.w / n
        return [pygame.Rect(int(r.x + i * w), r.y, int(r.x + (i + 1) * w) - int(r.x + i * w), r.h) for i in range(n)]

    def draw(self, surf, theme, dy, mouse) -> None:
        r = self.rect.move(0, dy)
        radius = r.h // 2
        pygame.draw.rect(surf, Colors.PANEL_ALT, r, border_radius=radius)
        current = self.get()
        f = theme.font("small")
        hover_segs = self._segments(self.rect)
        for (value, label), seg, hseg in zip(self.options, self._segments(r), hover_segs):
            if value == current:
                pygame.draw.rect(surf, Colors.ACCENT_HOVER, seg, border_radius=seg.h // 2)
            elif mouse is not None and hseg.collidepoint(mouse):
                pygame.draw.rect(surf, Colors.ACCENT_HOVER, seg, border_radius=radius)
            blit_text(surf, f, fit_text(f, label, seg.w - theme.px(4)), Colors.TEXT, seg.center, "center")
        pygame.draw.rect(surf, Colors.PANEL_EDGE, r, 1, border_radius=radius)

    def handle(self, ev, pos) -> bool:
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(pos):
            for (value, _), seg in zip(self.options, self._segments(self.rect)):
                if seg.collidepoint(pos):
                    self.set(value)
                    return True
        return False


class Graph(Widget):
    def __init__(self, rect, title: str, data: Callable[[], Sequence[float]],
                 color=Colors.HIGHLIGHT, fmt: str = "{:+.2e}") -> None:
        super().__init__(rect)
        self.title = title
        self.data = data
        self.color = color
        self.fmt = fmt

    def draw(self, surf, theme, dy, mouse) -> None:
        r = self.rect.move(0, dy)
        f = theme.font("small")
        values = list(self.data())
        blit_text(surf, f, self.title, Colors.MUTED, (r.x, r.y))
        if values:
            blit_text(surf, f, self.fmt.format(values[-1]), self.color, (r.right, r.y), "topright")
        plot = pygame.Rect(r.x, r.y + f.get_linesize() + theme.px(4), r.w, r.h - f.get_linesize() - theme.px(4))
        pygame.draw.rect(surf, Colors.PANEL_ALT, plot, border_radius=theme.px(4))
        if len(values) >= 2:
            lo, hi = min(values), max(values)
            if hi - lo < 1e-300:
                lo, hi = lo - 1.0, hi + 1.0
            pad = (hi - lo) * 0.08
            lo, hi = lo - pad, hi + pad
            inner = plot.inflate(-theme.px(8), -theme.px(8))
            if lo < 0.0 < hi:
                zy = inner.bottom - (0.0 - lo) / (hi - lo) * inner.h
                pygame.draw.line(surf, Colors.PANEL_EDGE, (inner.x, zy), (inner.right, zy), 1)
            n = len(values)
            pts = [(inner.x + i / (n - 1) * inner.w, inner.bottom - (v - lo) / (hi - lo) * inner.h)
                   for i, v in enumerate(values)]
            pygame.draw.lines(surf, self.color, False, pts, max(1, theme.px(2)))
        else:
            blit_text(surf, f, "waiting for data", Colors.MUTED, plot.center, "center")
