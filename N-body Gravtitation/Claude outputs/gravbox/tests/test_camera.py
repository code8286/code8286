import numpy as np
import pytest

from gravbox.render.camera import Camera2D, Camera3D, nice_step


def test_nice_step():
    assert nice_step(0.7) == 1.0
    assert nice_step(1.5) == 2.0
    assert nice_step(3.2) == 5.0
    assert nice_step(7.0) == 10.0
    assert nice_step(230.0) == 500.0


def test_world_screen_round_trip():
    cam = Camera2D()
    cam.set_viewport(800, 600)
    cam.cx, cam.cy, cam.zoom = 10.0, -5.0, 2.5
    sx, sy = cam.world_to_screen(42.0, 17.0)
    assert cam.screen_to_world(sx, sy) == pytest.approx((42.0, 17.0))


def test_y_axis_points_up():
    cam = Camera2D()
    cam.set_viewport(100, 100)
    _, y_low = cam.world_to_screen(0, 0)
    _, y_high = cam.world_to_screen(0, 10)
    assert y_high < y_low


def test_zoom_keeps_cursor_point_fixed():
    cam = Camera2D()
    cam.set_viewport(1000, 700)
    before = cam.screen_to_world(123, 456)
    cam.zoom_at(123, 456, 3.0)
    assert cam.screen_to_world(123, 456) == pytest.approx(before)


def test_fit_is_uniform_and_contains_bounds():
    cam = Camera2D()
    cam.set_viewport(1600, 900)
    cam.fit(-100, 100, -50, 50, margin=0.0)
    x0, y1 = cam.screen_to_world(0, 0)
    x1, y0 = cam.screen_to_world(1600, 900)
    assert x0 <= -100 + 1e-9 and x1 >= 100 - 1e-9 and y0 <= -50 + 1e-9 and y1 >= 50 - 1e-9


def test_array_projection_matches_scalar():
    cam = Camera2D()
    cam.set_viewport(640, 480)
    xs, ys = np.array([1.0, -3.0]), np.array([2.0, 5.0])
    arr = cam.world_to_screen_arr(xs, ys)
    assert tuple(arr[1].tolist()) == pytest.approx(cam.world_to_screen(-3.0, 5.0))


def test_camera3d_orbit_zoom_pan_fit():
    cam = Camera3D()
    cam.fit(100.0)
    d = np.linalg.norm(cam.eye() - cam.target)
    assert d == pytest.approx(cam.dist)
    cam.orbit(0, 10_000)
    assert cam.pitch <= 89.0
    dist = cam.dist
    cam.zoom(2.0)
    assert cam.dist == pytest.approx(dist / 2)
    cam.pan(50, 0, 600)
    assert not np.allclose(cam.target, 0.0)
