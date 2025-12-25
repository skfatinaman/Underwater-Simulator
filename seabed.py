from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
import time
import math
import config
from ship import Ship

class Seabed:
    def __init__(self):
        self.quad = gluNewQuadric()
        self.ship = Ship()
        self.update_quality()

    def update_quality(self):
        """Re-calculates the grid based on the current GRAPHICS_LEVEL."""
        levels = {0: 24, 1: 14, 2: 8, 3: 4}
        self.spacing = levels.get(config.GRAPHICS_LEVEL, 14)
        self.size = config.SEABED_SIZE
        # Use numpy for coordinate generation
        self.x_coords = np.arange(-self.size, self.size + 1, self.spacing)
        self.z_coords = np.arange(-self.size, self.size + 1, self.spacing)
        
        # Initialize rocks and seaweeds
        self.rocks = []
        self.seaweeds = []
        
        # Simple procedural placement
        rng = np.random.RandomState(42) # Fixed seed for consistency
        for _ in range(60): # Increased rocks
            rx = rng.uniform(-self.size, self.size)
            rz = rng.uniform(-self.size, self.size)
            ry = self.get_height_at(rx, rz)
            scale = rng.uniform(0.5, 2.0)
            self.rocks.append((rx, ry, rz, scale))
            
        # Seaweed clusters
        num_clusters = 80
        for _ in range(num_clusters):
            cluster_x = rng.uniform(-self.size, self.size)
            cluster_z = rng.uniform(-self.size, self.size)
            
            # Plants per cluster
            plants_in_cluster = rng.randint(5, 12)
            for _ in range(plants_in_cluster):
                # Offset from cluster center
                off_x = rng.normal(0, 2.0)
                off_z = rng.normal(0, 2.0)
                
                sx = cluster_x + off_x
                sz = cluster_z + off_z
                
                # Clamp to map
                sx = max(-self.size, min(self.size, sx))
                sz = max(-self.size, min(self.size, sz))
                
                sy = self.get_height_at(sx, sz)
                scale = rng.uniform(0.8, 1.5)
                self.seaweeds.append((sx, sy, sz, scale))
                
        # Generate Corals (Multicolor sticks)
        self.corals = []
        for _ in range(60):
            cx = rng.uniform(-self.size, self.size)
            cz = rng.uniform(-self.size, self.size)
            cy = self.get_height_at(cx, cz)
            scale = rng.uniform(1.0, 2.5)
            # Random bright colors
            r = rng.uniform(0.5, 1.0)
            g = rng.uniform(0.2, 0.8)
            b = rng.uniform(0.2, 0.9)
            self.corals.append((cx, cy, cz, scale, [r, g, b]))

    def get_height_at(self, x, z):
        return config.HILL_INTENSITY * (math.sin(x * 0.08) + math.cos(z * 0.08))

    def get_vertex_color(self, x, y, z, cam_pos, t):
        # Numpy vectorized operations for color math could be done here if inputs were arrays,
        # but since we process vertex by vertex in the draw loop, standard math is acceptable.
        # However, to use numpy "wherever faster", we can treat inputs as simple floats here 
        # but use numpy for vector operations if we were processing batches.
        # For single scalar inputs, python math is faster than numpy scalar overhead.
        # So we keep this scalar for the immediate mode loop.
        
        base = config.SEABED_BASE_COLOR
        water = config.WATER_VOID_COLOR
        
        wave = (math.sin(x * 0.1 + t * 0.5) + math.cos(z * 0.1 + t * 0.7)) * 0.5 + 0.5
        h_shading = (y + config.HILL_INTENSITY) / (config.HILL_INTENSITY * 2)
        
        shading_factor = 0.4 + 0.6 * wave * h_shading
        shaded_color = [b * shading_factor for b in base]
        
        dist = math.sqrt((x-cam_pos[0])**2 + (y-cam_pos[1])**2 + (z-cam_pos[2])**2)
        visibility = max(0.0, min(1.0, 1.0 - (dist / 180.0)))
        
        return (
            shaded_color[0] * visibility + water[0] * (1.0 - visibility),
            shaded_color[1] * visibility + water[1] * (1.0 - visibility),
            shaded_color[2] * visibility + water[2] * (1.0 - visibility)
        )

    def draw_rocks(self, cam_pos):
        glColor3f(0.3, 0.3, 0.35) # Greyish rock color
        for (x, y, z, s) in self.rocks:
            # Culling
            if abs(x - cam_pos[0]) > 100 or abs(z - cam_pos[2]) > 100:
                continue

            glPushMatrix()
            glTranslatef(x, y, z)
            glScalef(s, s*0.7, s)
            # Simple rock shape (deformed sphere)
            glBegin(GL_TRIANGLES)
            # A simple pyramid-like rock for efficiency instead of high-poly sphere
            glVertex3f(0, 1, 0)
            glVertex3f(-1, 0, 1); glVertex3f(1, 0, 1)
            
            glVertex3f(0, 1, 0)
            glVertex3f(1, 0, 1); glVertex3f(1, 0, -1)
            
            glVertex3f(0, 1, 0)
            glVertex3f(1, 0, -1); glVertex3f(-1, 0, -1)
            
            glVertex3f(0, 1, 0)
            glVertex3f(-1, 0, -1); glVertex3f(-1, 0, 1)
            glEnd()
            glPopMatrix()

    def draw_corals(self, cam_pos):
        for (x, y, z, s, c) in self.corals:
            # Culling
            if abs(x - cam_pos[0]) > 80 or abs(z - cam_pos[2]) > 80:
                continue

            glColor3f(*c)
            glPushMatrix()
            glTranslatef(x, y, z)
            glScalef(s, s, s)
            
            # Base stick
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            gluCylinder(self.quad, 0.08, 0.06, 0.5, 6, 1)
            glPopMatrix()
            
            # Branches
            for i in range(6):
                glPushMatrix()
                glRotatef(i * 60, 0, 1, 0)
                glRotatef(35, 1, 0, 0)
                glTranslatef(0, 0.2, 0)
                
                # Branch cylinder
                glPushMatrix()
                glRotatef(-90, 1, 0, 0)
                gluCylinder(self.quad, 0.06, 0.03, 0.6, 5, 1)
                glPopMatrix()
                
                # Sub-branch
                glPushMatrix()
                glTranslatef(0, 0.5, 0)
                glRotatef(40, 0, 0, 1)
                glRotatef(-90, 1, 0, 0)
                gluCylinder(self.quad, 0.03, 0.01, 0.3, 4, 1)
                glPopMatrix()
                
                glPopMatrix()
            glPopMatrix()

    def draw_seaweeds(self, t, cam_pos):
        glColor3f(0.1, 0.6, 0.2) # Green
        for (x, y, z, s) in self.seaweeds:
            # Distance Calculation
            dist = math.sqrt((x - cam_pos[0])**2 + (z - cam_pos[2])**2)
            
            # Culling
            if dist > 100:
                continue
                
            # LOD: Reduce detail if far
            segments = 20
            if dist > 40:
                segments = 5 # Low detail

            glPushMatrix()
            glTranslatef(x, y, z)
            glScalef(s, s, s)
            
            # Draw 5 strands per cluster
            for i in range(5):
                glPushMatrix()
                glRotatef(i * 72, 0, 1, 0)
                # Thicker strands using QUADS (replaced QUAD_STRIP)
                glBegin(GL_QUADS)
                width = 0.15 # Thickness
                for h in range(segments):
                    sway1 = math.sin(t + h * 0.5 + x) * 0.2
                    y1 = h * 0.4
                    sway2 = math.sin(t + (h+1) * 0.5 + x) * 0.2
                    y2 = (h+1) * 0.4
                    
                    glVertex3f(sway1 - width, y1, 0)
                    glVertex3f(sway1 + width, y1, 0)
                    glVertex3f(sway2 + width, y2, 0)
                    glVertex3f(sway2 - width, y2, 0)
                glEnd()
                glPopMatrix()
            glPopMatrix()

    def draw(self, cam_pos):
        t = time.time()
        
        # Draw Ship
        self.ship.draw()
        
        glBegin(GL_QUADS)
        for i in range(len(self.x_coords) - 1):
            for j in range(len(self.z_coords) - 1):
                dist_approx = abs(self.x_coords[i] - cam_pos[0]) + abs(self.z_coords[j] - cam_pos[2])
                if dist_approx > 120: continue # Reduced from 220 for performance

                for dx, dz in [(0,0), (1,0), (1,1), (0,1)]:
                    idx_x, idx_z = i + dx, j + dz
                    x, z = self.x_coords[idx_x], self.z_coords[idx_z]
                    y = self.get_height_at(x, z)
                    glColor3f(*self.get_vertex_color(x, y, z, cam_pos, t))
                    glVertex3f(x, y, z)
        glEnd()
        
        # Draw props
        self.draw_rocks(cam_pos)
        self.draw_corals(cam_pos)
        self.draw_seaweeds(t, cam_pos)