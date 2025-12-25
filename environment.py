from OpenGL.GL import *
import math
import time

def draw_water_surface():
    """Renders a radial light surface that covers the view with a bright center."""
    t = time.time()
    # size is increased to 600 to ensure it covers the horizon even at depth
    size = 600 
    res = 25  # Slightly higher resolution for smoother color transitions
    surface_h = 500.0

    glBegin(GL_QUADS)
    for x in range(-size, size, res):
        for z in range(-size, size, res):
            for dx, dz in [(0,0), (res,0), (res,res), (0,res)]:
                px, pz = x + dx, z + dz
                
                # 1. RADIAL LOGIC (Bright center, dark edges)
                # Calculate distance from the center (0,0)
                dist_from_center = math.sqrt(px**2 + pz**2)
                # Normalize brightness (1.0 at center, 0.0 at far edges)
                radial_factor = max(0.0, 1.0 - (dist_from_center / 500.0))
                
                # 2. SHIMMER LOGIC (The moving waves)
                shimmer = (math.sin(px * 0.05 + t) + math.cos(pz * 0.05 + t * 1.1)) * 0.5 + 0.5
                
                # 3. COLOR BLENDING
                # Combine radial factor and shimmer for final intensity
                intensity = radial_factor * (0.6 + 0.4 * shimmer)
                
                if intensity > 0.8:
                    # Very bright sun rays at the very center
                    glColor3f(0.8, 0.9, 1.0)
                elif intensity > 0.4:
                    # Your requested water color #1da2d8
                    glColor3f(0.11, 0.63, 0.85)
                else:
                    # Deep dark patches at the edges/shadows
                    glColor3f(0.02, 0.1, 0.25)
                
                glVertex3f(float(px), surface_h, float(pz))
    glEnd()