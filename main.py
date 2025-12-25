import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import config
from camera import Camera
from seabed import Seabed
from fishes import FishManager

cam = Camera()
floor = Seabed()
fishes = FishManager(count=30)

def init():
    c = config.WATER_VOID_COLOR
    glClearColor(c[0], c[1], c[2], 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)

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

    glDisable(GL_DEPTH_TEST)

    # Darken background
    glColor4f(0, 0, 0, 0.5)
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

    glEnable(GL_DEPTH_TEST)
    
    # Restore 3D projection
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
    
    # Update and draw fishes
    if config.STATE == "GAME":
        fishes.update(floor, cam.pos)
    fishes.draw()
    
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
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_input)
    glutIdleFunc(display)
    glutMainLoop()

if __name__ == "__main__":
    main()