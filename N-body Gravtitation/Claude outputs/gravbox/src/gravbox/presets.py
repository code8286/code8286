"""Built-in initial conditions.

Every preset is expressed in world units for ``G`` supplied by the caller, so
circular-orbit speeds stay correct if the user has changed gravity. Presets
return plain dicts (``pos``, ``vel``, ``mass``, ``color``) that
:meth:`gravbox.physics.NBodySystem.load` understands.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Dict, List

PALETTE = [
    (255, 107, 107), (78, 205, 196), (255, 209, 102), (149, 125, 255),
    (6, 214, 160), (239, 71, 111), (17, 138, 178), (255, 159, 67),
    (162, 210, 255), (255, 175, 204), (202, 255, 191), (189, 178, 255),
]
STAR_COLOR = (255, 214, 102)


def palette_color(i: int):
    return PALETTE[i % len(PALETTE)]


def _body(pos, vel, mass, color) -> dict:
    p = list(pos) + [0.0] * (3 - len(pos))
    v = list(vel) + [0.0] * (3 - len(vel))
    return {"pos": [float(c) for c in p], "vel": [float(c) for c in v],
            "mass": float(mass), "color": tuple(int(c) for c in color)}


def _circular_speed(G: float, mass: float, r: float) -> float:
    return math.sqrt(G * mass / r) if r > 0 else 0.0


# ---------------------------------------------------------------- builders
def figure_eight(G: float, rng: random.Random) -> List[dict]:
    """Chenciner-Montgomery figure-eight choreography of three equal masses."""
    L, M = 200.0, 30000.0
    vs = math.sqrt(G * M / L)
    x1 = (0.97000436, -0.24308753)
    v3 = (-0.93240737, -0.86473146)
    half = (-v3[0] / 2, -v3[1] / 2)
    return [
        _body((x1[0] * L, x1[1] * L), (half[0] * vs, half[1] * vs), M, PALETTE[0]),
        _body((-x1[0] * L, -x1[1] * L), (half[0] * vs, half[1] * vs), M, PALETTE[1]),
        _body((0.0, 0.0), (v3[0] * vs, v3[1] * vs), M, PALETTE[2]),
    ]


def four_square(G: float, rng: random.Random) -> List[dict]:
    """Four equal masses on a square, spun slightly below the circular speed.

    The configuration is unstable: it looks orderly for a few revolutions,
    then decays into close encounters and ejections.
    """
    m, a = 8000.0, 150.0
    R, s = a * math.sqrt(2.0), 2.0 * a
    accel = G * m * (math.sqrt(2.0) / s ** 2 + 1.0 / (4.0 * R ** 2))
    v = 0.8 * math.sqrt(R * accel)
    out = []
    for i, (x, y) in enumerate([(a, a), (-a, a), (-a, -a), (a, -a)]):
        out.append(_body((x, y), (-y / R * v, x / R * v), m, PALETTE[i]))
    return out


def binary(G: float, rng: random.Random) -> List[dict]:
    m, d = 12000.0, 220.0
    v = math.sqrt(G * m / (2.0 * d))
    return [
        _body((d / 2, 0.0), (0.0, v), m, PALETTE[0]),
        _body((-d / 2, 0.0), (0.0, -v), m, PALETTE[1]),
    ]


def lagrange_triangle(G: float, rng: random.Random) -> List[dict]:
    """Lagrange's equilateral solution. Unstable for equal masses."""
    m, side = 10000.0, 240.0
    R = side / math.sqrt(3.0)
    v = math.sqrt(G * m / side)
    out = []
    for i in range(3):
        ang = math.pi / 2 + i * 2 * math.pi / 3
        x, y = R * math.cos(ang), R * math.sin(ang)
        out.append(_body((x, y), (-math.sin(ang) * v, math.cos(ang) * v), m, PALETTE[i + 3]))
    return out


def pythagorean(G: float, rng: random.Random) -> List[dict]:
    """Burrau's problem: masses 3, 4, 5 at rest on a 3-4-5 triangle."""
    L, M = 50.0, 1500.0
    spec = [(3, (1.0, 3.0)), (4, (-2.0, -1.0)), (5, (1.0, -1.0))]
    return [_body((x * L, y * L), (0.0, 0.0), m * M, PALETTE[i + 5]) for i, (m, (x, y)) in enumerate(spec)]


def solar_system(G: float, rng: random.Random) -> List[dict]:
    M = 25000.0
    bodies = [_body((0.0, 0.0), (0.0, 0.0), M, STAR_COLOR)]
    radii = [70, 105, 145, 190, 240, 300, 370]
    masses = [2, 4, 5, 3, 40, 25, 10]
    for i, (r, m) in enumerate(zip(radii, masses)):
        ang = rng.uniform(0, 2 * math.pi)
        v = _circular_speed(G, M, r)
        bodies.append(_body((r * math.cos(ang), r * math.sin(ang)),
                            (-math.sin(ang) * v, math.cos(ang) * v), m, palette_color(i + 1)))
    return bodies


def circumbinary(G: float, rng: random.Random) -> List[dict]:
    m, d = 10000.0, 70.0
    v = math.sqrt(G * m / (2.0 * d))
    bodies = [
        _body((d / 2, 0.0), (0.0, v), m, STAR_COLOR),
        _body((-d / 2, 0.0), (0.0, -v), m, PALETTE[7]),
    ]
    for i, r in enumerate((200.0, 260.0, 330.0)):
        ang = rng.uniform(0, 2 * math.pi)
        vp = _circular_speed(G, 2 * m, r)
        bodies.append(_body((r * math.cos(ang), r * math.sin(ang)),
                            (-math.sin(ang) * vp, math.cos(ang) * vp), 3.0, palette_color(i + 1)))
    return bodies


def disk_cluster(G: float, rng: random.Random) -> List[dict]:
    """A slowly rotating disk of 100 stars that collapses and relaxes."""
    n, R = 100, 300.0
    masses = [rng.uniform(20, 120) for _ in range(n)]
    total = sum(masses)
    bodies = []
    for i, m in enumerate(masses):
        r = R * math.sqrt(rng.random())
        ang = rng.uniform(0, 2 * math.pi)
        m_enc = total * (r / R) ** 2
        v = 0.5 * _circular_speed(G, m_enc, max(r, 1.0))
        vx = -math.sin(ang) * v + rng.gauss(0, 0.3)
        vy = math.cos(ang) * v + rng.gauss(0, 0.3)
        bodies.append(_body((r * math.cos(ang), r * math.sin(ang)), (vx, vy), m, palette_color(i)))
    return bodies


def galaxy_collision(G: float, rng: random.Random) -> List[dict]:
    """Two rotating disks on a bound, off-centre collision course."""
    core = 12000.0
    bodies: List[dict] = []
    for cx, cy, vx, spin, color in ((-280.0, -70.0, 2.8, 1, PALETTE[1]), (280.0, 70.0, -2.8, -1, PALETTE[5])):
        bodies.append(_body((cx, cy), (vx, 0.0), core, STAR_COLOR))
        for _ in range(50):
            r = rng.uniform(40, 160)
            ang = rng.uniform(0, 2 * math.pi)
            v = _circular_speed(G, core, r) * spin
            bodies.append(_body((cx + r * math.cos(ang), cy + r * math.sin(ang)),
                                (vx - math.sin(ang) * v, math.cos(ang) * v), rng.uniform(1, 4), color))
    return bodies


def cluster_3d(G: float, rng: random.Random) -> List[dict]:
    """A roughly virialised spherical cluster (natively 3D)."""
    n, R = 90, 250.0
    masses = [rng.uniform(20, 100) for _ in range(n)]
    sigma = 0.4 * math.sqrt(G * sum(masses) / R) / math.sqrt(3.0)
    bodies = []
    for i, m in enumerate(masses):
        while True:
            x, y, z = (rng.uniform(-1, 1) for _ in range(3))
            if x * x + y * y + z * z <= 1.0:
                break
        vel = (rng.gauss(0, sigma), rng.gauss(0, sigma), rng.gauss(0, sigma))
        bodies.append(_body((x * R, y * R, z * R), vel, m, palette_color(i)))
    return bodies


# ---------------------------------------------------------------- registry
@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    description: str
    build: Callable[[float, random.Random], List[dict]]


PRESETS: List[Preset] = [
    Preset("figure8", "Figure-8", "Stable three-body choreography (Chenciner-Montgomery).", figure_eight),
    Preset("square", "4-Body Square", "Four equal masses on a square; orderly, then chaotic.", four_square),
    Preset("binary", "Binary Star", "Two equal stars on a circular orbit.", binary),
    Preset("lagrange", "Lagrange Triangle", "Equilateral 3-body solution; slowly unstable.", lagrange_triangle),
    Preset("pythagorean", "Pythagorean", "Burrau's 3-4-5 problem: chaos and ejection from rest.", pythagorean),
    Preset("solar", "Solar System", "A star with seven planets on circular orbits.", solar_system),
    Preset("circumbinary", "Circumbinary", "Planets orbiting a close binary star.", circumbinary),
    Preset("cluster", "Disk Cluster", "100 stars in a rotating disk collapsing under gravity.", disk_cluster),
    Preset("galaxies", "Galaxy Collision", "Two rotating disks on a bound collision course.", galaxy_collision),
    Preset("cluster3d", "3D Cluster", "Spherical star cluster with 3D velocities.", cluster_3d),
]
PRESETS_BY_KEY: Dict[str, Preset] = {p.key: p for p in PRESETS}
DEFAULT_PRESET = "figure8"


def build_preset(key: str, G: float = 1.0, seed=None) -> List[dict]:
    if key not in PRESETS_BY_KEY:
        raise KeyError(f"unknown preset {key!r}; choose from {', '.join(PRESETS_BY_KEY)}")
    return PRESETS_BY_KEY[key].build(G, random.Random(seed))
