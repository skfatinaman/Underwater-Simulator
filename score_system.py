from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import time


class ScoreSystem:
    def __init__(self):
        self.score = 0
        # shutter animation state
        self.shutter_duration = 0.6  # total seconds for close+open
        self.shutter_elapsed = 0.0
        self.shutter_active = False
        self._last_trigger = 0.0

    def add_point(self):
        self.score += 1

    def trigger_shutter(self):
        self.shutter_active = True
        self.shutter_elapsed = 0.0
        self._last_trigger = time.time()

    def update(self, dt):
        if not self.shutter_active:
            return
        self.shutter_elapsed += dt
        if self.shutter_elapsed >= self.shutter_duration:
            self.shutter_active = False
            self.shutter_elapsed = 0.0

    def draw(self, w, h):
        # Draw score text (top-right)
        # Ensure overlays draw on top
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, w, 0, h)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Score text
        text = f"Score: {self.score}"
        glColor3f(1.0, 1.0, 1.0)
        glRasterPos2f(w - 150, h - 40)
        for c in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

        # Draw shutter if active
        if self.shutter_active:
            t = self.shutter_elapsed / max(1e-6, self.shutter_duration)
            # progress goes 0->1->0 (closing then opening)
            if t <= 0.5:
                prog = (t / 0.5)  # 0..1 closing
            else:
                prog = ((1.0 - t) / 0.5)  # 1..0 opening
            prog = max(0.0, min(1.0, prog))

            half_h = (h * 0.5) * prog

            # Draw two black rectangles from top and bottom
            glColor3f(0.0, 0.0, 0.0)
            glBegin(GL_QUADS)
            # top quad
            glVertex2f(0, h)
            glVertex2f(w, h)
            glVertex2f(w, h - half_h)
            glVertex2f(0, h - half_h)
            # bottom quad
            glVertex2f(0, 0)
            glVertex2f(w, 0)
            glVertex2f(w, half_h)
            glVertex2f(0, half_h)
            glEnd()

            # brief white flash at midpoint when fully closed
            if prog > 0.98:
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glColor4f(1.0, 1.0, 1.0, 0.6)
                glBegin(GL_QUADS)
                glVertex2f(0, 0)
                glVertex2f(w, 0)
                glVertex2f(w, h)
                glVertex2f(0, h)
                glEnd()
                glDisable(GL_BLEND)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        # Restore GL state
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
