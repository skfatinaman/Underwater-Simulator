import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import time
import config
from camera import Camera
from map_manager import MapManager
from oxygen_system import OxygenSystem
from health_system import HealthSystem

cam = Camera()
world = MapManager()
cam.pos = world.get_spawn_position()

# Oxygen and Health Systems
oxygen = OxygenSystem()
health = HealthSystem()

# Timing for systems update
last_update_time = time.time()
is_moving = False

def draw_background():
    """Alternative to glClearColor using a quad to set background color."""
    c = config.BG_COLOR
    glPushMatrix()
    glLoadIdentity()
    glTranslatef(0, 0, -50) # Move behind the scene
    glColor3f(c[0], c[1], c[2])
    glBegin(GL_QUADS)
    size = 100 
    glVertex3f(-size, -size, 0); glVertex3f(size, -size, 0)
    glVertex3f(size, size, 0); glVertex3f(-size, size, 0)
    glEnd()
    glPopMatrix()

def update():
    """Update oxygen and health systems based on elapsed time."""
    global last_update_time
    
    current_time = time.time()
    delta_time = current_time - last_update_time
    last_update_time = current_time
    
    # Update oxygen (depletes when moving)
    oxygen.update(delta_time)
    
    # Update health (depletes when oxygen is critical)
    health.update(delta_time, oxygen.is_critical())
    
    glutPostRedisplay()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    draw_background()
    cam.apply_view()
    world.draw(cam)
    world.draw_minimap(cam)
    
    # Disable depth test for UI overlay
    glDisable(GL_DEPTH_TEST)
    
    # Draw oxygen and health bars
    oxygen.render(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    health.render(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    
    # Re-enable depth test
    glEnable(GL_DEPTH_TEST)
    
    glutSwapBuffers()

def keyboard(key, x, y):
    global is_moving
    
    # Movement keys - start oxygen depletion
    if key in [b'w', b's', b'a', b'd', b'q', b'e']:
        cam.move(key, world)
        oxygen.start_depletion()
        is_moving = True
    
    # IJKL Looking
    sens = 3.0
    if key == b'i': cam.pitch += sens
    if key == b'k': cam.pitch -= sens
    if key == b'j': cam.yaw -= sens
    if key == b'l': cam.yaw += sens
    
    cam.pitch = max(-89.0, min(89.0, cam.pitch))
    glutPostRedisplay()


def keyboard_up(key, x, y):
    """Handle key release to stop oxygen depletion."""
    global is_moving
    if key in [b'w', b's', b'a', b'd', b'q', b'e']:
        is_moving = False
        oxygen.stop_depletion()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    glutCreateWindow(b"OOP Voxel Map")
    
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, config.WINDOW_WIDTH/config.WINDOW_HEIGHT, 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW)
    
    if getattr(config, "GPU_BACKFACE_CULL", False):
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
    
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutIdleFunc(update)
    glutMainLoop()

if __name__ == "__main__":
    main()
