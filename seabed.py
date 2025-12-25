from OpenGL.GL import *
import numpy as np
import time
import math
import config

class Seabed:
    def __init__(self):
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
        for _ in range(30): # 30 Rocks
            rx = rng.uniform(-self.size, self.size)
            rz = rng.uniform(-self.size, self.size)
            ry = self.get_height_at(rx, rz)
            scale = rng.uniform(0.5, 2.0)
            self.rocks.append((rx, ry, rz, scale))
            
        for _ in range(50): # 50 Seaweeds clusters
            sx = rng.uniform(-self.size, self.size)
            sz = rng.uniform(-self.size, self.size)
            sy = self.get_height_at(sx, sz)
            scale = rng.uniform(0.8, 1.5)
            self.seaweeds.append((sx, sy, sz, scale))

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

    def draw_rocks(self):
        glColor3f(0.3, 0.3, 0.35) # Greyish rock color
        for (x, y, z, s) in self.rocks:
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

    def draw_seaweeds(self, t):
        glColor3f(0.1, 0.6, 0.2) # Green
        for (x, y, z, s) in self.seaweeds:
            glPushMatrix()
            glTranslatef(x, y, z)
            glScalef(s, s, s)
            
            # Draw 3 strands per cluster
            for i in range(3):
                glPushMatrix()
                glRotatef(i * 120, 0, 1, 0)
                glBegin(GL_LINE_STRIP)
                for h in range(10):
                    # Waving motion
                    sway = math.sin(t + h * 0.5 + x) * 0.2
                    glVertex3f(sway, h * 0.5, 0)
                glEnd()
                glPopMatrix()
            glPopMatrix()

    def draw(self, cam_pos):
        t = time.time()
        glBegin(GL_QUADS)
        for i in range(len(self.x_coords) - 1):
            for j in range(len(self.z_coords) - 1):
                dist_approx = abs(self.x_coords[i] - cam_pos[0]) + abs(self.z_coords[j] - cam_pos[2])
                if dist_approx > 220: continue 

                for dx, dz in [(0,0), (1,0), (1,1), (0,1)]:
                    idx_x, idx_z = i + dx, j + dz
                    x, z = self.x_coords[idx_x], self.z_coords[idx_z]
                    y = self.get_height_at(x, z)
                    glColor3f(*self.get_vertex_color(x, y, z, cam_pos, t))
                    glVertex3f(x, y, z)
        glEnd()
        
        # Draw props
        self.draw_rocks()
        self.draw_seaweeds(t)