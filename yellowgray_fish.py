from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random

class YellowGrayFish:
    def __init__(self, x, z, y):
        self.base_x = x
        self.base_z = z
        self.base_y = y
        self.wander_radius = random.uniform(5.0, 10.0)
        self.phase = random.uniform(0, 6.28318)
        self.speed = random.uniform(0.4, 0.7)
        self.vertical_speed = random.uniform(0.2, 0.35)
        self.size = random.uniform(0.3, 0.5)
        
        # Yellow and gray color combinations
        if random.random() < 0.5:
            self.body_color = (1.0, 0.9, 0.2)  # Bright yellow
            self.accent_color = (0.5, 0.5, 0.5)  # Medium gray
        else:
            self.body_color = (0.9, 0.85, 0.3)  # Golden yellow
            self.accent_color = (0.6, 0.6, 0.6)  # Light gray
        
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
        swim_offset_x = math.sin(t * self.speed + self.phase) * 1.8
        swim_offset_z = math.cos(t * self.speed * 0.7 + self.phase) * 1.8
        self.x = self.base_x + circle_x + swim_offset_x
        self.z = self.base_z + circle_z + swim_offset_z
        self.y = self.base_y + math.sin(t * self.vertical_speed + self.phase) * 1.2
        
        # Calculate direction from actual movement
        dx = self.x - self.prev_x
        dz = self.z - self.prev_z
        
        # Only update angle if fish is actually moving
        if abs(dx) > 0.001 or abs(dz) > 0.001:
            self.angle = math.atan2(dz, dx)

    def draw(self):
        import time
        t = time.time()
        tail_wave = math.sin(t * 3.0 + self.phase) * 12
        
        # Main diamond body
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glRotatef(45, 0, 0, 1)
        glColor3f(*self.body_color)
        glScalef(self.size * 1.5, self.size * 1.5, self.size * 0.7)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Gray stripe across middle
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glRotatef(45, 0, 0, 1)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.5, self.size * 0.5, self.size * 0.75)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Simple tail fin
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.3, 0, 0)
        glRotatef(tail_wave, 0, 1, 0)
        glColor3f(*self.body_color)
        glScalef(self.size * 1.0, self.size * 1.0, self.size * 0.08)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Side fins
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.3, 0, self.size * 0.6)
        glColor3f(*self.accent_color)
        glScalef(self.size * 0.1, self.size * 0.8, self.size * 0.05)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.3, 0, -self.size * 0.6)
        glColor3f(*self.accent_color)
        glScalef(self.size * 0.1, self.size * 0.8, self.size * 0.05)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.3, 0, -self.size * 0.6)
        glColor3f(*self.accent_color)
        glScalef(self.size * 0.1, self.size * 0.8, self.size * 0.05)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Eyes
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.8, self.size * 0.3, self.size * 0.4)
        glColor3f(0.0, 0.0, 0.0)
        glutSolidSphere(self.size * 0.14, 10, 10)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.8, self.size * 0.3, -self.size * 0.4)
        glColor3f(0.0, 0.0, 0.0)
        glutSolidSphere(self.size * 0.14, 10, 10)
        glPopMatrix()
