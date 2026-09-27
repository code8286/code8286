import math

import numpy as np
import pytest

from gravbox.physics import NBodySystem, accelerations, body_radius, potential_energy

G, EPS = 1.0, 0.5


def binary_system(m=1000.0, d=100.0):
    s = NBodySystem()
    v = math.sqrt(G * m / (2 * d))
    s.add((d / 2, 0, 0), (0, v, 0), m, (255, 0, 0))
    s.add((-d / 2, 0, 0), (0, -v, 0), m, (0, 0, 255))
    return s


def total_energy(s):
    return s.kinetic_energy() + s.potential_energy(G, EPS)


def test_two_body_acceleration_matches_newton():
    pos = np.array([[0.0, 0, 0], [10.0, 0, 0]])
    mass = np.array([5.0, 3.0])
    a = accelerations(pos, mass, G=2.0, eps=0.0)
    assert a[0, 0] == pytest.approx(2.0 * 3.0 / 100.0)
    assert a[1, 0] == pytest.approx(-2.0 * 5.0 / 100.0)
    assert np.allclose(a[:, 1:], 0.0)


def test_newtons_third_law_net_force_is_zero():
    rng = np.random.default_rng(0)
    pos = rng.normal(0, 100, (50, 3))
    mass = rng.uniform(1, 10, 50)
    a = accelerations(pos, mass, G, EPS)
    assert np.allclose((mass[:, None] * a).sum(axis=0), 0.0, atol=1e-9)


def test_softening_keeps_coincident_bodies_finite():
    pos = np.zeros((2, 3))
    a = accelerations(pos, np.ones(2), G, eps=1.0)
    assert np.isfinite(a).all()
    assert np.isfinite(potential_energy(pos, np.ones(2), G, 1.0))


def test_potential_energy_pair():
    pos = np.array([[0.0, 0, 0], [3.0, 4.0, 0]])
    assert potential_energy(pos, np.array([2.0, 3.0]), G, 0.0) == pytest.approx(-6.0 / 5.0)


@pytest.mark.parametrize("integrator", ["leapfrog", "rk4"])
def test_accurate_integrators_conserve_energy(integrator):
    s = binary_system()
    e0 = total_energy(s)
    for _ in range(3000):
        s.step(0.01, G, EPS, integrator)
    assert abs((total_energy(s) - e0) / e0) < 1e-4


def test_euler_drifts_more_than_leapfrog():
    drifts = {}
    for integrator in ("euler", "leapfrog"):
        s = binary_system()
        e0 = total_energy(s)
        for _ in range(3000):
            s.step(0.01, G, EPS, integrator)
        drifts[integrator] = abs((total_energy(s) - e0) / e0)
    assert drifts["euler"] > 10 * drifts["leapfrog"]


def test_momentum_is_conserved():
    rng = np.random.default_rng(1)
    s = NBodySystem()
    for _ in range(20):
        s.add(rng.normal(0, 100, 3), rng.normal(0, 2, 3), rng.uniform(1, 50))
    p0 = s.momentum()
    for _ in range(500):
        s.step(0.01, G, EPS)
    assert np.allclose(s.momentum(), p0, atol=1e-8)


def test_com_frame_zeroes_position_and_momentum():
    s = binary_system()
    s.pos += 123.0
    s.vel += 4.0
    s.to_com_frame()
    assert np.allclose(s.center_of_mass(), 0.0, atol=1e-10)
    assert np.allclose(s.momentum(), 0.0, atol=1e-10)


def test_damping_removes_energy():
    s = binary_system()
    ke0 = s.kinetic_energy()
    for _ in range(200):
        s.step(0.01, G, EPS, damping=0.99)
    assert s.kinetic_energy() < ke0


def test_merge_conserves_mass_and_momentum():
    s = NBodySystem()
    s.add((0, 0, 0), (1, 0, 0), 10.0)
    s.add((0.5, 0, 0), (-1, 2, 0), 30.0)
    s.add((500, 0, 0), (0, 0, 0), 1.0)
    m0, p0 = s.total_mass(), s.momentum()
    merged = s.merge_collisions()
    assert len(merged) == 1
    assert s.n == 2
    assert s.total_mass() == pytest.approx(m0)
    assert np.allclose(s.momentum(), p0)
    survivor, absorbed = merged[0]
    assert survivor == 1 and absorbed == 0  # heavier body survives


def test_uids_are_never_reused():
    s = NBodySystem()
    first = s.add((0, 0, 0), (0, 0, 0), 1.0)
    s.clear()
    second = s.add((0, 0, 0), (0, 0, 0), 1.0)
    assert second != first


def test_add_rejects_bad_input():
    s = NBodySystem()
    with pytest.raises(ValueError):
        s.add((0, 0, 0), (0, 0, 0), 0.0)
    with pytest.raises(ValueError):
        s.add((math.nan, 0, 0), (0, 0, 0), 1.0)


def test_remove_non_finite():
    s = binary_system()
    s.pos[0, 0] = np.inf
    assert s.remove_non_finite() == 1
    assert s.n == 1


def test_perturb_and_flatten():
    s = binary_system()
    assert s.is_flat()
    s.perturb_z(np.random.default_rng(0))
    assert not s.is_flat()
    s.flatten()
    assert s.is_flat()


def test_round_trip_bodies():
    s = binary_system()
    t = NBodySystem()
    t.load(s.to_bodies(), time=5.0)
    assert np.allclose(t.pos, s.pos) and np.allclose(t.vel, s.vel) and np.allclose(t.mass, s.mass)
    assert t.time == 5.0


def test_radius_grows_with_mass():
    assert body_radius(8.0) == pytest.approx(2 * body_radius(1.0))
