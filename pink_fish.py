from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random

class PinkFish:
    def __init__(self, x, z, y):
        self.base_x = x
        self.base_z = z
        self.base_y = y
        self.wander_radius = random.uniform(6.0, 12.0)
        self.phase = random.uniform(0, 6.28318)
        self.speed = random.uniform(0.3, 0.6)
        self.vertical_speed = random.uniform(0.15, 0.3)
        self.size = random.uniform(0.35, 0.55)
        
        # Pink and purple gradient colors
        if random.random() < 0.5:
            self.body_color = (1.0, 0.4, 0.8)  # Bright pink
            self.accent_color = (0.8, 0.2, 0.9)  # Purple
        else:
            self.body_color = (0.9, 0.3, 0.9)  # Magenta
            self.accent_color = (1.0, 0.5, 0.9)  # Light pink
        
        self.angle = 0.0
        self.x = x
        self.y = y
        self.z = z
        self.prev_x = x
        self.prev_z = z

    def update(self, t):
        # Store previous position
        self.prev_x = self.x
        self.prev_z = self.z
        
        circle_x = math.cos(t * self.speed * 0.3 + self.phase) * self.wander_radius
        circle_z = math.sin(t * self.speed * 0.3 + self.phase) * self.wander_radius
        swim_offset_x = math.sin(t * self.speed + self.phase) * 2.0
        swim_offset_z = math.cos(t * self.speed * 0.7 + self.phase) * 2.0
        self.x = self.base_x + circle_x + swim_offset_x
        self.z = self.base_z + circle_z + swim_offset_z
        self.y = self.base_y + math.sin(t * self.vertical_speed + self.phase) * 1.5
        
        # Calculate direction from actual movement
        dx = self.x - self.prev_x
        dz = self.z - self.prev_z
        
        # Only update angle if fish is actually moving
        if abs(dx) > 0.001 or abs(dz) > 0.001:
            self.angle = math.atan2(dz, dx)

    def draw(self):
        import time
        t = time.time()
        flow_wave = math.sin(t * 2.5 + self.phase) * 8
        
        # Main body (elongated and elegant)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glColor3f(*self.body_color)
        glScalef(self.size * 1.3, self.size * 0.7, self.size * 0.6)
        glutSolidSphere(1.0, 14, 14)
        glPopMatrix()
        
        # Tail connector
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.0, 0, 0)
        glColor3f(*self.body_color)
        glScalef(self.size * 0.5, self.size * 0.5, self.size * 0.4)
        glutSolidSphere(1.0, 12, 12)
        glPopMatrix()
        
        # Long flowing tail - upper section
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.6, self.size * 0.2, 0)
        glRotatef(flow_wave, 0, 0, 1)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.8, self.size * 0.8, self.size * 0.05)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Long flowing tail - lower section
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.6, -self.size * 0.2, 0)
        glRotatef(-flow_wave, 0, 0, 1)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.8, self.size * 0.8, self.size * 0.05)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Flowing tail end - upper ribbon
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 2.8, self.size * 0.4, 0)
        glRotatef(flow_wave * 1.5, 0, 0, 1)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.2, self.size * 0.6, self.size * 0.03)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Flowing tail end - lower ribbon
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 2.8, -self.size * 0.4, 0)
        glRotatef(-flow_wave * 1.5, 0, 0, 1)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.2, self.size * 0.6, self.size * 0.03)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Upper dorsal fin (large and flowing)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.1, self.size * 0.8, 0)
        glRotatef(flow_wave * 0.5, 1, 0, 0)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.0, self.size * 1.2, self.size * 0.04)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Flowing side fins (like ribbons)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.4, 0, self.size * 0.5)
        glRotatef(30 + flow_wave * 0.7, 1, 0, 0)
        glRotatef(20, 0, 1, 0)
        glColor3f(*self.accent_color)
        glScalef(self.size * 0.12, self.size * 1.5, self.size * 0.04)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.4, 0, -self.size * 0.5)
        glRotatef(-30 - flow_wave * 0.7, 1, 0, 0)
        glRotatef(-20, 0, 1, 0)
        glColor3f(*self.accent_color)
        glScalef(self.size * 0.12, self.size * 1.5, self.size * 0.04)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Eyes with sparkle
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.9, self.size * 0.3, self.size * 0.35)
        glColor3f(0.2, 0.1, 0.3)
        glutSolidSphere(self.size * 0.15, 10, 10)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.9, self.size * 0.3, -self.size * 0.35)
        glColor3f(0.2, 0.1, 0.3)
        glutSolidSphere(self.size * 0.15, 10, 10)
        glPopMatrix()
        
        # Eye highlights
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.95, self.size * 0.35, self.size * 0.35)
        glColor3f(1.0, 1.0, 1.0)
        glutSolidSphere(self.size * 0.06, 8, 8)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.95, self.size * 0.35, -self.size * 0.35)
        glColor3f(1.0, 1.0, 1.0)
        glutSolidSphere(self.size * 0.06, 8, 8)
        glPopMatrix()
