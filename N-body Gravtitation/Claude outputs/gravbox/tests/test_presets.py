import numpy as np
import pytest

from gravbox.physics import NBodySystem
from gravbox.presets import DEFAULT_PRESET, PRESETS, PRESETS_BY_KEY, build_preset


@pytest.mark.parametrize("preset", PRESETS, ids=lambda p: p.key)
def test_preset_is_valid(preset):
    bodies = build_preset(preset.key, G=1.0, seed=42)
    assert 2 <= len(bodies) <= 400
    s = NBodySystem()
    s.load(bodies)
    assert np.isfinite(s.pos).all() and np.isfinite(s.vel).all()
    assert (s.mass > 0).all()
    assert len(s.colors) == s.n


@pytest.mark.parametrize("preset", PRESETS, ids=lambda p: p.key)
def test_preset_runs_stably_for_a_while(preset):
    s = NBodySystem()
    s.load(build_preset(preset.key, G=1.0, seed=7))
    s.to_com_frame()
    e0 = s.kinetic_energy() + s.potential_energy(1.0, 2.0)
    for _ in range(300):
        s.step(0.005, 1.0, 2.0, "leapfrog")
    e1 = s.kinetic_energy() + s.potential_energy(1.0, 2.0)
    assert np.isfinite(s.pos).all()
    assert abs((e1 - e0) / e0) < 1e-3


def test_presets_are_deterministic_with_seed():
    assert build_preset("solar", seed=3) == build_preset("solar", seed=3)


def test_default_and_unknown():
    assert DEFAULT_PRESET in PRESETS_BY_KEY
    with pytest.raises(KeyError):
        build_preset("nope")


def test_figure_eight_has_zero_momentum():
    s = NBodySystem()
    s.load(build_preset("figure8"))
    assert np.allclose(s.momentum(), 0.0, atol=1e-6)


def test_circular_speeds_scale_with_gravity():
    slow = build_preset("binary", G=1.0)
    fast = build_preset("binary", G=4.0)
    assert fast[0]["vel"][1] == pytest.approx(2 * slow[0]["vel"][1])
