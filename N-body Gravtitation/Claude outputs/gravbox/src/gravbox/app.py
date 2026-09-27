"""Application controller: event loop, actions, and glue between modules."""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pygame

from gravbox import __app_name__, __version__, paths, storage
from gravbox.config import INTEGRATOR_LABELS, TARGET_FPS, Settings
from gravbox.physics import NBodySystem
from gravbox.platform_utils import enable_high_dpi
from gravbox.presets import DEFAULT_PRESET, PRESETS, PRESETS_BY_KEY, build_preset, palette_color
from gravbox.recorder import Recorder
from gravbox.render.camera import Camera2D, Camera3D
from gravbox.render.renderer2d import Renderer2D
from gravbox.render.renderer3d import GL_AVAILABLE, GL_IMPORT_ERROR, Renderer3D
from gravbox.trails import TrailStore
from gravbox.ui.hud import hint_bar, text_box
from gravbox.ui.panel import Panel
from gravbox.ui.theme import Colors, Theme, ui_scale_for
from gravbox.ui.widgets import blit_text
from gravbox.window import Window

PRESET_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
               pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0]
HINT_2D = "LMB click/drag: add body   RMB drag: pan   Wheel: zoom   F: fit   Tab: 3D   H: panel"
HINT_3D = "LMB drag: orbit   RMB drag: pan   Wheel: zoom   F: fit   Tab: 2D   H: panel"
CLICK_THRESHOLD = 5  # pixels of movement before a click becomes a drag


def make_icon(size: int = 64) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    ring = int(size * 0.36)
    pygame.draw.circle(surf, (*Colors.CANVAS, 255), (c, c), c)
    pygame.draw.circle(surf, (78, 205, 196, 255), (c, c), ring, max(1, size // 24))
    pygame.draw.circle(surf, (255, 214, 102, 255), (c, c), size // 7)
    pygame.draw.circle(surf, (255, 107, 107, 255), (int(c + ring * 0.707), int(c - ring * 0.707)), size // 11)
    return surf


class App:
    def __init__(self, settings: Settings, preset: Optional[str] = None,
                 start_3d: bool = False, snapshot: Optional[str] = None) -> None:
        self.settings = settings
        pygame.init()
        pygame.display.set_caption(f"{__app_name__} {__version__}")
        try:
            pygame.display.set_icon(make_icon())
        except pygame.error:
            pass
        self.window = Window(settings.window)
        self.window.open(gl=False)
        self.clock = pygame.time.Clock()

        self.system = NBodySystem()
        self.trails = TrailStore()
        self.recorder = Recorder()
        self.cam2d = Camera2D()
        self.cam3d = Camera3D()
        self.renderer2d = Renderer2D()
        self.renderer3d = Renderer3D() if GL_AVAILABLE else None
        self.gl_available = GL_AVAILABLE
        self.rng = np.random.default_rng()

        self.mode = "2d"
        self.paused = False
        self.running = True
        self.effective_substeps = settings.sim.substeps
        self.throttled = False
        self.step_ms = 0.0
        self.toasts: List[Tuple[str, tuple, float]] = []
        self.drag = None
        self.current_preset: Optional[str] = None
        self.preset_label = "Custom"
        self._diag_dirty = True
        self._pending_screenshot = False
        self._last_size = None

        self.theme: Optional[Theme] = None
        self.panel = Panel(self)
        self.panel_w = 0
        self.relayout()

        loaded = False
        if snapshot:
            loaded = self.load_snapshot(Path(snapshot))
        if not loaded:
            self.load_preset(preset if preset in PRESETS_BY_KEY else DEFAULT_PRESET)
        if start_3d:
            self.enter_3d()
        if not GL_AVAILABLE:
            self.notify("3D view unavailable: pip install PyOpenGL", Colors.WARN, 6)

    # ================================================================ layout
    def relayout(self) -> None:
        old_canvas = None
        if self._last_size:
            pw = self.panel_w if self.settings.view.panel_visible else 0
            old_canvas = pygame.Rect(0, 0, max(1, self._last_size[0] - pw), max(1, self._last_size[1]))
        w, h = self.window.size()
        self._last_size = (w, h)
        scale = ui_scale_for(w, h)
        if self.theme is None or abs(self.theme.scale - scale) > 1e-3:
            self.theme = Theme(scale)
        self.panel_w = max(1, min(self.theme.px(360), int(w * 0.45)))
        self.panel.layout(self.panel_w, h, self.theme)
        self.renderer2d.invalidate()
        self._rescale_view(old_canvas)

    def _rescale_view(self, old_canvas) -> None:
        """Scale the 2D zoom with the canvas so resizing never crops the scene."""
        new = self.canvas_rect()
        if old_canvas is None or old_canvas.size == new.size:
            return
        ratio = min(new.w / max(1, old_canvas.w), new.h / max(1, old_canvas.h))
        self.cam2d.zoom = min(Camera2D.MAX_ZOOM, max(Camera2D.MIN_ZOOM, self.cam2d.zoom * ratio))
        self.cam2d.set_viewport(new.w, new.h)

    def canvas_rect(self) -> pygame.Rect:
        w, h = self.window.size()
        pw = self.panel_w if self.settings.view.panel_visible else 0
        return pygame.Rect(0, 0, max(1, w - pw), max(1, h))

    def panel_rect(self) -> Optional[pygame.Rect]:
        if not self.settings.view.panel_visible:
            return None
        w, h = self.window.size()
        return pygame.Rect(w - self.panel_w, 0, self.panel_w, h)

    # ============================================================== queries
    def fps(self) -> float:
        return self.clock.get_fps()

    def sim_rate(self) -> float:
        if self.paused:
            return 0.0
        return self.settings.sim.timestep * self.effective_substeps * max(self.fps(), 1.0)

    def is_fullscreen(self) -> bool:
        return self.window.fullscreen

    def gl_status(self) -> str:
        if not GL_AVAILABLE:
            return f"OpenGL unavailable ({GL_IMPORT_ERROR or 'PyOpenGL not installed'}). pip install PyOpenGL"
        name = self.renderer3d.renderer_name if self.renderer3d else ""
        return f"OpenGL ready{': ' + name if name else ''}. Switching lifts flat systems off the plane."

    def notify(self, text: str, color=Colors.TEXT, seconds: float = 2.5) -> None:
        self.toasts.append((text, color, time.monotonic() + seconds))
        self.toasts = self.toasts[-4:]

    # ============================================================== actions
    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def step_once(self) -> None:
        sim = self.settings.sim
        self.paused = True
        if self.system.n:
            self.system.step(sim.timestep, sim.gravity, sim.softening, sim.integrator, sim.damping)
            if sim.merge_on_collision and self.system.merge_collisions():
                self.recorder.rebase()
            self.trails.record(self.system)
            self.recorder.sample(self.system, sim.gravity, sim.softening, record=True)

    def reset(self) -> None:
        self.load_preset(self.current_preset or DEFAULT_PRESET)

    def load_preset(self, key: str) -> None:
        preset = PRESETS_BY_KEY[key]
        self.system.load(build_preset(key, self.settings.sim.gravity, seed=random.randrange(1 << 30)))
        self.system.to_com_frame()
        self.current_preset = key
        self.preset_label = preset.label
        self._after_system_replaced()
        self.notify(f"Loaded preset: {preset.label}")

    def _after_system_replaced(self) -> None:
        if self.mode == "3d" and self.settings.view.perturb_on_3d and self.system.is_flat():
            self.system.perturb_z(self.rng)
        self.trails.clear()
        self.recorder.reset()
        self.effective_substeps = self.settings.sim.substeps
        self._diag_dirty = True
        self.fit_view()
        pygame.display.set_caption(f"{__app_name__} {__version__} - {self.preset_label}")

    def _bodies_changed(self) -> None:
        self.recorder.rebase()
        self._diag_dirty = True

    def on_physics_changed(self, _value=None) -> None:
        self.system.invalidate()
        self._bodies_changed()

    def set_integrator(self, value: str) -> None:
        self.settings.sim.integrator = value
        self.on_physics_changed()
        self.notify(f"Integrator: {INTEGRATOR_LABELS.get(value, value)}")

    def center_com(self) -> None:
        self.system.to_com_frame()
        self.trails.clear()
        self._bodies_changed()
        self.fit_view()
        self.notify("Shifted to centre-of-mass frame")

    def clear_trails(self) -> None:
        self.trails.clear()
        self.notify("Trails cleared")

    def clear_bodies(self) -> None:
        self.system.clear()
        self.current_preset = None
        self.preset_label = "Custom"
        self.recorder.reset()
        self._diag_dirty = True
        self.notify("All bodies removed (trails kept)")

    def remove_last(self) -> None:
        if self.system.remove_last():
            self._bodies_changed()

    def fit_view(self) -> None:
        rect = self.canvas_rect()
        self.cam2d.set_viewport(rect.w, rect.h)
        com, extent = self.system.center_of_mass(), self.system.extent()
        self.cam2d.fit(com[0] - extent, com[0] + extent, com[1] - extent, com[1] + extent, margin=0.04)
        self.cam3d.fit(self.system.extent())
        self.renderer2d.invalidate()

    def toggle_panel(self) -> None:
        old_canvas = self.canvas_rect()
        self.settings.view.panel_visible = not self.settings.view.panel_visible
        self._rescale_view(old_canvas)
        self.panel.captured = None
        self.renderer2d.invalidate()

    # ---------------------------------------------------------- body spawning
    def _orbital_velocity(self, p: np.ndarray) -> np.ndarray:
        s = self.system
        if s.n == 0:
            return np.zeros(3)
        com = s.center_of_mass()
        r = p - com
        r[2] = 0.0
        d = float(np.linalg.norm(r))
        if d < 1e-6:
            return s.com_velocity()
        speed = math.sqrt(self.settings.sim.gravity * s.total_mass() / d)
        return s.com_velocity() + np.array([-r[1], r[0], 0.0]) / d * speed

    def add_body(self, pos, vel=None) -> bool:
        sim, spawn = self.settings.sim, self.settings.spawn
        if self.system.n >= sim.max_bodies:
            self.notify(f"Body limit reached ({sim.max_bodies}). Raise it in BODIES.", Colors.WARN)
            return False
        p = np.array([pos[0], pos[1], 0.0])
        if vel is None:
            if spawn.mode == "orbit":
                vel = self._orbital_velocity(p)
            elif spawn.mode == "random":
                ang = self.rng.uniform(0, 2 * math.pi)
                vel = np.array([math.cos(ang), math.sin(ang), 0.0]) * spawn.speed
            else:
                vel = np.zeros(3)
        self.system.add(p, vel, spawn.mass, palette_color(int(self.system._next_uid)))
        self.current_preset = None
        self.preset_label = "Custom"
        self._bodies_changed()
        return True

    def scatter_bodies(self, count: int = 20) -> None:
        extent = self.system.extent() if self.system.n else 200.0
        com = self.system.center_of_mass()
        added = 0
        for _ in range(count):
            r = self.rng.uniform(0.35, 1.0) * extent
            ang = self.rng.uniform(0, 2 * math.pi)
            p = com + np.array([r * math.cos(ang), r * math.sin(ang), 0.0])
            saved = self.settings.spawn.mode
            self.settings.spawn.mode = "orbit"
            ok = self.add_body(p)
            self.settings.spawn.mode = saved
            if not ok:
                break
            added += 1
        if added:
            self.notify(f"Added {added} orbiting bodies")

    # --------------------------------------------------------------- 2D / 3D
    def toggle_mode(self) -> None:
        if self.mode == "3d":
            self.exit_3d()
        else:
            self.enter_3d()

    def enter_3d(self) -> None:
        if not GL_AVAILABLE or self.renderer3d is None:
            self.notify("3D needs PyOpenGL:  pip install PyOpenGL", Colors.WARN, 5)
            return
        if self.mode == "3d":
            return
        if self.settings.view.perturb_on_3d and self.system.is_flat():
            self.system.perturb_z(self.rng)
            self._bodies_changed()
        try:
            self.window.open(gl=True)
            self.renderer3d.init_gl()
        except Exception as exc:  # driver without a usable GL context
            self.window.open(gl=False)
            self.gl_available = False
            self.notify(f"Could not start OpenGL: {exc}", Colors.DANGER, 6)
            return
        self.mode = "3d"
        self.cam3d.fit(self.system.extent())
        self.relayout()
        self.notify("3D view (OpenGL)")

    def exit_3d(self) -> None:
        if self.mode != "3d":
            return
        self.mode = "2d"
        self.window.open(gl=False)
        self.relayout()
        self.notify("2D view (top-down projection)")

    def perturb_z(self) -> None:
        self.system.perturb_z(self.rng)
        self._bodies_changed()
        self.notify("Added random z offsets / velocities")

    def flatten(self) -> None:
        self.system.flatten()
        self._bodies_changed()
        self.notify("Flattened to the xy-plane")

    def toggle_fullscreen(self) -> None:
        self.drag = None
        self.panel.captured = None
        try:
            self.window.toggle_fullscreen()
            if self.mode == "3d" and self.renderer3d:
                self.renderer3d.init_gl()
        except pygame.error as exc:
            self.notify(f"Fullscreen failed: {exc}", Colors.DANGER)
        self.relayout()

    # ------------------------------------------------------------- data I/O
    def export_csv(self) -> None:
        if not self.recorder.rows:
            self.notify("Nothing recorded yet - run the simulation first", Colors.WARN)
            return
        path = paths.exports_dir() / f"gravbox_series_{paths.timestamp()}.csv"
        try:
            count = self.recorder.export_csv(path)
            self.notify(f"Exported {count:,} samples -> {path.name}", Colors.SUCCESS, 4)
        except OSError as exc:
            self.notify(f"Export failed: {exc}", Colors.DANGER, 5)

    def export_state(self) -> None:
        path = paths.exports_dir() / f"gravbox_state_{paths.timestamp()}.csv"
        try:
            count = storage.export_state_csv(path, self.system)
            self.notify(f"Exported {count} bodies -> {path.name}", Colors.SUCCESS, 4)
        except OSError as exc:
            self.notify(f"Export failed: {exc}", Colors.DANGER, 5)

    def save_snapshot(self) -> None:
        path = paths.saves_dir() / f"snapshot_{paths.timestamp()}.json"
        try:
            storage.save_snapshot(path, self.system, self.settings.to_dict()["sim"], self.preset_label)
            self.notify(f"Snapshot saved -> {path.name}", Colors.SUCCESS, 4)
        except OSError as exc:
            self.notify(f"Save failed: {exc}", Colors.DANGER, 5)

    def load_latest_snapshot(self) -> None:
        path = storage.latest_snapshot(paths.saves_dir())
        if path is None:
            self.notify("No snapshots saved yet", Colors.WARN)
            return
        self.load_snapshot(path)

    def load_snapshot(self, path: Path) -> bool:
        try:
            data = storage.load_snapshot(path)
            bodies = data["bodies"]
            merged = Settings.from_dict({**self.settings.to_dict(), "sim": {**self.settings.to_dict()["sim"],
                                                                            **data["sim"]}})
            self.settings.sim = merged.sim
            self.system.load(bodies, time=float(data["time"]))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.notify(f"Could not load snapshot: {exc}", Colors.DANGER, 5)
            return False
        self.current_preset = None
        self.preset_label = str(data.get("label") or path.stem)
        self._after_system_replaced()
        self.notify(f"Loaded {path.name}", Colors.SUCCESS)
        return True

    def screenshot(self) -> None:
        self._pending_screenshot = True

    def _capture_screenshot(self) -> None:
        path = paths.screenshots_dir() / f"gravbox_{paths.timestamp()}.png"
        try:
            if self.mode == "3d" and self.renderer3d:
                image = self.renderer3d.read_pixels(*self.window.size())
            else:
                image = pygame.display.get_surface().copy()
            pygame.image.save(image, str(path))
            self.notify(f"Screenshot -> {path.name}", Colors.SUCCESS, 4)
        except Exception as exc:
            self.notify(f"Screenshot failed: {exc}", Colors.DANGER, 5)

    def open_data_folder(self) -> None:
        if not paths.open_in_file_manager(paths.data_dir()):
            self.notify(f"Data folder: {paths.data_dir()}", Colors.TEXT, 6)

    def save_settings(self) -> None:
        self.window.remember_size()
        self.window.export(self.settings.window)
        try:
            self.settings.save(paths.settings_file())
        except OSError:
            pass

    # =============================================================== events
    def handle_event(self, ev) -> None:
        if ev.type == pygame.QUIT:
            self.running = False
            return
        if ev.type == pygame.KEYDOWN:
            self.on_key(ev)
            return
        if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and ev.button in (4, 5):
            return  # legacy wheel buttons; MOUSEWHEEL handles zoom/scroll
        if ev.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
            return

        pos = ev.pos if hasattr(ev, "pos") else pygame.mouse.get_pos()
        prect = self.panel_rect()
        local = (pos[0] - prect.x, pos[1]) if prect else pos

        if self.panel.captured is not None and ev.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
            self.panel.handle_event(ev, local)
            return
        if self.drag is not None and ev.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
            self.on_canvas_event(ev, pos)
            return
        if prect is not None and prect.collidepoint(pos):
            self.panel.handle_event(ev, local)
            return
        self.on_canvas_event(ev, pos)

    def on_key(self, ev) -> None:
        k = ev.key
        ctrl = bool(ev.mod & pygame.KMOD_CTRL)
        alt = bool(ev.mod & pygame.KMOD_ALT)
        view = self.settings.view
        sim = self.settings.sim
        if ctrl:
            actions = {pygame.K_s: self.save_snapshot, pygame.K_o: self.load_latest_snapshot,
                       pygame.K_e: self.export_csv, pygame.K_q: self.quit}
            if k in actions:
                actions[k]()
            return
        if k == pygame.K_RETURN and alt or k == pygame.K_F11:
            self.toggle_fullscreen()
        elif k == pygame.K_ESCAPE:
            if self.window.fullscreen:
                self.toggle_fullscreen()
            elif self.drag is not None:
                self.drag = None
        elif k == pygame.K_SPACE:
            self.toggle_pause()
        elif k in (pygame.K_RIGHT, pygame.K_PERIOD):
            self.step_once()
        elif k == pygame.K_r:
            self.reset()
        elif k == pygame.K_TAB:
            self.toggle_mode()
        elif k == pygame.K_f:
            self.fit_view()
        elif k == pygame.K_h:
            self.toggle_panel()
        elif k == pygame.K_c:
            self.clear_trails()
        elif k == pygame.K_t:
            view.show_trails = not view.show_trails
        elif k == pygame.K_g:
            view.show_grid = not view.show_grid
        elif k == pygame.K_v:
            view.show_velocity = not view.show_velocity
        elif k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            sim.substeps = min(64, sim.substeps * 2)
            self.notify(f"Substeps: {sim.substeps}")
        elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
            sim.substeps = max(1, sim.substeps // 2)
            self.notify(f"Substeps: {sim.substeps}")
        elif k in (pygame.K_DELETE, pygame.K_BACKSPACE):
            self.remove_last()
        elif k in (pygame.K_F12, pygame.K_p):
            self.screenshot()
        elif k in PRESET_KEYS:
            index = PRESET_KEYS.index(k)
            if index < len(PRESETS):
                self.load_preset(PRESETS[index].key)

    def on_canvas_event(self, ev, pos) -> None:
        if self.mode == "3d":
            self._canvas_event_3d(ev, pos)
        else:
            self._canvas_event_2d(ev, pos)

    def _canvas_event_2d(self, ev, pos) -> None:
        cam = self.cam2d
        if ev.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            cam.zoom_at(mx, my, 1.15 ** ev.y)
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1:
                self.drag = {"kind": "spawn", "start": pos, "now": pos, "world": cam.screen_to_world(*pos)}
            elif ev.button in (2, 3):
                self.drag = {"kind": "pan", "last": pos}
        elif ev.type == pygame.MOUSEMOTION and self.drag:
            if self.drag["kind"] == "pan":
                cam.pan_pixels(pos[0] - self.drag["last"][0], pos[1] - self.drag["last"][1])
                self.drag["last"] = pos
            else:
                self.drag["now"] = pos
        elif ev.type == pygame.MOUSEBUTTONUP and self.drag:
            drag, self.drag = self.drag, None
            if drag["kind"] == "spawn" and ev.button == 1:
                self.add_body(drag["world"], self._spawn_drag_velocity(drag))

    def _spawn_drag_velocity(self, drag):
        (sx, sy), (ex, ey) = drag["start"], drag["now"]
        if math.hypot(ex - sx, ey - sy) < CLICK_THRESHOLD:
            return None  # plain click: use the spawn mode
        wx, wy = drag["world"]
        tx, ty = self.cam2d.screen_to_world(ex, ey)
        k = self.settings.spawn.drag_scale
        return np.array([(tx - wx) * k, (ty - wy) * k, 0.0])

    def _canvas_event_3d(self, ev, pos) -> None:
        cam = self.cam3d
        if ev.type == pygame.MOUSEWHEEL:
            cam.zoom(1.15 ** ev.y)
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1:
                self.drag = {"kind": "orbit", "last": pos}
            elif ev.button in (2, 3):
                self.drag = {"kind": "pan3d", "last": pos}
        elif ev.type == pygame.MOUSEMOTION and self.drag:
            dx, dy = pos[0] - self.drag["last"][0], pos[1] - self.drag["last"][1]
            self.drag["last"] = pos
            if self.drag["kind"] == "orbit":
                cam.orbit(dx, dy)
            else:
                cam.pan(dx, dy, self.canvas_rect().h)
        elif ev.type == pygame.MOUSEBUTTONUP:
            self.drag = None

    def quit(self) -> None:
        self.running = False

    # =============================================================== update
    def update(self) -> bool:
        if self.paused or self.system.n == 0:
            return False
        sim = self.settings.sim
        target = max(1, int(sim.substeps))
        if sim.auto_throttle:
            self.effective_substeps = max(1, min(self.effective_substeps, target))
        else:
            self.effective_substeps = target
        budget = sim.step_budget_ms / 1000.0
        merged = False
        start = time.perf_counter()
        for _ in range(self.effective_substeps):
            self.system.step(sim.timestep, sim.gravity, sim.softening, sim.integrator, sim.damping)
            if sim.merge_on_collision and self.system.merge_collisions():
                merged = True
            if sim.auto_throttle and time.perf_counter() - start > budget * 3:
                break  # hard stop: never let physics freeze the UI
        elapsed = time.perf_counter() - start
        self.step_ms = elapsed * 1000.0
        if sim.auto_throttle:
            if elapsed > budget and self.effective_substeps > 1:
                self.effective_substeps = max(1, int(self.effective_substeps * 0.7))
            elif elapsed < budget * 0.5 and self.effective_substeps < target:
                self.effective_substeps += 1
        self.throttled = sim.auto_throttle and self.effective_substeps < target

        removed = self.system.remove_non_finite()
        if removed:
            self.paused = True
            merged = True
            self.notify(f"Numerical blow-up: removed {removed} bodies. Lower dt or raise softening.",
                        Colors.DANGER, 6)
        if merged:
            self.recorder.rebase()
        self.trails.record(self.system)
        return True

    # =============================================================== render
    def _hud_items(self, crect: pygame.Rect):
        t = self.theme
        pad = t.px(10)
        items = []
        view, sim = self.settings.view, self.settings.sim
        if view.show_stats:
            d = self.recorder.latest
            lines = [
                (f"{self.preset_label}", Colors.HIGHLIGHT),
                (f"t = {self.system.time:,.2f}    N = {self.system.n}", Colors.TEXT),
                (f"{self.fps():.0f} fps   substeps {self.effective_substeps}/{sim.substeps}   "
                 f"{self.step_ms:.1f} ms", Colors.TEXT),
                (f"dE/E0 = {d.get('rel_drift', 0.0):+.2e}   {INTEGRATOR_LABELS[sim.integrator]}", Colors.TEXT),
            ]
            if self.paused:
                lines.append(("PAUSED  (Space)", Colors.WARN))
            if self.throttled:
                lines.append(("THROTTLED - CPU budget exceeded", Colors.WARN))
            items.append((text_box(lines, t), (pad, pad)))

        hint = hint_bar(HINT_3D if self.mode == "3d" else HINT_2D, t)
        hint_pos = (max(pad, (crect.w - hint.get_width()) // 2), crect.h - hint.get_height() - pad)
        if hint.get_width() < crect.w - 2 * pad:
            items.append((hint, hint_pos))
        if not view.panel_visible:
            tag = hint_bar("H: show panel", t)
            items.append((tag, (crect.w - tag.get_width() - pad, pad)))

        now = time.monotonic()
        self.toasts = [toast for toast in self.toasts if toast[2] > now]
        y = hint_pos[1] - t.px(6)
        for text, color, _ in reversed(self.toasts):
            box = text_box([(text, color)], t, alpha=220)
            y -= box.get_height() + t.px(4)
            items.append((box, (pad, y)))
        return items

    def _draw_spawn_preview(self, canvas: pygame.Surface) -> None:
        d = self.drag
        start, now = d["start"], d["now"]
        r = max(3, int(self.settings.spawn.mass ** (1 / 3) * 0.9 * self.cam2d.zoom))
        pygame.draw.circle(canvas, Colors.MUTED, start, min(r, 400), 1)
        if math.hypot(now[0] - start[0], now[1] - start[1]) >= CLICK_THRESHOLD:
            pygame.draw.line(canvas, Colors.HIGHLIGHT, start, now, 2)
            ang = math.atan2(now[1] - start[1], now[0] - start[0])
            for side in (-0.5, 0.5):
                tip = (now[0] - 12 * math.cos(ang + side), now[1] - 12 * math.sin(ang + side))
                pygame.draw.line(canvas, Colors.HIGHLIGHT, now, tip, 2)
            v = self._spawn_drag_velocity(d)
            blit_text(canvas, self.theme.font("small"), f"v = {float(np.linalg.norm(v)):.2f}",
                      Colors.HIGHLIGHT, (now[0] + 10, now[1] + 10))

    def render(self) -> None:
        if self.mode == "3d" and self.renderer3d is not None:
            self._render_3d()
        else:
            self._render_2d()
        if self._pending_screenshot:
            self._pending_screenshot = False
            self._capture_screenshot()
        pygame.display.flip()

    def _update_panel_mouse(self) -> None:
        prect = self.panel_rect()
        mx, my = pygame.mouse.get_pos()
        self.panel.mouse = (mx - prect.x, my) if prect and prect.collidepoint((mx, my)) else None

    def _render_2d(self) -> None:
        screen = pygame.display.get_surface()
        crect = self.canvas_rect()
        screen.fill(Colors.BG)
        canvas = screen.subsurface(crect)
        self.renderer2d.draw(canvas, self.cam2d, self.system, self.trails, self.settings.view,
                             line_scale=max(1, round(self.theme.scale)))
        if self.drag and self.drag["kind"] == "spawn":
            self._draw_spawn_preview(canvas)
        for surf, pos in self._hud_items(crect):
            screen.blit(surf, pos)
        if self.settings.view.panel_visible:
            self._update_panel_mouse()
            screen.blit(self.panel.draw(), (crect.w, 0))

    def _render_3d(self) -> None:
        crect = self.canvas_rect()
        overlays = [(f"hud{i}", surf, x, y) for i, (surf, (x, y)) in enumerate(self._hud_items(crect))]
        if self.settings.view.panel_visible:
            self._update_panel_mouse()
            overlays.append(("panel", self.panel.draw(), crect.w, 0))
        self.renderer3d.render(self.window.size(), crect.w, self.cam3d, self.system, self.trails,
                               self.settings.view, overlays)

    # ================================================================= loop
    def run(self) -> int:
        try:
            while self.running:
                self.clock.tick(TARGET_FPS)
                if self.window.size() != self._last_size:
                    self.window.remember_size()
                    self.relayout()
                for ev in pygame.event.get():
                    self.handle_event(ev)
                stepped = self.update()
                if stepped or self._diag_dirty:
                    sim = self.settings.sim
                    self.recorder.sample(self.system, sim.gravity, sim.softening, record=stepped)
                    self._diag_dirty = False
                self.render()
        finally:
            self.save_settings()
            pygame.quit()
        return 0


# ==================================================================== CLI
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gravbox", description="Interactive N-body gravity simulator.")
    parser.add_argument("--preset", choices=[p.key for p in PRESETS], help="initial preset")
    parser.add_argument("--load", metavar="FILE", help="load a snapshot JSON on start")
    parser.add_argument("--3d", dest="three_d", action="store_true", help="start in the 3D view")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--fullscreen", action="store_true", help="start fullscreen")
    mode.add_argument("--windowed", action="store_true", help="start windowed")
    parser.add_argument("--data-dir", metavar="DIR", help="folder for settings, exports and screenshots")
    parser.add_argument("--reset-settings", action="store_true", help="ignore saved settings")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.data_dir:
        os.environ["GRAVBOX_DATA_DIR"] = str(Path(args.data_dir).expanduser().resolve())
    enable_high_dpi()
    settings = Settings() if args.reset_settings else Settings.load(paths.settings_file())
    if args.fullscreen:
        settings.window.fullscreen = True
    elif args.windowed:
        settings.window.fullscreen = False
    try:
        app = App(settings, preset=args.preset, start_3d=args.three_d, snapshot=args.load)
    except pygame.error as exc:
        print(f"Could not open a window: {exc}", file=sys.stderr)
        return 1
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
