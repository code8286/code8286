"""Vectorised N-body gravity engine.

All state lives in numpy arrays (positions ``(N, 3)``, velocities ``(N, 3)``,
masses ``(N,)``) so a full O(N^2) force evaluation is a handful of matrix
operations instead of a Python double loop.

The engine is always three-dimensional. A "2D" simulation is simply one where
every body has ``z == 0`` and ``vz == 0``; gravity then keeps it in the plane.

Forces use Plummer softening, ``F = G m1 m2 r / (r^2 + eps^2)^(3/2)``, and the
matching softened potential, so the reported total energy is the quantity the
integrators actually conserve.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

import numpy as np

RADIUS_SCALE = 0.5  # visual/collision radius = RADIUS_SCALE * cbrt(mass)
INTEGRATORS = ("euler", "leapfrog", "rk4")

Color = Tuple[int, int, int]


def body_radius(mass) -> np.ndarray:
    return RADIUS_SCALE * np.cbrt(np.asarray(mass, dtype=float))


def pairwise_r2(pos: np.ndarray, eps2: float = 0.0) -> np.ndarray:
    """Squared pairwise distances (plus ``eps2``) as an ``(N, N)`` matrix."""
    sq = np.einsum("ij,ij->i", pos, pos)
    r2 = sq[:, None] + sq[None, :] - 2.0 * (pos @ pos.T)
    np.maximum(r2, 0.0, out=r2)
    if eps2:
        r2 += eps2
    return r2


def accelerations(pos: np.ndarray, mass: np.ndarray, G: float, eps: float) -> np.ndarray:
    """Gravitational acceleration on every body (softened, O(N^2))."""
    n = pos.shape[0]
    if n < 2:
        return np.zeros_like(pos)
    r2 = pairwise_r2(pos, eps * eps)
    with np.errstate(divide="ignore", invalid="ignore"):
        inv_r3 = r2 ** -1.5
    np.fill_diagonal(inv_r3, 0.0)
    inv_r3[~np.isfinite(inv_r3)] = 0.0
    w = inv_r3 * mass[None, :]
    # a_i = G * sum_j m_j (p_j - p_i) / r_ij^3
    return G * (w @ pos - pos * w.sum(axis=1)[:, None])


def potential_energy(pos: np.ndarray, mass: np.ndarray, G: float, eps: float) -> float:
    n = pos.shape[0]
    if n < 2:
        return 0.0
    r2 = pairwise_r2(pos, eps * eps)
    with np.errstate(divide="ignore", invalid="ignore"):
        inv_r = 1.0 / np.sqrt(r2)
    np.fill_diagonal(inv_r, 0.0)
    inv_r[~np.isfinite(inv_r)] = 0.0
    return float(-0.5 * G * (mass @ inv_r @ mass))


def _vec3(value) -> np.ndarray:
    out = np.zeros(3)
    src = np.asarray(value, dtype=float).reshape(-1)[:3]
    out[: src.size] = src
    return out


class NBodySystem:
    """A mutable set of point masses plus the integrators that advance them."""

    def __init__(self) -> None:
        self.pos = np.zeros((0, 3))
        self.vel = np.zeros((0, 3))
        self.mass = np.zeros(0)
        self.uids = np.zeros(0, dtype=np.int64)
        self.colors: List[Color] = []
        self.time = 0.0
        self._next_uid = 0
        self._acc = None
        self._acc_key = None

    # ------------------------------------------------------------------ state
    @property
    def n(self) -> int:
        return int(self.mass.shape[0])

    def invalidate(self) -> None:
        """Drop cached accelerations after any external mutation."""
        self._acc = None

    def add(self, pos, vel, mass: float, color: Sequence[int] = (255, 255, 255)) -> int:
        mass = float(mass)
        if not np.isfinite(mass) or mass <= 0:
            raise ValueError(f"mass must be positive and finite, got {mass!r}")
        p, v = _vec3(pos), _vec3(vel)
        if not (np.isfinite(p).all() and np.isfinite(v).all()):
            raise ValueError("position and velocity must be finite")
        self.pos = np.vstack([self.pos, p[None, :]])
        self.vel = np.vstack([self.vel, v[None, :]])
        self.mass = np.append(self.mass, mass)
        uid = self._next_uid
        self._next_uid += 1
        self.uids = np.append(self.uids, uid)
        self.colors.append(tuple(int(c) for c in color[:3]))
        self.invalidate()
        return uid

    def load(self, bodies: Iterable[dict], time: float = 0.0) -> None:
        self.clear()
        for b in bodies:
            self.add(b["pos"], b["vel"], b["mass"], b.get("color", (255, 255, 255)))
        self.time = float(time)

    def to_bodies(self) -> List[dict]:
        return [
            {
                "pos": self.pos[i].tolist(),
                "vel": self.vel[i].tolist(),
                "mass": float(self.mass[i]),
                "color": list(self.colors[i]),
            }
            for i in range(self.n)
        ]

    def clear(self) -> None:
        """Remove every body. UIDs keep counting so old trails stay distinct."""
        self._keep(np.zeros(self.n, dtype=bool))
        self.time = 0.0

    def _keep(self, mask: np.ndarray) -> None:
        self.pos = self.pos[mask]
        self.vel = self.vel[mask]
        self.mass = self.mass[mask]
        self.uids = self.uids[mask]
        self.colors = [c for c, keep in zip(self.colors, mask) if keep]
        self.invalidate()

    def remove_indices(self, indices: Iterable[int]) -> None:
        mask = np.ones(self.n, dtype=bool)
        mask[list(indices)] = False
        self._keep(mask)

    def remove_last(self) -> bool:
        if self.n == 0:
            return False
        self.remove_indices([self.n - 1])
        return True

    def remove_non_finite(self) -> int:
        """Drop bodies whose state became NaN/inf. Returns how many."""
        ok = np.isfinite(self.pos).all(axis=1) & np.isfinite(self.vel).all(axis=1)
        bad = int((~ok).sum())
        if bad:
            self._keep(ok)
        return bad

    def radii(self) -> np.ndarray:
        return body_radius(self.mass)

    # ------------------------------------------------------------ diagnostics
    def total_mass(self) -> float:
        return float(self.mass.sum())

    def center_of_mass(self) -> np.ndarray:
        m = self.total_mass()
        if m <= 0:
            return np.zeros(3)
        return (self.mass[:, None] * self.pos).sum(axis=0) / m

    def com_velocity(self) -> np.ndarray:
        m = self.total_mass()
        if m <= 0:
            return np.zeros(3)
        return (self.mass[:, None] * self.vel).sum(axis=0) / m

    def to_com_frame(self) -> None:
        """Shift into the centre-of-mass frame (zero net position and momentum)."""
        if self.n == 0:
            return
        self.pos -= self.center_of_mass()
        self.vel -= self.com_velocity()
        self.invalidate()

    def kinetic_energy(self) -> float:
        return float(0.5 * (self.mass * (self.vel ** 2).sum(axis=1)).sum())

    def potential_energy(self, G: float, eps: float) -> float:
        return potential_energy(self.pos, self.mass, G, eps)

    def momentum(self) -> np.ndarray:
        return (self.mass[:, None] * self.vel).sum(axis=0)

    def angular_momentum(self) -> np.ndarray:
        if self.n == 0:
            return np.zeros(3)
        return (self.mass[:, None] * np.cross(self.pos, self.vel)).sum(axis=0)

    def extent(self) -> float:
        """Radius of a sphere around the CoM that contains every body."""
        if self.n == 0:
            return 100.0
        r = np.linalg.norm(self.pos - self.center_of_mass(), axis=1) + self.radii()
        return float(max(r.max(), 10.0))

    def bounds_xy(self) -> Tuple[float, float, float, float]:
        if self.n == 0:
            return (-100.0, 100.0, -100.0, 100.0)
        r = self.radii()
        x, y = self.pos[:, 0], self.pos[:, 1]
        return (float((x - r).min()), float((x + r).max()), float((y - r).min()), float((y + r).max()))

    # ------------------------------------------------------------- 2D <-> 3D
    def is_flat(self, tol: float = 1e-9) -> bool:
        return bool(np.all(np.abs(self.pos[:, 2]) < tol) and np.all(np.abs(self.vel[:, 2]) < tol))

    def perturb_z(self, rng: np.random.Generator, fraction: float = 0.05) -> None:
        """Lift a planar system into 3D with small random z offsets/velocities."""
        if self.n == 0:
            return
        scale = self.extent() * fraction
        speed = float(np.sqrt((self.vel ** 2).sum(axis=1).mean())) if self.n else 0.0
        self.pos[:, 2] += rng.normal(0.0, scale, self.n)
        self.vel[:, 2] += rng.normal(0.0, max(speed, 1e-3) * fraction, self.n)
        self.invalidate()

    def flatten(self) -> None:
        self.pos[:, 2] = 0.0
        self.vel[:, 2] = 0.0
        self.invalidate()

    # ------------------------------------------------------------ integration
    def step(self, dt: float, G: float, eps: float, integrator: str = "leapfrog",
             damping: float = 1.0) -> None:
        if self.n == 0:
            self.time += dt
            return
        if integrator == "euler":
            a = accelerations(self.pos, self.mass, G, eps)
            self.pos += self.vel * dt
            self.vel += a * dt
            self._acc = None
        elif integrator == "rk4":
            self._step_rk4(dt, G, eps)
            self._acc = None
        else:  # leapfrog (kick-drift-kick), symplectic
            key = (G, eps)
            if self._acc is None or self._acc_key != key or self._acc.shape != self.pos.shape:
                self._acc = accelerations(self.pos, self.mass, G, eps)
                self._acc_key = key
            self.vel += 0.5 * dt * self._acc
            self.pos += dt * self.vel
            self._acc = accelerations(self.pos, self.mass, G, eps)
            self.vel += 0.5 * dt * self._acc
        if damping != 1.0:
            self.vel *= damping
        self.time += dt

    def _step_rk4(self, dt: float, G: float, eps: float) -> None:
        m = self.mass
        x0, v0 = self.pos, self.vel
        a1 = accelerations(x0, m, G, eps)
        x2, v2 = x0 + 0.5 * dt * v0, v0 + 0.5 * dt * a1
        a2 = accelerations(x2, m, G, eps)
        x3, v3 = x0 + 0.5 * dt * v2, v0 + 0.5 * dt * a2
        a3 = accelerations(x3, m, G, eps)
        x4, v4 = x0 + dt * v3, v0 + dt * a3
        a4 = accelerations(x4, m, G, eps)
        self.pos = x0 + (dt / 6.0) * (v0 + 2 * v2 + 2 * v3 + v4)
        self.vel = v0 + (dt / 6.0) * (a1 + 2 * a2 + 2 * a3 + a4)

    # ------------------------------------------------------------- collisions
    def merge_collisions(self) -> List[Tuple[int, int]]:
        """Perfectly inelastic merging of overlapping bodies.

        Conserves mass and linear momentum. Returns ``(survivor_uid, absorbed_uid)``
        pairs so callers can react (e.g. keep the absorbed body's trail).
        """
        if self.n < 2:
            return []
        r = self.radii()
        d2 = pairwise_r2(self.pos)
        hit = np.triu(d2 < (r[:, None] + r[None, :]) ** 2, k=1)
        if not hit.any():
            return []
        alive = np.ones(self.n, dtype=bool)
        merged: List[Tuple[int, int]] = []
        for i, j in np.argwhere(hit):
            if not (alive[i] and alive[j]):
                continue
            if self.mass[j] > self.mass[i]:
                i, j = j, i
            m = self.mass[i] + self.mass[j]
            self.pos[i] = (self.pos[i] * self.mass[i] + self.pos[j] * self.mass[j]) / m
            self.vel[i] = (self.vel[i] * self.mass[i] + self.vel[j] * self.mass[j]) / m
            self.mass[i] = m
            alive[j] = False
            merged.append((int(self.uids[i]), int(self.uids[j])))
        self._keep(alive)
        return merged
