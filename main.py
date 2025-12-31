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

def draw_first_person_camera():
    """Draw camera model in first person view (blocky hand holding camera)."""
    glPushMatrix()
    
    # Position in bottom-right corner of view
    glTranslatef(0.5, -0.35, -1.5)
    glRotatef(-15, 0, 1, 0)  # Slight angle for natural look
    glRotatef(-8, 1, 0, 0)
    glRotatef(5, 0, 0, 1)
    
    # ARM - One simple rectangle coming from bottom
    glPushMatrix()
    glColor3f(0.88, 0.68, 0.58)  # Skin tone
    glBegin(GL_QUADS)
    # Front face
    glVertex3f(-0.05, -0.8, -0.05)
    glVertex3f(0.05, -0.8, -0.05)
    glVertex3f(0.05, 0.05, -0.05)
    glVertex3f(-0.05, 0.05, -0.05)
    # Back face
    glVertex3f(-0.05, -0.8, 0.05)
    glVertex3f(0.05, -0.8, 0.05)
    glVertex3f(0.05, 0.05, 0.05)
    glVertex3f(-0.05, 0.05, 0.05)
    # Left face
    glVertex3f(-0.05, -0.8, -0.05)
    glVertex3f(-0.05, -0.8, 0.05)
    glVertex3f(-0.05, 0.05, 0.05)
    glVertex3f(-0.05, 0.05, -0.05)
    # Right face
    glVertex3f(0.05, -0.8, -0.05)
    glVertex3f(0.05, -0.8, 0.05)
    glVertex3f(0.05, 0.05, 0.05)
    glVertex3f(0.05, 0.05, -0.05)
    glEnd()
    glPopMatrix()
    
    # FINGERS - 4 small rectangles holding the camera
    finger_positions = [
        (0.18, 0.0, -0.06),
        (0.18, 0.0, -0.02),
        (0.18, 0.0, 0.02),
        (0.18, 0.0, 0.06)
    ]
    
    for fx, fy, fz in finger_positions:
        glPushMatrix()
        glColor3f(0.88, 0.68, 0.58)
        glBegin(GL_QUADS)
        # Front face
        glVertex3f(fx-0.08, fy-0.04, fz-0.015)
        glVertex3f(fx+0.02, fy-0.04, fz-0.015)
        glVertex3f(fx+0.02, fy+0.04, fz-0.015)
        glVertex3f(fx-0.08, fy+0.04, fz-0.015)
        # Back face
        glVertex3f(fx-0.08, fy-0.04, fz+0.015)
        glVertex3f(fx+0.02, fy-0.04, fz+0.015)
        glVertex3f(fx+0.02, fy+0.04, fz+0.015)
        glVertex3f(fx-0.08, fy+0.04, fz+0.015)
        # Top face
        glVertex3f(fx-0.08, fy+0.04, fz-0.015)
        glVertex3f(fx+0.02, fy+0.04, fz-0.015)
        glVertex3f(fx+0.02, fy+0.04, fz+0.015)
        glVertex3f(fx-0.08, fy+0.04, fz+0.015)
        # Bottom face
        glVertex3f(fx-0.08, fy-0.04, fz-0.015)
        glVertex3f(fx+0.02, fy-0.04, fz-0.015)
        glVertex3f(fx+0.02, fy-0.04, fz+0.015)
        glVertex3f(fx-0.08, fy-0.04, fz+0.015)
        glEnd()
        glPopMatrix()
    
    # Camera body (main rectangular body)
    glPushMatrix()
    glTranslatef(0.15, 0.02, 0.0)
    
    # Main camera body
    glColor3f(0.35, 0.35, 0.4)
    glScalef(0.65, 0.45, 0.5)
    glutSolidCube(0.35)
    glPopMatrix()
    
    # Top section (viewfinder hump)
    glPushMatrix()
    glTranslatef(0.13, 0.1, 0.0)
    glColor3f(0.3, 0.3, 0.35)
    glScalef(0.5, 0.25, 0.42)
    glutSolidCube(0.3)
    glPopMatrix()
    
    # Lens housing (protruding section)
    glPushMatrix()
    glTranslatef(0.23, 0.02, 0.0)
    glColor3f(0.25, 0.25, 0.3)
    glScalef(0.35, 0.35, 0.35)
    glutSolidCube(0.35)
    glPopMatrix()
    
    # Lens glass (dark)
    glPushMatrix()
    glTranslatef(0.29, 0.02, 0.0)
    glColor3f(0.05, 0.05, 0.1)
    glutSolidSphere(0.065, 24, 24)
    glPopMatrix()
    
    # Lens rim (metallic ring)
    glPushMatrix()
    glTranslatef(0.29, 0.02, 0.0)
    glColor3f(0.7, 0.7, 0.75)
    glutSolidTorus(0.012, 0.07, 12, 24)
    glPopMatrix()
    
    # Shutter button (red button on top)
    glPushMatrix()
    glTranslatef(0.12, 0.12, 0.05)
    glColor3f(0.9, 0.2, 0.15)
    glutSolidCylinder(0.015, 0.02, 10, 10)
    glPopMatrix()
    
    # Flash (small silver rectangle)
    glPushMatrix()
    glTranslatef(0.18, 0.1, 0.07)
    glColor3f(0.9, 0.9, 0.95)
    glScalef(0.2, 0.15, 0.15)
    glutSolidCube(0.15)
    glPopMatrix()
    
    # Grip texture (small dark rectangle on front)
    glPushMatrix()
    glTranslatef(0.08, 0.0, 0.09)
    glColor3f(0.15, 0.15, 0.2)
    glScalef(0.3, 0.35, 0.08)
    glutSolidCube(0.25)
    glPopMatrix()
    
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
    
    # Draw first person camera (after world, before UI)
    glLoadIdentity()
    draw_first_person_camera()
    
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
