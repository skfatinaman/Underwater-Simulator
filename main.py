import sys
import math
import time
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import config
from camera import Camera
from seabed import Seabed
from fishes import FishManager
from particles import ParticleManager

cam = Camera()
floor = Seabed()
fishes = FishManager(count=config.FISH_COUNT)
particles = ParticleManager(count=600)

def init():
    c = config.WATER_VOID_COLOR
    glClearColor(c[0], c[1], c[2], 1.0)
    
    # Setup Projection (replacing reshape)
    w, h = 1280, 720
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Reduced far plane for performance (400 -> 150)
    gluPerspective(45.0, w/h, 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW)

def draw_text(x, y, text):
    """Utility to render simple text on screen."""
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

def draw_menu():
    """Draws a 2D Overlay Menu."""
    # Switch to 2D projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1280, 0, 720)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Darken background
    glColor3f(0, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(440, 200); glVertex2f(840, 200)
    glVertex2f(840, 520); glVertex2f(440, 520)
    glEnd()

    # Menu Text
    glColor3f(1, 1, 1)
    draw_text(540, 480, "--- PAUSED ---")
    draw_text(480, 420, "Press 0: Low Graphics")
    draw_text(480, 380, "Press 1: Medium Graphics")
    draw_text(480, 340, "Press 2: High Graphics")
    draw_text(480, 300, "Press 3: Ultra Graphics")
    
    # Fish Count Controls
    draw_text(480, 260, f"Fish Count: {config.FISH_COUNT} (Press +/-)")
    
    draw_text(520, 200, "Press ESC to Resume")

    # Show current setting
    glColor3f(0.5, 1, 0.5)
    draw_text(520, 450, f"Current Level: {config.GRAPHICS_LEVEL}")
    
    # Restore 3D projection
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_hud():
    """Draws a simple HUD with counters."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1280, 0, 720)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glColor3f(1, 1, 1)
    draw_text(20, 700, f"Rocks: {len(floor.rocks)}")
    draw_text(20, 670, f"Plants: {len(floor.seaweeds)}")
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_sonar():
    """Draws a circular sonar map in the top right."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1280, 0, 720)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Sonar Config
    center_x, center_y = 1150, 600
    radius = 100
    scale = 2.0 # Map units to pixels
    
    # Background (Greenish transparent)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0, 0.2, 0, 0.5)
    
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(center_x, center_y)
    for i in range(361):
        rad = math.radians(i)
        glVertex2f(center_x + math.cos(rad) * radius, center_y + math.sin(rad) * radius)
    glEnd()
    
    # Rim
    glLineWidth(2.0)
    glColor3f(0, 0.8, 0)
    glBegin(GL_LINE_LOOP)
    for i in range(361):
        rad = math.radians(i)
        glVertex2f(center_x + math.cos(rad) * radius, center_y + math.sin(rad) * radius)
    glEnd()
    glLineWidth(1.0)
    
    # Sweep Line (Animated)
    t = time.time() * 2
    sweep_x = center_x + math.cos(t) * radius
    sweep_y = center_y + math.sin(t) * radius
    glBegin(GL_LINES)
    glVertex2f(center_x, center_y)
    glVertex2f(sweep_x, sweep_y)
    glEnd()
    
    # Draw Entities
    glPointSize(4.0)
    glBegin(GL_POINTS)
    
    # Player (Center) - White
    glColor3f(1, 1, 1)
    glVertex2f(center_x, center_y)
    
    # Ship (Static at 0,0,0) - Yellow Square-ish
    # Ship is at (0, 0, 0) in world
    dx_ship = 0 - cam.pos[0]
    dz_ship = 0 - cam.pos[2]
    # Rotate by camera yaw to orient map with view? Or Fixed North?
    # Usually sonar rotates with player.
    # If fixed north: just use dx, dz.
    # If rotating: rotate (dx, dz) by -cam.yaw.
    
    # Let's do fixed north for simplicity first (Player moves on map? No, player is center).
    # So map moves around player.
    # To orient "Forward" as "Up" on sonar:
    # We need to rotate world coordinates by -cam.yaw.
    
    yaw_rad = math.radians(cam.yaw + 90) # Adjust for camera coordinate system
    
    def rotate_point(x, z):
        # Rotate (x, z) by -yaw
        c = math.cos(-yaw_rad)
        s = math.sin(-yaw_rad)
        rx = x * c - z * s
        rz = x * s + z * c
        return rx, rz

    # Ship
    sx, sz = rotate_point(dx_ship, dz_ship)
    dist_ship = math.sqrt(sx*sx + sz*sz) * scale
    if dist_ship < radius:
        glColor3f(1, 1, 0) # Yellow
        glVertex2f(center_x + sx * scale, center_y - sz * scale) # Flip Z for screen Y
        
    # Fishes - Red
    glColor3f(1, 0, 0)
    for fish in fishes.fishes:
        dx = fish.x - cam.pos[0]
        dz = fish.z - cam.pos[2]
        fx, fz = rotate_point(dx, dz)
        
        if (fx*fx + fz*fz) * scale*scale < radius*radius:
             glVertex2f(center_x + fx * scale, center_y - fz * scale)
             
    glEnd()
    glPointSize(1.0)
    glDisable(GL_BLEND)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Render the 3D world
    cam.clamp_to_ground(floor)
    cam.apply_view()
    floor.draw(cam.pos)
    
    # Update and draw entities
    if config.STATE == "GAME":
        fishes.update(floor, cam.pos)
        particles.update(cam.pos)
        
    fishes.draw()
    particles.draw()
    
    # Draw HUD
    if config.STATE == "GAME":
        draw_hud()
        draw_sonar()
    
    # If paused, draw the menu on top
    if config.STATE == "MENU":
        draw_menu()
        
    glutSwapBuffers()

def keyboard(key, x, y):
    # Handle ESC key to toggle menu
    if key == b'\x1b':
        config.STATE = "MENU" if config.STATE == "GAME" else "GAME"
    
    if config.STATE == "GAME":
        key = key.upper()
        if key == b'W': cam.move(1)
        if key == b'S': cam.move(-1)
        # Ascend/Descend controls
        if key == b'Q': cam.pos[1] += 1.0
        if key == b'E': cam.pos[1] -= 1.0
    
    elif config.STATE == "MENU":
        # Options for graphics
        if key in [b'0', b'1', b'2', b'3']:
            config.GRAPHICS_LEVEL = int(key)
            # Re-initialize floor spacing to update graphics
            floor.update_quality()
        
        # Adjust Fish Count
        if key == b'+' or key == b'=':
            config.FISH_COUNT += 5
            fishes.set_count(config.FISH_COUNT)
        if key == b'-' or key == b'_':
            config.FISH_COUNT = max(0, config.FISH_COUNT - 5)
            fishes.set_count(config.FISH_COUNT)
            
    glutPostRedisplay()

def special_input(key, x, y):
    if config.STATE == "GAME":
        if key == GLUT_KEY_LEFT:  cam.yaw -= 4.0
        if key == GLUT_KEY_RIGHT: cam.yaw += 4.0
        if key == GLUT_KEY_UP:    cam.pitch += 4.0
        if key == GLUT_KEY_DOWN:  cam.pitch -= 4.0
        cam.pitch = max(-89.0, min(89.0, cam.pitch))
    glutPostRedisplay()

def reshape(w, h):
    if h == 0: h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, w/h, 0.1, 400.0)
    glMatrixMode(GL_MODELVIEW)

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1280, 720)
    glutCreateWindow(b"Scuba Simulator - Pause Menu")
    init()
    glutDisplayFunc(display)
    # glutReshapeFunc(reshape) # Removed as not in usableFunctions.txt
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_input)
    glutIdleFunc(display)
    glutMainLoop()

if __name__ == "__main__":
    main()