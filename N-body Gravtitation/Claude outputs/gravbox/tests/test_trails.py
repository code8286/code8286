import numpy as np

from gravbox.physics import NBodySystem
from gravbox.trails import Trail, TrailStore


def test_min_distance_filter():
    t = Trail(0, (255, 255, 255), capacity=16)
    assert t.append(np.array([0.0, 0, 0]), 1.0)
    assert not t.append(np.array([0.5, 0, 0]), 1.0)
    assert t.append(np.array([2.0, 0, 0]), 1.0)
    assert t.count == 2


def test_decimation_keeps_history_and_bounds_memory():
    t = Trail(0, (255, 255, 255), capacity=64)
    for i in range(1000):
        t.append(np.array([float(i), 0, 0]), 0.0)
    assert t.count <= 64
    assert t.points[0, 0] == 0.0          # the very first point is never lost
    assert t.points[-1, 0] == 999.0       # the newest point is present
    assert np.all(np.diff(t.points[:, 0]) > 0)  # order preserved
    assert t.version > 0


def test_trails_outlive_their_bodies():
    s = NBodySystem()
    s.add((0, 0, 0), (1, 0, 0), 1.0)
    store = TrailStore(min_step=0.0)
    store.record(s)
    s.pos[0, 0] = 5.0
    store.record(s)
    s.clear()
    store.record(s)
    assert len(store.trails) == 1
    trail = next(iter(store.trails.values()))
    assert trail.count == 2 and not trail.alive


def test_clear_bumps_version():
    store = TrailStore()
    v = store.version
    store.clear()
    assert store.version == v + 1 and store.total_points() == 0
