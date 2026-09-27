"""pygame image helpers that work across pygame 2.x versions."""

from __future__ import annotations

import pygame


def surface_to_bytes(surface: pygame.Surface, fmt: str = "RGBA", flipped: bool = False) -> bytes:
    fn = getattr(pygame.image, "tobytes", None) or pygame.image.tostring
    return fn(surface, fmt, flipped)


def bytes_to_surface(data: bytes, size, fmt: str = "RGBA") -> pygame.Surface:
    fn = getattr(pygame.image, "frombytes", None) or pygame.image.fromstring
    return fn(data, size, fmt)
