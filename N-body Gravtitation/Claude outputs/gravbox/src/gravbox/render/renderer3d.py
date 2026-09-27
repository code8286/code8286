"""OpenGL 3D renderer (fixed-function pipeline via PyOpenGL).

Why OpenGL rather than Vulkan: Python has no maintained high-level Vulkan
binding, and raw Vulkan needs a hand-written swapchain, render pass, pipeline
and SPIR-V shaders before a single triangle appears. OpenGL gives the same
hardware-accelerated result and runs on every desktop GPU driver.

The 2D control panel and HUD are rendered with pygame into ordinary surfaces
and composited on top of the 3D scene as textured quads, so the UI behaves
identically in both modes.
"""

from __future__ import annotations

import numpy as np
import pygame

from gravbox.render.camera import nice_step
from gravbox.render.imageutil import bytes_to_surface, surface_to_bytes
from gravbox.ui.theme import Colors

try:
    from OpenGL import GL as gl
    from OpenGL import GLU as glu

    GL_AVAILABLE = True
    GL_IMPORT_ERROR = ""
except Exception as exc:  # ImportError, or a broken platform plugin
    gl = glu = None
    GL_AVAILABLE = False
    GL_IMPORT_ERROR = str(exc)


def _rgb(color, factor=1.0):
    return tuple(min(1.0, c / 255.0 * factor) for c in color[:3])


class Renderer3D:
    def __init__(self) -> None:
        self._sphere = None
        self._quadric = None
        self._textures = {}
        self.renderer_name = ""

    def init_gl(self) -> None:
        """(Re)create GL state. Must be called after every OpenGL set_mode."""
        self._textures = {}
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LEQUAL)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
        gl.glEnable(gl.GL_NORMALIZE)
        gl.glShadeModel(gl.GL_SMOOTH)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, (0.28, 0.28, 0.32, 1.0))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, (0.95, 0.95, 0.95, 1.0))
        gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE)
        self._quadric = glu.gluNewQuadric()
        glu.gluQuadricNormals(self._quadric, glu.GLU_SMOOTH)
        self._sphere = gl.glGenLists(1)
        gl.glNewList(self._sphere, gl.GL_COMPILE)
        glu.gluSphere(self._quadric, 1.0, 18, 12)
        gl.glEndList()
        name = gl.glGetString(gl.GL_RENDERER)
        self.renderer_name = name.decode(errors="replace") if isinstance(name, bytes) else str(name or "")

    # ---------------------------------------------------------------- frame
    def render(self, win_size, canvas_w, cam, system, trails, view, overlays) -> None:
        W, H = win_size
        cw = max(1, int(canvas_w))
        gl.glViewport(0, 0, W, H)
        gl.glClearColor(*_rgb(Colors.CANVAS), 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Scene only in the canvas area -> correct aspect ratio, no stretching.
        gl.glViewport(0, 0, cw, H)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(cam.fov, cw / max(1, H), max(0.05, cam.dist * 0.001), cam.dist * 50.0 + 5000.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        eye, tgt = cam.eye(), cam.target
        glu.gluLookAt(eye[0], eye[1], eye[2], tgt[0], tgt[1], tgt[2], 0.0, 0.0, 1.0)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (0.4, 0.3, 1.0, 0.0))

        gl.glDisable(gl.GL_LIGHTING)
        if view.show_grid:
            self._draw_grid(cam)
        if view.show_trails:
            self._draw_trails(trails, view)
        if view.show_velocity:
            self._draw_velocities(system)
        self._draw_bodies(system, cam)
        if view.show_com and system.n:
            self._draw_com(system, cam)
        self._draw_overlays(W, H, overlays)

    def _draw_grid(self, cam) -> None:
        step = nice_step(cam.dist / 6.0)
        n = 10
        gx = round(cam.target[0] / step) * step
        gy = round(cam.target[1] / step) * step
        ext = n * step
        gl.glLineWidth(1.0)
        gl.glBegin(gl.GL_LINES)
        for i in range(-n, n + 1):
            gl.glColor3f(*_rgb(Colors.GRID_MAJOR if i % 5 == 0 else Colors.GRID))
            gl.glVertex3f(gx + i * step, gy - ext, 0.0)
            gl.glVertex3f(gx + i * step, gy + ext, 0.0)
            gl.glVertex3f(gx - ext, gy + i * step, 0.0)
            gl.glVertex3f(gx + ext, gy + i * step, 0.0)
        # axes
        gl.glColor3f(0.75, 0.3, 0.35)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(ext * 0.3, 0, 0)
        gl.glColor3f(0.3, 0.7, 0.45)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, ext * 0.3, 0)
        gl.glColor3f(0.35, 0.5, 0.85)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, 0, ext * 0.3)
        gl.glEnd()

    def _draw_trails(self, trails, view) -> None:
        gl.glLineWidth(float(max(1, int(view.trail_width))))
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        for trail in trails.trails.values():
            if trail.count < 2:
                continue
            gl.glColor3f(*_rgb(trail.color, 0.6 if trail.alive else 0.38))
            pts = np.ascontiguousarray(trail.points, dtype=np.float32)
            gl.glVertexPointer(3, gl.GL_FLOAT, 0, pts)
            gl.glDrawArrays(gl.GL_LINE_STRIP, 0, trail.count)
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glLineWidth(1.0)

    def _draw_velocities(self, system) -> None:
        gl.glBegin(gl.GL_LINES)
        for p, v, c in zip(system.pos.tolist(), system.vel.tolist(), system.colors):
            gl.glColor3f(*_rgb(c))
            gl.glVertex3f(*p)
            gl.glVertex3f(p[0] + v[0] * 2.0, p[1] + v[1] * 2.0, p[2] + v[2] * 2.0)
        gl.glEnd()

    def _draw_bodies(self, system, cam) -> None:
        if system.n == 0:
            return
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glEnable(gl.GL_COLOR_MATERIAL)
        min_r = cam.dist * 0.003
        for p, r, c in zip(system.pos.tolist(), system.radii().tolist(), system.colors):
            gl.glColor3f(*_rgb(c))
            gl.glPushMatrix()
            gl.glTranslatef(p[0], p[1], p[2])
            s = max(r, min_r)
            gl.glScalef(s, s, s)
            gl.glCallList(self._sphere)
            gl.glPopMatrix()
        gl.glDisable(gl.GL_COLOR_MATERIAL)
        gl.glDisable(gl.GL_LIGHTING)

    def _draw_com(self, system, cam) -> None:
        c = system.center_of_mass()
        s = cam.dist * 0.02
        gl.glColor3f(*_rgb(Colors.HIGHLIGHT))
        gl.glBegin(gl.GL_LINES)
        for axis in range(3):
            a, b = c.copy(), c.copy()
            a[axis] -= s
            b[axis] += s
            gl.glVertex3f(*a)
            gl.glVertex3f(*b)
        gl.glEnd()

    # ------------------------------------------------------------- overlays
    def _draw_overlays(self, W, H, overlays) -> None:
        gl.glViewport(0, 0, W, H)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, W, 0, H, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_TEXTURE_2D)
        for key, surface, x, y in overlays:
            self._blit(key, surface, x, y, H)
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glEnable(gl.GL_DEPTH_TEST)

    def _blit(self, key, surface, x, y, H) -> None:
        w, h = surface.get_size()
        if w == 0 or h == 0:
            return
        data = surface_to_bytes(surface, "RGBA", True)
        tex = self._textures.get(key)
        if tex is None:
            tex = gl.glGenTextures(1)
            self._textures[key] = tex
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
        y0 = H - y - h
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 0)
        gl.glVertex2f(x, y0)
        gl.glTexCoord2f(1, 0)
        gl.glVertex2f(x + w, y0)
        gl.glTexCoord2f(1, 1)
        gl.glVertex2f(x + w, y0 + h)
        gl.glTexCoord2f(0, 1)
        gl.glVertex2f(x, y0 + h)
        gl.glEnd()

    def read_pixels(self, W: int, H: int) -> pygame.Surface:
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
        data = gl.glReadPixels(0, 0, W, H, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        if hasattr(data, "tobytes"):
            data = data.tobytes()
        image = bytes_to_surface(bytes(data), (W, H), "RGB")
        return pygame.transform.flip(image, False, True)
