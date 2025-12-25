import random
import math
import time
from OpenGL.GL import *
from OpenGL.GLUT import *

class Particle:
    def __init__(self, x, y, z, p_type):
        self.x = x
        self.y = y
        self.z = z
        self.type = p_type # 'snow' or 'bubble'
        self.active = True
        
        if self.type == 'snow':
            self.size = random.uniform(0.02, 0.05)
            self.speed_y = random.uniform(-0.02, 0.02) # Drift up or down slightly
            # Grey to White
            gray = random.uniform(0.5, 1.0)
            self.color = [gray, gray, gray]
        else: # bubble
            self.size = random.uniform(0.05, 0.2)
            self.speed_y = random.uniform(0.05, 0.15) # Rise up
            self.color = [0.8, 0.9, 1.0, 0.4] # Transparent white-ish
            
    def update(self):
        self.y += self.speed_y
        
        if self.type == 'snow':
            # Slight drift
            self.x += random.uniform(-0.01, 0.01)
            self.z += random.uniform(-0.01, 0.01)
        elif self.type == 'bubble':
            # Wiggle
            self.x += math.sin(self.y * 5) * 0.01
            self.z += math.cos(self.y * 5) * 0.01
            
            # Reset if too high (handled by manager typically, but self-check helps)
            if self.y > 100:
                self.active = False

class ParticleManager:
    def __init__(self, count=500):
        self.particles = []
        self.target_count = count
        
    def update(self, cam_pos):
        # 1. Remove far particles (Reduced range)
        spawn_radius = 25.0
        despawn_radius = 40.0
        
        self.particles = [p for p in self.particles if 
                          p.active and 
                          math.sqrt((p.x - cam_pos[0])**2 + (p.y - cam_pos[1])**2 + (p.z - cam_pos[2])**2) < despawn_radius]
        
        # 2. Spawn new particles
        current_count = len(self.particles)
        if current_count < self.target_count:
            for _ in range(self.target_count - current_count):
                # Spawn around camera
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(5, spawn_radius)
                height_offset = random.uniform(-20, 20)
                
                x = cam_pos[0] + math.cos(angle) * dist
                y = cam_pos[1] + height_offset
                z = cam_pos[2] + math.sin(angle) * dist
                
                # Determine type
                p_type = 'snow' if random.random() < 0.95 else 'bubble'
                
                # Correction for bubbles: spawn them lower so they rise into view
                if p_type == 'bubble':
                    y -= 10 
                    
                self.particles.append(Particle(x, y, z, p_type))
                
        # 3. Update all
        for p in self.particles:
            p.update()
            
    def draw(self):
        # Removed blend enabling as per strict function list
        
        # Draw Snow (Points/Quads)
        glBegin(GL_POINTS)
        for p in self.particles:
            if p.type == 'snow':
                glColor3f(*p.color)
                glVertex3f(p.x, p.y, p.z)
        glEnd()
        
        # Draw Bubbles
        for p in self.particles:
            if p.type == 'bubble':
                # Use glColor3f instead of glColor4f (no alpha)
                glColor3f(p.color[0], p.color[1], p.color[2])
                glPushMatrix()
                glTranslatef(p.x, p.y, p.z)
                glutSolidSphere(p.size, 6, 6)
                glPopMatrix()
