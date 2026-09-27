"""Persistent orbit trails.

Trails never disappear during a run. Each trail keeps its full history in a
fixed-size buffer: when the buffer fills up, the *older* half is thinned to
every other point while the recent half keeps full resolution. The overall
path is therefore always visible, memory stays bounded, and old segments just
become slightly coarser.

Trails are keyed by body UID and outlive their body, so the path of a body
that merged or was deleted remains on screen until the user clears trails.
"""

from __future__ import annotations

from typing import Dict

import numpy as np


class Trail:
    __slots__ = ("uid", "color", "buf", "count", "alive", "version")

    def __init__(self, uid: int, color, capacity: int) -> None:
        self.uid = uid
        self.color = tuple(color)
        self.buf = np.empty((max(8, capacity), 3), dtype=np.float32)
        self.count = 0
        self.alive = True
        self.version = 0  # bumped whenever existing points are rewritten

    @property
    def points(self) -> np.ndarray:
        return self.buf[: self.count]

    def append(self, point, min_dist2: float) -> bool:
        if self.count:
            d = self.buf[self.count - 1] - point
            if float(d @ d) < min_dist2:
                return False
        if self.count == len(self.buf):
            self._decimate()
        self.buf[self.count] = point
        self.count += 1
        return True

    def _decimate(self) -> None:
        half = self.count // 2
        older = self.buf[:half:2].copy()
        recent = self.buf[half:self.count].copy()
        k = len(older)
        self.buf[:k] = older
        self.buf[k:k + len(recent)] = recent
        self.count = k + len(recent)
        self.version += 1


class TrailStore:
    def __init__(self, capacity: int = 4000, min_step: float = 0.5) -> None:
        self.capacity = capacity
        self.min_step = min_step
        self.trails: Dict[int, Trail] = {}
        self.version = 0  # bumped on clear so renderers do a full redraw

    def record(self, system) -> None:
        min_d2 = self.min_step * self.min_step
        live = set()
        for uid, color, p in zip(system.uids.tolist(), system.colors, system.pos):
            trail = self.trails.get(uid)
            if trail is None:
                trail = Trail(uid, color, self.capacity)
                self.trails[uid] = trail
            trail.alive = True
            trail.append(p, min_d2)
            live.add(uid)
        for uid, trail in self.trails.items():
            if uid not in live:
                trail.alive = False

    def clear(self) -> None:
        self.trails = {}
        self.version += 1

    def total_points(self) -> int:
        return sum(t.count for t in self.trails.values())
