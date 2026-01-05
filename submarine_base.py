from OpenGL.GL import *
from OpenGL.GLUT import *
import math

class SubmarineBase:
    def __init__(self, x=10, y=3, z=10):
        self.x = x
        self.y = y
        self.z = z
        self.radius = 6.0  # refill zone

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)

        # Main body
        glColor3f(0.4, 0.4, 0.45)
        glScalef(6, 2, 2)
        glutSolidSphere(1, 20, 20)

        glPopMatrix()

        # Front dome
        glPushMatrix()
        glTranslatef(self.x + 3.5, self.y, self.z)
        glColor3f(0.2, 0.6, 0.8)
        glutSolidSphere(1.2, 16, 16)
        glPopMatrix()

    def is_inside(self, cam_pos):
        dx = cam_pos[0] - self.x
        dy = cam_pos[1] - self.y
        dz = cam_pos[2] - self.z
        return math.sqrt(dx*dx + dy*dy + dz*dz) <= self.radius

    def refill_player(self, oxygen, health):
        oxygen.level = 100.0
        health.level = 100.0
