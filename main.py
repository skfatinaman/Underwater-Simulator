import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import time
import math
import config
from camera import Camera
from map_manager import MapManager
from oxygen_system import OxygenSystem
from health_system import HealthSystem
from first_person_view import FirstPersonView
from background import UnderwaterBackground
from settings_menu import SettingsMenu

cam = Camera()
world = MapManager()
cam.pos = world.get_spawn_position()

# Oxygen and Health Systems
oxygen = OxygenSystem()
health = HealthSystem()

# First Person View
first_person = FirstPersonView()

# Background and Settings
background = UnderwaterBackground()
settings_menu = SettingsMenu(background)

# Timing for systems update
last_update_time = time.time()
is_moving = False

# Camera view mode - toggles between normal view and camera view
camera_view_mode = False

def draw_camera_overlay():
    """Draw camera recording overlay when in camera view mode."""
    # Set up 2D orthographic projection for overlay
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, config.WINDOW_WIDTH, 0, config.WINDOW_HEIGHT, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw camera frame as 4 L-shaped corners - moved inwards
    frame_thickness = 8
    frame_length = 60
    frame_offset = 30
    
    glColor3f(0.1, 0.1, 0.1)  # Dark gray/black
    
    # Top-left corner L
    glBegin(GL_QUADS)
    glVertex2f(frame_offset, config.WINDOW_HEIGHT - frame_length - frame_offset)
    glVertex2f(frame_offset + frame_thickness, config.WINDOW_HEIGHT - frame_length - frame_offset)
    glVertex2f(frame_offset + frame_thickness, config.WINDOW_HEIGHT - frame_offset)
    glVertex2f(frame_offset, config.WINDOW_HEIGHT - frame_offset)
    glEnd()
    glBegin(GL_QUADS)
    glVertex2f(frame_offset, config.WINDOW_HEIGHT - frame_offset - frame_thickness)
    glVertex2f(frame_offset + frame_length, config.WINDOW_HEIGHT - frame_offset - frame_thickness)
    glVertex2f(frame_offset + frame_length, config.WINDOW_HEIGHT - frame_offset)
    glVertex2f(frame_offset, config.WINDOW_HEIGHT - frame_offset)
    glEnd()
    
    # Top-right corner L
    glBegin(GL_QUADS)
    glVertex2f(config.WINDOW_WIDTH - frame_offset - frame_thickness, config.WINDOW_HEIGHT - frame_length - frame_offset)
    glVertex2f(config.WINDOW_WIDTH - frame_offset, config.WINDOW_HEIGHT - frame_length - frame_offset)
    glVertex2f(config.WINDOW_WIDTH - frame_offset, config.WINDOW_HEIGHT - frame_offset)
    glVertex2f(config.WINDOW_WIDTH - frame_offset - frame_thickness, config.WINDOW_HEIGHT - frame_offset)
    glEnd()
    glBegin(GL_QUADS)
    glVertex2f(config.WINDOW_WIDTH - frame_offset - frame_length, config.WINDOW_HEIGHT - frame_offset - frame_thickness)
    glVertex2f(config.WINDOW_WIDTH - frame_offset, config.WINDOW_HEIGHT - frame_offset - frame_thickness)
    glVertex2f(config.WINDOW_WIDTH - frame_offset, config.WINDOW_HEIGHT - frame_offset)
    glVertex2f(config.WINDOW_WIDTH - frame_offset - frame_length, config.WINDOW_HEIGHT - frame_offset)
    glEnd()
    
    # Bottom-left corner L
    glBegin(GL_QUADS)
    glVertex2f(frame_offset, frame_offset)
    glVertex2f(frame_offset + frame_thickness, frame_offset)
    glVertex2f(frame_offset + frame_thickness, frame_offset + frame_length)
    glVertex2f(frame_offset, frame_offset + frame_length)
    glEnd()
    glBegin(GL_QUADS)
    glVertex2f(frame_offset, frame_offset)
    glVertex2f(frame_offset + frame_length, frame_offset)
    glVertex2f(frame_offset + frame_length, frame_offset + frame_thickness)
    glVertex2f(frame_offset, frame_offset + frame_thickness)
    glEnd()
    
    # Bottom-right corner L
    glBegin(GL_QUADS)
    glVertex2f(config.WINDOW_WIDTH - frame_offset - frame_thickness, frame_offset)
    glVertex2f(config.WINDOW_WIDTH - frame_offset, frame_offset)
    glVertex2f(config.WINDOW_WIDTH - frame_offset, frame_offset + frame_length)
    glVertex2f(config.WINDOW_WIDTH - frame_offset - frame_thickness, frame_offset + frame_length)
    glEnd()
    glBegin(GL_QUADS)
    glVertex2f(config.WINDOW_WIDTH - frame_offset - frame_length, frame_offset)
    glVertex2f(config.WINDOW_WIDTH - frame_offset, frame_offset)
    glVertex2f(config.WINDOW_WIDTH - frame_offset, frame_offset + frame_thickness)
    glVertex2f(config.WINDOW_WIDTH - frame_offset - frame_length, frame_offset + frame_thickness)
    glEnd()
    
    # Draw recording indicator (red circle with REC text)
    overlay_x = config.WINDOW_WIDTH - 120
    overlay_y = config.WINDOW_HEIGHT - 50
    
    glColor3f(1.0, 0.0, 0.0)  # Red
    dot_radius = 25
    dot_center_x = overlay_x + 40
    dot_center_y = overlay_y - 15
    
    # Draw circle as filled polygon
    glBegin(GL_TRIANGLES)
    for i in range(32):
        angle1 = (i / 32.0) * 2 * math.pi
        angle2 = ((i + 1) / 32.0) * 2 * math.pi
        glVertex2f(dot_center_x, dot_center_y)
        glVertex2f(dot_center_x + dot_radius * math.cos(angle1), dot_center_y + dot_radius * math.sin(angle1))
        glVertex2f(dot_center_x + dot_radius * math.cos(angle2), dot_center_y + dot_radius * math.sin(angle2))
    glEnd()
    
    # Draw "REC" text inside the circle
    glColor3f(1.0, 1.0, 1.0)  # White
    text = "REC"
    text_x = dot_center_x - 15
    text_y = dot_center_y - 5
    glRasterPos2f(text_x, text_y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
    
    # Restore matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def restart_simulation():
    """Reset all game systems to initial state."""
    global is_moving, last_update_time, cam
    
    # Reset movement state
    is_moving = False
    
    # Reset camera to spawn position
    cam.pos = world.get_spawn_position()
    cam.yaw = 0.0
    cam.pitch = 0.0
    
    # Reset oxygen system
    oxygen.level = 100.0
    oxygen.is_depleting = False
    
    # Reset health system
    health.reset()
    
    # Reset timer
    last_update_time = time.time()

def display():
    global camera_view_mode
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Draw gradient background
    background.draw()
    
    if camera_view_mode:
        # Camera view mode - show view from camera model's perspective
        cam_pos_backup = list(cam.pos)
        cam_yaw_backup = cam.yaw
        cam_pitch_backup = cam.pitch
        
        # Offset to camera model position (camera is on left of hand)
        offset_x = -0.3
        offset_y = -0.2
        offset_z = -0.5
        
        # Apply offset in camera's local space
        rad_yaw = math.radians(cam.yaw)
        cam.pos[0] += offset_x * math.cos(rad_yaw) - offset_z * math.sin(rad_yaw)
        cam.pos[1] += offset_y
        cam.pos[2] += offset_x * math.sin(rad_yaw) + offset_z * math.cos(rad_yaw)
        
        # Rotation adjustment to match camera model angle
        cam.yaw += 15
        cam.pitch -= 8
        
        cam.apply_view()
        
        # Restore camera state
        cam.pos = cam_pos_backup
        cam.yaw = cam_yaw_backup
        cam.pitch = cam_pitch_backup
    else:
        # Normal view mode
        cam.apply_view()
    
    world.draw(cam)
    
    if not camera_view_mode:
        world.draw_minimap(cam)
    
    # Draw first person camera (only in normal view)
    if not camera_view_mode:
        glLoadIdentity()
        first_person.draw()
    
    # Draw oxygen and health bars (only in normal view)
    if not camera_view_mode:
        oxygen.render(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        health.render(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    
    # Draw camera overlay if in camera view mode
    if camera_view_mode:
        draw_camera_overlay()
    
    # Draw death screen if player is dead
    if health.is_dead:
        health.draw_death_screen(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    
    # Draw settings menu if open
    settings_menu.draw()
    
    glutSwapBuffers()

def keyboard(key, x, y):
    global is_moving
    
    # Handle restart key when dead
    if health.is_dead and key == b'1':
        restart_simulation()
        glutPostRedisplay()
        return
    
    # Prevent all other actions when dead
    if health.is_dead:
        return
    
    # Check if settings menu handles the key
    if settings_menu.handle_key(key):
        glutPostRedisplay()
        return
    
    # Settings menu toggle
    if key == b'`' or key == b'~':
        settings_menu.toggle()
        glutPostRedisplay()
        return
    
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

def mouse(button, state, x, y):
    """Handle mouse button clicks - right click toggles camera view."""
    global camera_view_mode
    
    if button == GLUT_RIGHT_BUTTON:
        if state == GLUT_DOWN:
            camera_view_mode = not camera_view_mode
            glutPostRedisplay()

def keyboard_up(key, x, y):
    """Handle key release to stop oxygen depletion."""
    global is_moving
    # Don't process key release when dead
    if health.is_dead:
        return
    if key in [b'w', b's', b'a', b'd', b'q', b'e']:
        is_moving = False
        oxygen.stop_depletion()

def update():
    """Update oxygen and health systems based on elapsed time."""
    global last_update_time
    
    # Don't update game state when dead
    if health.is_dead:
        glutPostRedisplay()
        return
    
    current_time = time.time()
    delta_time = current_time - last_update_time
    last_update_time = current_time
    
    # Update oxygen (depletes when moving)
    oxygen.update(delta_time)
    
    # Update health (depletes when oxygen is critical)
    health.update(delta_time, oxygen.is_critical())
    
    # Check if player has died
    health.is_depleted()
    
    glutPostRedisplay()
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    glutCreateWindow(b"Underwater Simulator")
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, config.WINDOW_WIDTH/config.WINDOW_HEIGHT, 0.1, 150.0)
    glMatrixMode(GL_MODELVIEW)
    
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutMouseFunc(mouse)
    glutIdleFunc(update)
    glutMainLoop()

if __name__ == "__main__":
    main()
