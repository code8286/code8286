"""The tabbed control panel (right-hand side of the window).

Layout, top to bottom:
  * title
  * toolbar (always visible): play/pause, step, reset, 2D/3D, fullscreen
  * tab bar: SIM | PHYS | BODIES | VIEW | DATA | HELP
  * scrollable tab content
  * status bar

The panel renders into its own surface so the same code serves the 2D
renderer (blitted directly) and the 3D renderer (uploaded as a texture).
"""

from __future__ import annotations

import pygame

from gravbox import __version__, paths
from gravbox.config import INTEGRATOR_LABELS, SPAWN_MODE_LABELS
from gravbox.presets import PRESETS, PRESETS_BY_KEY
from gravbox.ui.layout import LayoutBuilder
from gravbox.ui.theme import Colors
from gravbox.ui.widgets import blit_text, fit_text

TABS = [("sim", "SIM"), ("physics", "PHYS"), ("bodies", "BODIES"),
        ("view", "VIEW"), ("data", "DATA"), ("help", "HELP")]

INTEGRATOR_NOTES = {
    "euler": "Explicit Euler: simplest, energy drifts - for comparison.",
    "leapfrog": "Leapfrog (KDK): symplectic, excellent long-run energy.",
    "rk4": "RK4: accurate per step, slowly leaks energy over time.",
}


def _fmt_e(v) -> str:
    return f"{v:.4e}"


class Panel:
    def __init__(self, app) -> None:
        self.app = app
        self.tab = "sim"
        self.scroll = 0
        self.captured = None
        self.surface = None
        self.width = self.height = 0
        self.theme = None
        self.fixed = []
        self.content = []
        self.tab_rects = []
        self.content_rect = pygame.Rect(0, 0, 0, 0)
        self.content_h = 0
        self.mouse = None  # mouse position in panel coordinates, or None

    # ---------------------------------------------------------------- layout
    def layout(self, width: int, height: int, theme) -> None:
        self.width, self.height, self.theme = width, height, theme
        self.surface = pygame.Surface((max(1, width), max(1, height)))
        pad = theme.px(12)
        self.pad = pad
        a = self.app

        header = LayoutBuilder(pad, pad, width - 2 * pad, theme)
        header.y += theme.font("title", bold=True).get_linesize() + theme.px(8)
        header.row([
            dict(text=lambda: "Play" if a.paused else "Pause", on_click=a.toggle_pause,
                 style=lambda: "success" if a.paused else "normal"),
            dict(text="Step", on_click=a.step_once),
            dict(text="Reset", on_click=a.reset),
            dict(text=lambda: "2D" if a.mode == "3d" else "3D", on_click=a.toggle_mode,
                 enabled=lambda: a.gl_available or a.mode == "3d"),
            dict(text=lambda: "Window" if a.is_fullscreen() else "Full", on_click=a.toggle_fullscreen),
        ])
        self.fixed = header.widgets

        tab_h = theme.px(30)
        tab_y = header.y
        tab_w = width / len(TABS)
        self.tab_rects = [(key, label, pygame.Rect(int(i * tab_w), tab_y, int((i + 1) * tab_w) - int(i * tab_w), tab_h))
                          for i, (key, label) in enumerate(TABS)]
        top = tab_y + tab_h
        self.status_h = theme.px(26)
        self.content_rect = pygame.Rect(0, top, width, max(1, height - top - self.status_h))
        self.build_content()

    def build_content(self) -> None:
        pad = self.pad
        builder = LayoutBuilder(pad, pad, self.width - 2 * pad - self.theme.px(6), self.theme)
        getattr(self, f"_tab_{self.tab}")(builder)
        self.content = builder.widgets
        self.content_h = builder.y + pad
        self._clamp_scroll()

    def set_tab(self, tab: str) -> None:
        if tab != self.tab:
            self.tab = tab
            self.scroll = 0
            self.captured = None
            self.build_content()

    def _clamp_scroll(self) -> None:
        self.scroll = max(0, min(self.scroll, max(0, self.content_h - self.content_rect.h)))

    # ------------------------------------------------------------------ tabs
    def _tab_sim(self, b: LayoutBuilder) -> None:
        a, sim = self.app, self.app.settings.sim
        b.header("Presets")
        b.grid([dict(text=f"{i + 1 if i < 9 else 0}  {p.label}", on_click=(lambda k=p.key: a.load_preset(k)),
                     active=(lambda k=p.key: a.current_preset == k)) for i, p in enumerate(PRESETS)], cols=2)
        b.paragraph(lambda: PRESETS_BY_KEY[a.current_preset].description
                    if a.current_preset in PRESETS_BY_KEY else "Custom system or loaded snapshot.", max_lines=2)
        b.header("Time")
        b.slider("Substeps per frame", lambda: sim.substeps, lambda v: setattr(sim, "substeps", v),
                 1, 64, "{:d}", integer=True)
        b.slider("Timestep dt", lambda: sim.timestep, lambda v: setattr(sim, "timestep", v),
                 0.0005, 0.05, "{:.4f}", log=True)
        b.kv("Simulation time", lambda: f"{a.system.time:,.2f} t.u.")
        b.kv("Simulation rate", lambda: f"{a.sim_rate():.2f} t.u./s")
        b.header("CPU safety")
        b.toggle("Auto-throttle substeps", lambda: sim.auto_throttle, lambda v: setattr(sim, "auto_throttle", v))
        b.slider("Step budget per frame", lambda: sim.step_budget_ms,
                 lambda v: setattr(sim, "step_budget_ms", v), 2, 40, "{:.0f} ms")
        b.kv("Effective substeps", lambda: f"{a.effective_substeps} / {sim.substeps}",
             lambda: Colors.WARN if a.throttled else Colors.SUCCESS)
        b.kv("Physics time / frame", lambda: f"{a.step_ms:.2f} ms")

    def _tab_physics(self, b: LayoutBuilder) -> None:
        a, sim = self.app, self.app.settings.sim
        b.header("Force law")
        b.slider("Gravitational constant G", lambda: sim.gravity, lambda v: setattr(sim, "gravity", v),
                 0.01, 100.0, "{:.3f}", log=True, on_change=a.on_physics_changed)
        b.slider("Softening length eps", lambda: sim.softening, lambda v: setattr(sim, "softening", v),
                 0.1, 50.0, "{:.2f}", log=True, on_change=a.on_physics_changed)
        b.slider("Velocity damping", lambda: sim.damping, lambda v: setattr(sim, "damping", v),
                 0.990, 1.0, "{:.4f}", on_change=a.on_physics_changed)
        b.paragraph("Damping 1.0000 keeps the system isolated (energy conserving).")
        b.header("Integrator")
        b.segmented(list(INTEGRATOR_LABELS.items()), lambda: sim.integrator, a.set_integrator)
        b.label(lambda: INTEGRATOR_NOTES.get(sim.integrator, ""))
        b.header("Collisions")
        b.toggle("Merge on collision", lambda: sim.merge_on_collision,
                 lambda v: setattr(sim, "merge_on_collision", v))
        b.paragraph("Perfectly inelastic merging conserves mass and momentum and reduces N over time.")
        b.header("Reference frame")
        b.button("Shift to centre-of-mass frame", a.center_com)

    def _tab_bodies(self, b: LayoutBuilder) -> None:
        a, spawn, sim = self.app, self.app.settings.spawn, self.app.settings.sim
        b.header("Add with the mouse")
        b.paragraph("Click the canvas to place a body. Click-and-drag to aim its velocity.")
        b.segmented(list(SPAWN_MODE_LABELS.items()), lambda: spawn.mode, lambda v: setattr(spawn, "mode", v))
        b.slider("Mass", lambda: spawn.mass, lambda v: setattr(spawn, "mass", v),
                 0.1, 50000.0, "{:.1f}", log=True)
        b.slider("Speed (Random mode)", lambda: spawn.speed, lambda v: setattr(spawn, "speed", v),
                 0.0, 60.0, "{:.1f}")
        b.slider("Drag velocity scale", lambda: spawn.drag_scale, lambda v: setattr(spawn, "drag_scale", v),
                 0.01, 1.0, "{:.2f}", log=True)
        b.header("Population")
        b.kv("Bodies", lambda: f"{a.system.n} / {sim.max_bodies}")
        b.kv("Total mass", lambda: f"{a.system.total_mass():,.1f}")
        b.slider("Max bodies", lambda: sim.max_bodies, lambda v: setattr(sim, "max_bodies", v),
                 10, 1000, "{:d}", integer=True)
        b.row([dict(text="Add 20 orbiting", on_click=lambda: a.scatter_bodies(20)),
               dict(text="Remove last", on_click=a.remove_last)])
        b.button("Remove all bodies", a.clear_bodies, style="danger")

    def _tab_view(self, b: LayoutBuilder) -> None:
        a, view = self.app, self.app.settings.view
        b.header("Display")
        b.row([dict(text=lambda: "Switch to 2D" if a.mode == "3d" else "Switch to 3D", on_click=a.toggle_mode,
                    style="primary", enabled=lambda: a.gl_available or a.mode == "3d"),
               dict(text=lambda: "Exit fullscreen" if a.is_fullscreen() else "Fullscreen",
                    on_click=a.toggle_fullscreen)])
        b.row([dict(text="Fit view  (F)", on_click=a.fit_view),
               dict(text="Hide panel (H)", on_click=a.toggle_panel)])
        b.header("Trails")
        b.toggle("Show persistent trails", lambda: view.show_trails, lambda v: setattr(view, "show_trails", v))
        b.slider("Trail width", lambda: view.trail_width, lambda v: setattr(view, "trail_width", v),
                 1, 4, "{:d} px", integer=True)
        b.kv("Stored trail points", lambda: f"{a.trails.total_points():,}")
        b.button("Clear trails  (C)", a.clear_trails)
        b.header("Overlays")
        b.toggle("Grid", lambda: view.show_grid, lambda v: setattr(view, "show_grid", v))
        b.toggle("Velocity vectors", lambda: view.show_velocity, lambda v: setattr(view, "show_velocity", v))
        b.toggle("Centre-of-mass marker", lambda: view.show_com, lambda v: setattr(view, "show_com", v))
        b.toggle("Stats overlay", lambda: view.show_stats, lambda v: setattr(view, "show_stats", v))
        b.header("3D conversion")
        b.toggle("Lift flat systems into 3D", lambda: view.perturb_on_3d,
                 lambda v: setattr(view, "perturb_on_3d", v))
        b.row([dict(text="Perturb z now", on_click=a.perturb_z), dict(text="Flatten to plane", on_click=a.flatten)])
        b.paragraph(a.gl_status())

    def _tab_data(self, b: LayoutBuilder) -> None:
        a = self.app

        def latest(key):
            return lambda: a.recorder.latest.get(key, 0.0)

        def drift_color():
            d = abs(a.recorder.latest.get("rel_drift", 0.0))
            return Colors.SUCCESS if d < 1e-4 else (Colors.WARN if d < 1e-2 else Colors.DANGER)

        b.header("Live diagnostics")
        b.kv("Time", lambda: f"{latest('time')():,.3f}")
        b.kv("Bodies", lambda: f"{a.system.n}")
        b.kv("Kinetic energy", lambda: _fmt_e(latest("kinetic")()))
        b.kv("Potential energy", lambda: _fmt_e(latest("potential")()))
        b.kv("Total energy", lambda: _fmt_e(latest("total")()))
        b.kv("Energy drift dE/E0", lambda: f"{latest('rel_drift')():+.3e}", drift_color)
        b.kv("|Momentum|", lambda: f"{(latest('px')() ** 2 + latest('py')() ** 2 + latest('pz')() ** 2) ** 0.5:.3e}")
        b.kv("Angular momentum Lz", lambda: _fmt_e(latest("lz")()))
        b.kv("FPS", lambda: f"{a.fps():.0f}")
        b.graph("Energy drift dE/E0", lambda: a.recorder.drift, Colors.HIGHLIGHT, 88)
        b.graph("Kinetic energy", lambda: a.recorder.kinetic, Colors.SUCCESS, 88, "{:.3e}")
        b.header("Recording & export")
        b.toggle("Record time series", lambda: a.recorder.recording,
                 lambda v: setattr(a.recorder, "recording", v))
        b.kv("Samples recorded", lambda: f"{len(a.recorder.rows):,}")
        b.row([dict(text="Export series CSV", on_click=a.export_csv),
               dict(text="Export state CSV", on_click=a.export_state)])
        b.row([dict(text="Save snapshot", on_click=a.save_snapshot),
               dict(text="Load latest", on_click=a.load_latest_snapshot)])
        b.row([dict(text="Screenshot", on_click=a.screenshot),
               dict(text="Open data folder", on_click=a.open_data_folder)])

    def _tab_help(self, b: LayoutBuilder) -> None:
        b.header("Keyboard")
        b.label([
            "Space        play / pause",
            "Right / .    single step",
            "R            reset preset",
            "1-9, 0       load preset",
            "Tab          2D <-> 3D",
            "F11 / Alt+Enter  fullscreen",
            "Esc          leave fullscreen",
            "F            fit view",
            "H            hide/show panel",
            "C / T        clear / toggle trails",
            "G / V        grid / velocities",
            "+ / -        faster / slower",
            "Del          remove last body",
            "F12          screenshot",
            "Ctrl+S / O   save / load snapshot",
            "Ctrl+E       export CSV",
            "Ctrl+Q       quit",
        ], Colors.TEXT)
        b.header("Mouse")
        b.label([
            "2D  LMB click   add body",
            "2D  LMB drag    add with velocity",
            "2D  RMB drag    pan",
            "3D  LMB drag    orbit camera",
            "3D  RMB drag    pan camera",
            "Wheel           zoom",
        ], Colors.TEXT)
        b.header("About")
        b.paragraph(f"GravBox v{__version__}. Isolated-system N-body gravity sandbox with "
                    "Plummer softening and symplectic integration.")
        b.paragraph(f"Data folder: {paths.data_dir()}")

    # ------------------------------------------------------------------ draw
    def draw(self) -> pygame.Surface:
        s, t = self.surface, self.theme
        s.fill(Colors.PANEL)
        mouse = self.mouse
        cx, cy = self.pad + t.px(9), self.pad + t.px(11)
        pygame.draw.circle(s, Colors.TEXT, (cx, cy), t.px(3), 1)
        pygame.draw.ellipse(s, Colors.TEXT, (cx - t.px(9), cy - t.px(4), t.px(18), t.px(8)), 1)
        title = blit_text(s, t.font("title"), "GRAVBOX", Colors.TEXT, (self.pad + t.px(26), self.pad))
        blit_text(s, t.font("tiny"), f"N-BODY SANDBOX  v{__version__}", Colors.MUTED,
                  (title.right + t.px(12), title.centery), "midleft")
        for w in self.fixed:
            w.draw(s, t, 0, mouse)

        f = t.font("small")
        for key, label, rect in self.tab_rects:
            active = key == self.tab
            hover = mouse is not None and rect.collidepoint(mouse)
            pill = rect.inflate(-t.px(4), -t.px(8))
            if active:
                pygame.draw.rect(s, Colors.ACCENT_HOVER, pill, border_radius=pill.h // 2)
                pygame.draw.rect(s, Colors.PANEL_EDGE, pill, 1, border_radius=pill.h // 2)
            elif hover:
                pygame.draw.rect(s, Colors.ACCENT, pill, border_radius=pill.h // 2)
            blit_text(s, f, label, Colors.TEXT if active else Colors.MUTED, rect.center, "center")
        pygame.draw.line(s, Colors.PANEL_EDGE, (0, self.content_rect.y - 1), (self.width, self.content_rect.y - 1))

        cr = self.content_rect
        dy = cr.y - self.scroll
        cmouse = None
        if mouse is not None and cr.collidepoint(mouse):
            cmouse = (mouse[0], mouse[1] - dy)
        s.set_clip(cr)
        for w in self.content:
            if w.rect.bottom + dy >= cr.y and w.rect.y + dy <= cr.bottom:
                w.draw(s, t, dy, cmouse)
        s.set_clip(None)

        if self.content_h > cr.h:
            bar_h = max(t.px(24), int(cr.h * cr.h / self.content_h))
            bar_y = cr.y + int((cr.h - bar_h) * self.scroll / max(1, self.content_h - cr.h))
            pygame.draw.rect(s, Colors.PANEL_EDGE, (self.width - t.px(5), bar_y, t.px(3), bar_h),
                             border_radius=t.px(2))

        self._draw_status(s, t)
        pygame.draw.line(s, Colors.PANEL_EDGE, (0, 0), (0, self.height))
        return s

    def _draw_status(self, s, t) -> None:
        a = self.app
        y = self.height - self.status_h
        pygame.draw.rect(s, Colors.BG, (0, y, self.width, self.status_h))
        state = "PAUSED" if a.paused else "RUNNING"
        color = Colors.WARN if a.paused else Colors.SUCCESS
        f = t.font("tiny")
        r = blit_text(s, f, state, color, (self.pad, y + self.status_h // 2), "midleft")
        info = f"{a.mode.upper()}  N={a.system.n}  {a.fps():.0f} fps"
        if a.throttled:
            info += "  THROTTLED"
        blit_text(s, f, fit_text(f, info, self.width - r.right - self.pad * 2), Colors.MUTED,
                  (self.width - self.pad, y + self.status_h // 2), "midright")

    # ---------------------------------------------------------------- events
    def _content_pos(self, local):
        return (local[0], local[1] - self.content_rect.y + self.scroll)

    def handle_event(self, ev, local) -> bool:
        """Route an event whose position (``local``) is in panel coordinates."""
        if self.captured is not None:
            if ev.type == pygame.MOUSEMOTION:
                self.captured.drag(self._content_pos(local))
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.captured = None
            return True
        if ev.type == pygame.MOUSEWHEEL:
            if self.content_rect.collidepoint(local):
                self.scroll -= int(ev.y * self.theme.px(40))
                self._clamp_scroll()
            return True
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for w in self.fixed:
                if w.rect.collidepoint(local) and w.handle(ev, local):
                    return True
            for key, _, rect in self.tab_rects:
                if rect.collidepoint(local):
                    self.set_tab(key)
                    return True
            if self.content_rect.collidepoint(local):
                cpos = self._content_pos(local)
                for w in self.content:
                    if w.rect.collidepoint(cpos) and w.handle(ev, cpos):
                        if w.captures:
                            self.captured = w
                        return True
        return True
