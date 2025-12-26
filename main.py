import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import config
from camera import Camera
from map_manager import MapManager

cam = Camera()
world = MapManager()
cam.pos = world.get_spawn_position()

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

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    draw_background()
    cam.apply_view()
    world.draw(cam)
    world.draw_minimap(cam)
    glutSwapBuffers()

def keyboard(key, x, y):
    cam.move(key, world)
    
    # IJKL Looking
    sens = 3.0
    if key == b'i': cam.pitch += sens
    if key == b'k': cam.pitch -= sens
    if key == b'j': cam.yaw -= sens
    if key == b'l': cam.yaw += sens
    
    cam.pitch = max(-89.0, min(89.0, cam.pitch))
    glutPostRedisplay()

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
    glutIdleFunc(display)
    glutMainLoop()

if __name__ == "__main__":
    main()
