import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_9_BY_15
import time
import math
import config
import traceback
from camera import Camera
from map_manager import MapManager
from oxygen_system import OxygenSystem
from health_system import HealthSystem
from first_person_view import FirstPersonView
from background import UnderwaterBackground
from settings_menu import SettingsMenu
from shark_enemy import SharkManager
from score_system import ScoreSystem
from submarine_base import SubmarineBase

BG_COLOR = [0.294, 0.616, 0.663]

BLOCK_TYPES = {
    1: ((0.8, 0.2, 0.2), 1),  # demo red block
    2: ((0.2, 0.8, 0.2), 2),  # demo green block
    3: ((0.2, 0.2, 0.8), 4),  # demo blue block
    10: ((0.85, 0.75, 0.55), 1),  # sand base
    11: ((0.4, 0.4, 0.45), 2),    # rock
    12: ((1.0, 0.4, 0.6), 2),     # coral pink
    13: ((1.0, 0.9, 0.3), 2),     # coral yellow
    14: ((0.3, 0.6, 1.0), 2),     # coral blue
    15: ((0.8, 0.3, 0.9), 2),     # coral purple
    16: ((0.1, 0.6, 0.2), 3),     # seaweed green
}

MAP_SIZE = 80
MAX_HEIGHT = 15  # Maximum Y the player can reach
MIN_HEIGHT = 0.5 # Minimum Y to stay above the floor

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

LIGHT_AMBIENT = 0.55
LIGHT_DEPTH_DARKEN = 0.02
CAUSTICS_SCALE = 0.25
CAUSTICS_SPEED = 0.4
CAUSTICS_INTENSITY = 0.35

CORAL_REEF_MIN_SIZE = 20
CORAL_REEF_MAX_SIZE = 30

SEAWEED_SEG_LEN = 1.8
SEAWEED_SWAY_AMP = 0.25

CAVE_DARKEN = 0.5

PHONG_ON = False
PHONG_LIGHT_DIR = (0.6, 0.8, 0.2)
PHONG_AMB = 0.3
PHONG_DIFF = 0.7
PHONG_SPEC = 0.15
PHONG_SHININESS = 8.0
MINIMAP_CELL = 4
MINIMAP_VIEW_SIZE = 40
MINIMAP_MARGIN = 10
USE_DYNAMIC_MINIMAP = True
USE_VIEW_CULLING = True
DRAW_RADIUS = 50
USE_MULTITHREADING = False
GPU_BACKFACE_CULL = True
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

# External systems: sharks, scoring, submarine base
shark_manager = SharkManager()
score_system = ScoreSystem()
# place submarine at the fixed starting corner so it's always available
# use a fixed Y so its position doesn't vary between runs
# Place submarine consistently near the player's spawn position so it's available at start
try:
    spawn_pos = world.get_spawn_position()
    # offset a few units from the spawn so player can spot and return to it
    submarine = SubmarineBase(x=spawn_pos[0] + 3.0, y=spawn_pos[1], z=spawn_pos[2] + 3.0)
except Exception:
    # fallback to fixed corner if spawn lookup fails
    submarine = SubmarineBase(x=1.5, y=2.0, z=1.5)

# Blood overlay state (set when shark hits player)
blood_timer = 0.0
blood_duration = 0.8

# Hint shown when player tries to capture while not in first-person
capture_hint_timer = 0.0

# Timing for systems update
last_update_time = time.time()
is_moving = False

# Camera view mode - toggles between normal view and camera view
camera_view_mode = False

def draw_camera_overlay():
    """Draw camera recording overlay when in camera view mode."""
    # Disable depth testing so overlay draws on top
    glDisable(GL_DEPTH_TEST)

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
    # Restore GL state
    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)

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
    try:
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

            # Draw submarine and sharks within the world
            submarine.draw()
            shark_manager.draw(cam)

        # Draw first person camera (only in normal view)
        if not camera_view_mode:
            glLoadIdentity()
            first_person.draw()

        # Draw oxygen and health bars (only in normal view)
        if not camera_view_mode:
            oxygen.render(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
            health.render(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
            # Draw score overlay in normal view
            score_system.draw(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

        # Draw camera overlay if in camera view mode
        if camera_view_mode:
            draw_camera_overlay()

        # Draw death screen if player is dead
        if health.is_dead:
            health.draw_death_screen(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

        # Draw settings menu if open
        settings_menu.draw()

        # Always draw score overlay on top (safe to call again; draw manages matrices)
        score_system.draw(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

        # Blood overlay (red flash) when recent shark collision
        # Capture hint when player tries to take a picture outside first-person
        if capture_hint_timer > 0.0:
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            gluOrtho2D(0, config.WINDOW_WIDTH, 0, config.WINDOW_HEIGHT)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            glDisable(GL_DEPTH_TEST)


            glColor3f(1.0*0.95, 1.0*0.95, 1.0*0.95)
            hint = "Switch to first-person to capture (right-click)."
            # Center the text roughly
            text_x = config.WINDOW_WIDTH // 2 - (len(hint) * 4)
            text_y = 40
            glRasterPos2f(text_x, text_y)
            for ch in hint:
                glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))
            glDisable(GL_BLEND)
            glEnable(GL_DEPTH_TEST)
            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)

        if blood_timer > 0.0:
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            gluOrtho2D(0, config.WINDOW_WIDTH, 0, config.WINDOW_HEIGHT)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
           

            glColor3f(1.0*0.35, 0.0, 0.0)
            glBegin(GL_QUADS)
            glVertex2f(0, 0)
            glVertex2f(config.WINDOW_WIDTH, 0)
            glVertex2f(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
            glVertex2f(0, config.WINDOW_HEIGHT)
            glEnd()
            glDisable(GL_BLEND)
            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)

        glutSwapBuffers()
    except Exception as e:
        # Print exception to console and clear to a visible color so window doesn't go black
        print("Exception in display:", e)
        traceback.print_exc()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glutSwapBuffers()

def keyboard(key, x, y):
    global is_moving
    global capture_hint_timer
    
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

    # Camera shutter/capture: only in first-person view
    if key in (b'c', b'C'):
        if not camera_view_mode:
            score_system.add_point()
            score_system.trigger_shutter()
        else:
            # Provide feedback: console + short on-screen hint
            try:
                print("Capture failed: switch to first-person to capture.")
            except Exception:
                pass
            capture_hint_timer = 1.8
        glutPostRedisplay()
    
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
    global last_update_time, blood_timer
    
    # Don't update game state when dead
    if health.is_dead:
        glutPostRedisplay()
        return
    
    current_time = time.time()
    delta_time = current_time - last_update_time
    last_update_time = current_time
    
    # Update oxygen (depletes when moving)
    oxygen.update(delta_time)

    # Update score system (shutter animation)
    score_system.update(delta_time)
    
    # Update health (depletes when oxygen is critical)
    health.update(delta_time, oxygen.is_critical())
    
    # Check if player has died
    health.is_depleted()

    # Update shark AI and check submarine refill
    # shark_manager.update returns number of collisions this frame
    collisions = shark_manager.update(cam, health, oxygen, delta_time)
    if collisions > 0:
        global blood_timer
        blood_timer = blood_duration
        try:
            print(f"Collisions detected: {collisions}, health now={getattr(health, 'level', None)}")
        except Exception:
            pass
    if submarine.is_inside(cam.pos):
        submarine.refill_player(oxygen, health)

    # Periodic debug: print oxygen and health every 2 seconds so we can see changes
    try:
        if not hasattr(update, "_debug_acc"):
            update._debug_acc = 0.0
        update._debug_acc += delta_time
        if update._debug_acc >= 2.0:
            update._debug_acc = 0.0
            try:
                print(f"Status: O2={oxygen.level:.1f}, HP={getattr(health, 'level', None)}")
            except Exception:
                pass
    except Exception:
        pass

    # Decrease blood timer
    try:
        blood_timer -= delta_time
        if blood_timer < 0.0:
            blood_timer = 0.0
        # Decrease capture hint timer
        global capture_hint_timer
        capture_hint_timer -= delta_time
        if capture_hint_timer < 0.0:
            capture_hint_timer = 0.0
    except Exception:
        pass
    
    glutPostRedisplay()

from OpenGL.GL import *

class UnderwaterBackground:
    """Draws an underwater gradient background from dark blue (bottom) to light blue (top)."""
    
    def __init__(self):
        # Define gradient colors from darkest (bottom) to lightest (top)
        self.num_layers = 50  # More layers = smoother gradient
        
    def draw(self):
        """Draw gradient background using multiple horizontal rectangles."""
        glPushMatrix()
        glLoadIdentity()
        
        # Position far behind the scene
        z_position = -100
        size = 150  # Large size to cover entire view
        
        # Y range for gradient
        y_min = -size
        y_max = size
        layer_height = (y_max - y_min) / self.num_layers
        
        # Color range: dark blue at bottom to light blue at top
        # Deep underwater navy (bottom) - darker and more blue-green
        r_start, g_start, b_start = 0.0, 0.05, 0.15
        # Bright aqua blue (top) - more vibrant underwater feel
        r_end, g_end, b_end = 0.3, 0.7, 0.85
        
        # Draw each horizontal layer with gradually lighter color
        for i in range(self.num_layers):
            # Calculate position
            y_bottom = y_min + (i * layer_height)
            y_top = y_min + ((i + 1) * layer_height)
            
            # Interpolate color (progress from 0 to 1)
            progress = i / (self.num_layers - 1)
            r = r_start + (r_end - r_start) * progress
            g = g_start + (g_end - g_start) * progress
            b = b_start + (b_end - b_start) * progress
            
            glColor3f(r, g, b)
            
            # Draw rectangle for this layer
            glBegin(GL_QUADS)
            glVertex3f(-size, y_bottom, z_position)
            glVertex3f(size, y_bottom, z_position)
            glVertex3f(size, y_top, z_position)
            glVertex3f(-size, y_top, z_position)
            glEnd()
        
        glPopMatrix()

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random

class BlueBlackFish:
    def __init__(self, x, z, y):
        self.base_x = x
        self.base_z = z
        self.base_y = y
        self.wander_radius = random.uniform(5.0, 10.0)
        self.phase = random.uniform(0, 6.28318)
        self.speed = random.uniform(0.5, 1.0)
        self.vertical_speed = random.uniform(0.2, 0.4)
        self.size = random.uniform(0.25, 0.4)
        self.body_color = (0.1, 0.3, 0.8)
        self.stripe_color = (1.0, 0.9, 0.0)
        self.black_color = (0.1, 0.1, 0.1)
        self.angle = 0.0
        self.x = x
        self.y = y
        self.z = z
        self.prev_x = x
        self.prev_z = z

    def update(self, t):
        # Store previous position
        self.prev_x = self.x
        self.prev_z = self.z
        
        circle_x = math.cos(t * self.speed * 0.3 + self.phase) * self.wander_radius
        circle_z = math.sin(t * self.speed * 0.3 + self.phase) * self.wander_radius
        swim_offset_x = math.sin(t * self.speed + self.phase) * 2.0
        swim_offset_z = math.cos(t * self.speed * 0.7 + self.phase) * 2.0
        self.x = self.base_x + circle_x + swim_offset_x
        self.z = self.base_z + circle_z + swim_offset_z
        self.y = self.base_y + math.sin(t * self.vertical_speed + self.phase) * 1.5
        
        # Calculate direction from actual movement
        dx = self.x - self.prev_x
        dz = self.z - self.prev_z
        
        # Only update angle if fish is actually moving
        if abs(dx) > 0.001 or abs(dz) > 0.001:
            self.angle = math.atan2(dz, dx)

    def draw(self):
        # Main body (elongated - more torpedo shaped)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glColor3f(*self.body_color)
        glScalef(self.size * 1.8, self.size * 0.6, self.size * 0.6)
        glutSolidSphere(1.0, 12, 12)
        glPopMatrix()
        
        # Black stripe along top
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(0, self.size * 0.55, 0)
        glColor3f(*self.black_color)
        glScalef(self.size * 1.6, self.size * 0.15, self.size * 0.6)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Yellow accent stripe
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.3, 0, 0)
        glColor3f(*self.stripe_color)
        glScalef(self.size * 0.12, self.size * 0.65, self.size * 0.65)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Tail section
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.4, 0, 0)
        glColor3f(*self.body_color)
        glScalef(self.size * 0.5, self.size * 0.4, self.size * 0.4)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Tail fin (forked style)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.8, self.size * 0.2, 0)
        glColor3f(*self.stripe_color)
        glScalef(self.size * 0.25, self.size * 0.8, self.size * 0.08)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.8, -self.size * 0.2, 0)
        glColor3f(*self.stripe_color)
        glScalef(self.size * 0.25, self.size * 0.8, self.size * 0.08)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Dorsal fin (smaller and pointed)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 0.2, self.size * 0.7, 0)
        glColor3f(*self.black_color)
        glScalef(self.size * 0.6, self.size * 0.5, self.size * 0.06)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Side fins (smaller)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.4, -self.size * 0.1, self.size * 0.5)
        glRotatef(30, 1, 0, 0)
        glColor3f(*self.stripe_color)
        glScalef(self.size * 0.1, self.size * 0.6, self.size * 0.06)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.4, -self.size * 0.1, -self.size * 0.5)
        glRotatef(-30, 1, 0, 0)
        glColor3f(*self.stripe_color)
        glScalef(self.size * 0.1, self.size * 0.6, self.size * 0.06)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Eyes
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 1.0, self.size * 0.2, self.size * 0.35)
        glColor3f(1.0, 1.0, 1.0)
        glutSolidSphere(self.size * 0.15, 8, 8)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 1.0, self.size * 0.2, -self.size * 0.35)
        glColor3f(1.0, 1.0, 1.0)
        glutSolidSphere(self.size * 0.15, 8, 8)
        glPopMatrix()
        
        # Eye pupils
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 1.05, self.size * 0.2, self.size * 0.35)
        glColor3f(0.0, 0.0, 0.0)
        glutSolidSphere(self.size * 0.08, 8, 8)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 1.05, self.size * 0.2, -self.size * 0.35)
        glColor3f(0.0, 0.0, 0.0)
        glutSolidSphere(self.size * 0.08, 8, 8)
        glPopMatrix()

import math
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import config

class Camera:
    def __init__(self):
        self.pos = [2.0, 2.0, 2.0]
        self.yaw = 45.0
        self.pitch = 0.0
        self.look_dir = [0, 0, 0]
        self.speed = 0.3
        self.visible = True

    def update_vectors(self):
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)
        self.look_dir[0] = math.cos(rad_yaw) * math.cos(rad_pitch)
        self.look_dir[1] = math.sin(rad_pitch)
        self.look_dir[2] = math.sin(rad_yaw) * math.cos(rad_pitch)

    def try_move(self, new_pos, world):
        """Enforces map boundaries, max height, and non-passable blocks."""
        # Horizontal and Vertical Boundary checks
        if not (0 <= new_pos[0] <= config.MAP_SIZE and 
                0 <= new_pos[2] <= config.MAP_SIZE and
                config.MIN_HEIGHT <= new_pos[1] <= config.MAX_HEIGHT):
            return

        # Collision check with blocks
        if not world.is_occupied(new_pos[0], new_pos[1], new_pos[2]):
            self.pos = new_pos

    def move(self, key, world):
        rad = math.radians(self.yaw)
        new_pos = list(self.pos)
        
        if key == b'w':
            new_pos[0] += math.cos(rad) * self.speed
            new_pos[2] += math.sin(rad) * self.speed
        if key == b's':
            new_pos[0] -= math.cos(rad) * self.speed
            new_pos[2] -= math.sin(rad) * self.speed
        if key == b'a':
            new_pos[0] += math.sin(rad) * self.speed
            new_pos[2] -= math.cos(rad) * self.speed
        if key == b'd':
            new_pos[0] -= math.sin(rad) * self.speed
            new_pos[2] += math.cos(rad) * self.speed
            
        if key == b'q': new_pos[1] += self.speed # Ascend
        if key == b'e': new_pos[1] -= self.speed # Descend

        self.try_move(new_pos, world)

    def apply_view(self):
        self.update_vectors()
        gluLookAt(self.pos[0], self.pos[1], self.pos[2],
                  self.pos[0] + self.look_dir[0], 
                  self.pos[1] + self.look_dir[1], 
                  self.pos[2] + self.look_dir[2],
                  0, 1, 0)

BG_COLOR = [0.294, 0.616, 0.663]

BLOCK_TYPES = {
    1: ((0.8, 0.2, 0.2), 1),  # demo red block
    2: ((0.2, 0.8, 0.2), 2),  # demo green block
    3: ((0.2, 0.2, 0.8), 4),  # demo blue block
    10: ((0.85, 0.75, 0.55), 1),  # sand base
    11: ((0.4, 0.4, 0.45), 2),    # rock
    12: ((1.0, 0.4, 0.6), 2),     # coral pink
    13: ((1.0, 0.9, 0.3), 2),     # coral yellow
    14: ((0.3, 0.6, 1.0), 2),     # coral blue
    15: ((0.8, 0.3, 0.9), 2),     # coral purple
    16: ((0.1, 0.6, 0.2), 3),     # seaweed green
}

MAP_SIZE = 80
MAX_HEIGHT = 15  # Maximum Y the player can reach
MIN_HEIGHT = 0.5 # Minimum Y to stay above the floor

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

LIGHT_AMBIENT = 0.55
LIGHT_DEPTH_DARKEN = 0.02
CAUSTICS_SCALE = 0.25
CAUSTICS_SPEED = 0.4
CAUSTICS_INTENSITY = 0.35

CORAL_REEF_MIN_SIZE = 20
CORAL_REEF_MAX_SIZE = 30

SEAWEED_SEG_LEN = 1.8
SEAWEED_SWAY_AMP = 0.25

CAVE_DARKEN = 0.5

PHONG_ON = False
PHONG_LIGHT_DIR = (0.6, 0.8, 0.2)
PHONG_AMB = 0.3
PHONG_DIFF = 0.7
PHONG_SPEC = 0.15
PHONG_SHININESS = 8.0
MINIMAP_CELL = 4
MINIMAP_VIEW_SIZE = 40
MINIMAP_MARGIN = 10
USE_DYNAMIC_MINIMAP = True
USE_VIEW_CULLING = True
DRAW_RADIUS = 50
USE_MULTITHREADING = False
GPU_BACKFACE_CULL = True

from OpenGL.GL import *
from OpenGL.GLUT import *

class FirstPersonView:
    """Handles the first-person camera and arm rendering."""
    
    def draw(self):
        """Draw camera model in first person view (blocky hand holding camera)."""
        glPushMatrix()
        
        # Position in bottom-right corner of view (camera shifted left of hand)
        glTranslatef(0.5, -0.35, -1.5)  # Hand stays in place
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
        
        # Camera body (main rectangular body)
        glPushMatrix()
        glTranslatef(-0.1, 0.02, 0.0)  # Shifted left from hand
        
        # Main camera body
        glColor3f(0.35, 0.35, 0.4)
        glScalef(0.65, 0.45, 0.5)
        glutSolidCube(0.35)
        glPopMatrix()
        
        # Top section (viewfinder hump)
        glPushMatrix()
        glTranslatef(-0.12, 0.1, 0.0)  # Shifted left
        glColor3f(0.3, 0.3, 0.35)
        glScalef(0.5, 0.25, 0.42)
        glutSolidCube(0.3)
        glPopMatrix()
        
        # Lens housing (protruding section)
        glPushMatrix()
        glTranslatef(-0.02, 0.02, 0.0)  # Shifted left
        glColor3f(0.25, 0.25, 0.3)
        glScalef(0.35, 0.35, 0.35)
        glutSolidCube(0.35)
        glPopMatrix()
        
        # Lens glass (dark cube instead of sphere)
        glPushMatrix()
        glTranslatef(0.04, 0.02, 0.0)  # Shifted left
        glColor3f(0.05, 0.05, 0.1)
        glScalef(0.13, 0.13, 0.13)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Lens rim (metallic cube frame instead of torus)
        glPushMatrix()
        glTranslatef(0.04, 0.02, 0.0)  # Shifted left
        glColor3f(0.7, 0.7, 0.75)
        glScalef(0.15, 0.15, 0.08)
        glutWireCube(1.0)
        glPopMatrix()
        
        # Shutter button (red cube instead of cylinder)
        glPushMatrix()
        glTranslatef(-0.13, 0.12, 0.05)  # Shifted left
        glColor3f(0.9, 0.2, 0.15)
        glScalef(0.03, 0.03, 0.03)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Flash (small silver rectangle)
        glPushMatrix()
        glTranslatef(-0.07, 0.1, 0.07)  # Shifted left
        glColor3f(0.9, 0.9, 0.95)
        glScalef(0.2, 0.15, 0.15)
        glutSolidCube(0.15)
        glPopMatrix()
        
        # Grip texture (small dark rectangle on front)
        glPushMatrix()
        glTranslatef(-0.17, 0.0, 0.09)  # Shifted left
        glColor3f(0.15, 0.15, 0.2)
        glScalef(0.3, 0.35, 0.08)
        glutSolidCube(0.25)
        glPopMatrix()
        
        glPopMatrix()

# ====== Health System Module ======
# This module manages:
#   - Health level tracking (0-100%)
#   - Health depletion when oxygen is low
#   - UI rendering for health bar
# ===================================

from OpenGL.GL import *
from OpenGL.GLUT import *


class HealthSystem:
    """
    Manages health level that depletes when oxygen falls below 15%.
    Health decreases at a constant rate when triggered.
    """
    
    def __init__(self):
        """Initialize health system at full capacity."""
        self.level = 100.0  # Current health percentage (0-100)
        self.depletion_rate = 2.5  # Health points lost per second when oxygen is low
        self.is_dead = False  # Track death state
        
        # UI properties
        self.bar_x = 20
        self.bar_y = 610  # Below oxygen bar
        self.bar_width = 220
        self.bar_height = 35
    
    
    def update(self, delta_time, is_oxygen_critical):
        """
        Update health level based on oxygen status.
        
        Args:
            delta_time: Time elapsed since last update in seconds
            is_oxygen_critical: Boolean indicating if oxygen is below 15%
        """
        if is_oxygen_critical and self.level > 0:
            self.level -= self.depletion_rate * delta_time
            self.level = max(0.0, self.level)  # Clamp to 0
    
    
    def is_depleted(self):
        """
        Check if health is completely depleted (game over condition).
        
        Returns:
            bool: True if health level is 0
        """
        if self.level <= 0.0:
            self.is_dead = True
            return True
        return False
    
    
    def is_critical(self):
        """
        Check if health is at critical level (below 30%).
        
        Returns:
            bool: True if health is below 30%
        """
        return self.level < 30.0
    
    
    def draw_bar(self, window_width, window_height):
        """
        Draw health bar with gradient, shadow, and effects.
        Minecraft-inspired blocky style with color-coded health levels.
        
        Args:
            window_width: Window width for 2D projection
            window_height: Window height for 2D projection
        """



        # Set up 2D orthographic projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        from OpenGL.GLU import gluOrtho2D
        gluOrtho2D(0, window_width, 0, window_height)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # === Draw shadow ===
        glColor3f(0, 0, 0)
        glBegin(GL_QUADS)
        glVertex2f(self.bar_x + 4, self.bar_y - 4)
        glVertex2f(self.bar_x + self.bar_width + 4, self.bar_y - 4)
        glVertex2f(self.bar_x + self.bar_width + 4, self.bar_y + self.bar_height - 4)
        glVertex2f(self.bar_x + 4, self.bar_y + self.bar_height - 4)
        glEnd()
        
        # === Draw background (empty bar) ===
        glBegin(GL_QUADS)
        # Gradient from dark to slightly lighter
        glColor3f(0.08, 0.12, 0.18)
        glVertex2f(self.bar_x, self.bar_y)
        glVertex2f(self.bar_x + self.bar_width, self.bar_y)
        glColor3f(0.12, 0.16, 0.22)
        glVertex2f(self.bar_x + self.bar_width, self.bar_y + self.bar_height)
        glVertex2f(self.bar_x, self.bar_y + self.bar_height)
        glEnd()
        
        # === Draw filled portion (health) ===
        filled_width = self.bar_width * (self.level / 100.0)
        
        if filled_width > 0:
            # Color changes based on health level
            if self.level > 70:
                # High health - bright green
                color_bottom = (0.0, 0.85, 0.15)
                color_top = (0.3, 1.0, 0.4)
            elif self.level > 30:
                # Medium health - yellow/orange
                color_bottom = (0.95, 0.75, 0.0)
                color_top = (1.0, 0.9, 0.3)
            else:
                # Critical health - red
                color_bottom = (0.9, 0.1, 0.0)
                color_top = (1.0, 0.3, 0.2)
            
            glBegin(GL_QUADS)
            # Bottom gradient
            glColor3f(*color_bottom)
            glVertex2f(self.bar_x, self.bar_y)
            glVertex2f(self.bar_x + filled_width, self.bar_y)
            # Top gradient
            glColor3f(*color_top)
            glVertex2f(self.bar_x + filled_width, self.bar_y + self.bar_height)
            glVertex2f(self.bar_x, self.bar_y + self.bar_height)
            glEnd()
            
            # === Add shine highlight ===
            glBegin(GL_QUADS)
            glColor3f(0.32, 0.32, 0.32)
            glVertex2f(self.bar_x, self.bar_y + self.bar_height * 0.65)
            glVertex2f(self.bar_x + filled_width, self.bar_y + self.bar_height * 0.65)
            glColor3f(1, 1, 1)  # Changed from glColor4f for compliance
            glVertex2f(self.bar_x + filled_width, self.bar_y + self.bar_height)
            glVertex2f(self.bar_x, self.bar_y + self.bar_height)
            glEnd()
        
        # === Draw border ===
        glColor3f(0.85, 0.92, 1.0)
        glLineWidth(4)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.bar_x, self.bar_y)
        glVertex2f(self.bar_x + self.bar_width, self.bar_y)
        glVertex2f(self.bar_x + self.bar_width, self.bar_y + self.bar_height)
        glVertex2f(self.bar_x, self.bar_y + self.bar_height)
        glEnd()
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        # Restore GL state
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
    
    
    def draw_text(self, window_width, window_height):
        """
        Draw health percentage text with shadow.
        
        Args:
            window_width: Window width for 2D projection
            window_height: Window height for 2D projection
        """
        # Disable depth testing so UI text draws on top
        glDisable(GL_DEPTH_TEST)
       

        # Set up 2D projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        from OpenGL.GLU import gluOrtho2D
        gluOrtho2D(0, window_width, 0, window_height)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        text = f"HP: {int(self.level)}%"
        text_x = self.bar_x + 8
        text_y = self.bar_y + 15
        
        # Draw shadow
        glColor3f(0, 0, 0)
        glRasterPos2f(text_x + 2, text_y - 2)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Draw main text
        glColor3f(1, 1, 1)
        glRasterPos2f(text_x, text_y)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        # Restore GL state
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
    
    
    def render(self, window_width=1000, window_height=800):
        """
        Main render method for health UI.
        Draws bar and text overlay.
        
        Args:
            window_width: Window width (default 1000)
            window_height: Window height (default 800)
        """
        self.draw_bar(window_width, window_height)
        self.draw_text(window_width, window_height)
    
    
    def reset(self):
        """
        Reset health system to initial state.
        """
        self.level = 100.0
        self.is_dead = False
    
    
    def draw_death_screen(self, window_width, window_height):
        """
        Draw death screen overlay with huge red text.
        
        Args:
            window_width: Window width for 2D projection
            window_height: Window height for 2D projection
        """
        # Set up 2D orthographic projection for overlay
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        from OpenGL.GLU import gluOrtho2D
        gluOrtho2D(0, window_width, 0, window_height)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw semi-transparent dark overlay
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(window_width, 0)
        glVertex2f(window_width, window_height)
        glVertex2f(0, window_height)
        glEnd()
        
        # Draw huge red "YOU HAVE DIED" text
        death_text = "YOU HAVE DIED"
        restart_text = "Press '1' to Restart"
        
        # Calculate text position (centered)
        text_x = window_width // 2 - 180
        text_y = window_height // 2 + 20
        restart_x = window_width // 2 - 110
        restart_y = window_height // 2 - 40
        
        # Draw death text shadow (multiple layers for huge effect)
        for offset in range(8, 0, -2):
            darkness = 1.0 - (offset / 10.0)
            glColor3f(darkness * 0.3, 0.0, 0.0)
            glRasterPos2f(text_x + offset, text_y - offset)
            for char in death_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Draw main death text (bright red)
        glColor3f(1.0, 0.0, 0.0)
        glRasterPos2f(text_x, text_y)
        for char in death_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Draw another layer for extra thickness
        glRasterPos2f(text_x + 1, text_y)
        for char in death_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        glRasterPos2f(text_x, text_y + 1)
        for char in death_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        glRasterPos2f(text_x + 1, text_y + 1)
        for char in death_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Draw restart instruction
        glColor3f(0.8, 0.8, 0.8)
        glRasterPos2f(restart_x + 1, restart_y - 1)
        for char in restart_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        glColor3f(1.0, 1.0, 1.0)
        glRasterPos2f(restart_x, restart_y)
        for char in restart_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)


from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D
import config
import math
import random
import time
from orangered_fish import OrangeRedFish
from blueblack_fish import BlueBlackFish
from pink_fish import PinkFish
from yellowgray_fish import YellowGrayFish

class Seaweed:
    def __init__(self, x, z, base_y, color=None):
        self.x = x + 0.5
        self.z = z + 0.5
        self.base_y = base_y  # Start at ground level (no +0.5 offset)
        # Random green color selection
        if color is None:
            green_colors = [
                (0.1, 0.6, 0.2),    # Green
                (0.05, 0.4, 0.1),   # Dark green
                (0.03, 0.3, 0.08)   # Darker green
            ]
            self.color = random.choice(green_colors)
        else:
            self.color = color
        self.phase = random.uniform(0, 6.28318)
        self.amp = config.SEAWEED_SWAY_AMP
        self.width = 0.15
        self.seg_len = config.SEAWEED_SEG_LEN

    def draw(self, t, cam):
        sway = math.sin(t + self.phase) * self.amp
        glPushMatrix()
        glTranslatef(self.x + sway, self.base_y + self.seg_len * 0.5, self.z)
        glColor3f(*self.color)
        glScalef(self.width, self.seg_len, self.width)
        glutSolidCube(1.0)
        glPopMatrix()

        # Draw 2D flat leaves (Cluster of leaves)
        self._draw_leaves(self.x + sway, self.base_y + self.seg_len * 0.5, self.z, 0)

        sway_top = math.sin(t + self.phase + 0.8) * (self.amp * 1.3)
        glPushMatrix()
        glTranslatef(self.x + sway_top, self.base_y + self.seg_len * 1.5, self.z)
        glColor3f(*self.color)
        glScalef(self.width, self.seg_len, self.width)
        glutSolidCube(1.0)
        glPopMatrix()

        # Draw leaves for top segment
        self._draw_leaves(self.x + sway_top, self.base_y + self.seg_len * 1.5, self.z, 1)

        if self._contains(cam.pos, sway, sway_top):
            cam.visible = False

    def _draw_leaves(self, x, y, z, level):
        # Draw many 2D flat leaves (rectangles) radially around the weed
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(self.color[0]*0.9, self.color[1]*1.1, self.color[2]*0.9) # Slightly different color
        
        # Draw multiple layers of leaves to make it dense
        # 3 layers vertically, more leaves around per layer for better radial distribution
        num_layers = 3
        leaves_per_layer = 8  # Increased from 4 to 8 for better radial coverage
        
        for l in range(num_layers):
            layer_y = (l - 1) * 0.2 # Spread vertically around the center
            
            for i in range(leaves_per_layer):
                glPushMatrix()
                # Rotate around Y axis to distribute leaves radially
                angle = i * (360.0 / leaves_per_layer) + (l * 15.0) # Offset layers rotation
                glRotatef(angle, 0, 1, 0)
                glTranslatef(0, layer_y, 0)
                
                # Draw leaf as a long rectangle extending outward radially
                glBegin(GL_QUADS)
                # Leaf shape - longer and thinner rectangles
                leaf_len = 0.35 + (level * 0.1)
                leaf_w = 0.08
                
                # Draw leaf extending outward from the center
                glVertex3f(0.02, -leaf_w/2, 0)
                glVertex3f(leaf_len, -leaf_w/2, 0)
                glVertex3f(leaf_len, leaf_w/2, 0)
                glVertex3f(0.02, leaf_w/2, 0)
                glEnd()
                glPopMatrix()
        glPopMatrix()

    def _contains(self, pos, sway, sway_top):
        px, py, pz = pos
        half = self.width * 0.5
        # Bottom segment AABB
        x0 = (self.x + sway) - half
        x1 = (self.x + sway) + half
        y0 = self.base_y
        y1 = self.base_y + self.seg_len
        z0 = self.z - half
        z1 = self.z + half
        in_bottom = (x0 <= px <= x1) and (y0 <= py <= y1) and (z0 <= pz <= z1)
        # Top segment AABB
        x0t = (self.x + sway_top) - half
        x1t = (self.x + sway_top) + half
        y0t = self.base_y + self.seg_len
        y1t = self.base_y + self.seg_len * 2.0
        in_top = (x0t <= px <= x1t) and (y0t <= py <= y1t) and (z0 <= pz <= z1)
        return in_bottom or in_top

class MapManager:
    def __init__(self):
        self.blocks = {}
        self.bubbles = []
        self.last_time = time.time()
        self._noise_perm = self._build_perm()
        self.height_map = {}
        self.seaweeds = []
        self.coral_rects = []
        self.coral_reefs = []
        self.orangered_fish_school = []
        self.blueblack_school = []
        self.pink_fish_school = []
        self.yellowgray_fish_school = []
        self.generate_world()

    def add_block(self, x, y, z, block_id):
        self.blocks[(int(x), int(y), int(z))] = block_id

    def generate_world(self):
        scale = 0.12
        amp = 3
        coral_threshold = 0.55
        rock_threshold = 0.4
        weed_threshold = 0.4  # Lowered from 0.5 to create more seaweed clusters
        for x in range(config.MAP_SIZE):
            for z in range(config.MAP_SIZE):
                n = self._perlin2d(x * scale, z * scale)
                h = max(1, int(1 + amp * (n * 0.5 + 0.5)))
                for y in range(h):
                    self.add_block(x, y, z, 10)
                top_y = h
                self.height_map[(x, z)] = top_y
                n2 = self._perlin2d(x * scale * 1.7 + 100.0, z * scale * 1.7 + 100.0)
                if n2 > coral_threshold and top_y + 2 < config.MAX_HEIGHT:
                    coral_ids = [12, 13, 14, 15]
                    c_id = random.choice(coral_ids)
                    self.add_block(x, top_y, z, c_id)
                    self.add_block(x, top_y + 1, z, c_id)
                elif n2 > rock_threshold:
                    self.add_block(x, top_y, z, 11)
                n3 = self._perlin2d(x * scale * 2.1 + 200.0, z * scale * 2.1 + 200.0)
                if n3 > weed_threshold and top_y + 3 < config.MAX_HEIGHT:
                    # Create main seaweed
                    self.seaweeds.append(Seaweed(x, z, top_y))
                    # Add cluster of nearby seaweed for denser patches
                    if random.random() < 0.6:  # 60% chance of cluster
                        for _ in range(random.randint(2, 4)):  # Add 2-4 more seaweed nearby
                            dx = random.randint(-1, 1)
                            dz = random.randint(-1, 1)
                            nx, nz = x + dx, z + dz
                            if 0 <= nx < config.MAP_SIZE and 0 <= nz < config.MAP_SIZE:
                                cluster_y = self.height_map.get((nx, nz), top_y)
                                if cluster_y + 3 < config.MAX_HEIGHT:
                                    self.seaweeds.append(Seaweed(nx, nz, cluster_y))

        reef_w = min(config.CORAL_REEF_MAX_SIZE, config.MAP_SIZE)
        reef_d = min(config.CORAL_REEF_MAX_SIZE, config.MAP_SIZE)
        reef_w = max(config.CORAL_REEF_MIN_SIZE, reef_w)
        reef_d = max(config.CORAL_REEF_MIN_SIZE, reef_d)
        reef_x0 = max(0, (config.MAP_SIZE - reef_w) // 2)
        reef_z0 = max(0, (config.MAP_SIZE - reef_d) // 2)
        self.coral_reefs.append((reef_x0, reef_z0, reef_w, reef_d))
        scale_r = 0.18
        for x in range(reef_x0, reef_x0 + reef_w):
            for z in range(reef_z0, reef_z0 + reef_d):
                nx = (x - reef_x0) / max(1.0, reef_w)
                nz = (z - reef_z0) / max(1.0, reef_d)
                dx = nx - 0.5
                dz = nz - 0.5
                ring = 1.0 - min(1.0, math.sqrt(dx*dx + dz*dz) * 1.4)
                mask = self._perlin2d(x * scale_r + 350.0, z * scale_r + 350.0) * 0.6 + ring * 0.4
                if mask <= 0.35:
                    continue
                top_y = self.height_map.get((x, z), 1)
                coral_ids = [12, 13, 14, 15]
                c_id = random.choice(coral_ids)
                if top_y + 2 < config.MAX_HEIGHT:
                    self.add_block(x, top_y, z, c_id)
                    if random.random() < 0.7:
                        self.add_block(x, top_y + 1, z, c_id)
                for k in range(random.randint(1, 4)):
                    ox = (random.random() - 0.5) * 0.6
                    oz = (random.random() - 0.5) * 0.6
                    height = random.uniform(0.6, 1.4)
                    width = random.uniform(0.08, 0.12)
                    color = config.BLOCK_TYPES[c_id][0]
                    self.coral_rects.append((x + 0.5 + ox, top_y + 0.5, z + 0.5 + oz, width, height, color))

        patch_min = 7
        patch_w = 8
        patch_d = 8
        px0 = max(0, config.MAP_SIZE - patch_w)
        pz0 = max(0, config.MAP_SIZE - patch_d)
        count = 0
        for x in range(px0, px0 + patch_w):
            for z in range(pz0, pz0 + patch_d):
                top_y = self.height_map.get((x, z), 1)
                self.seaweeds.append(Seaweed(x, z, top_y))
                count += 1
                if count >= patch_min:
                    pass
        
        num_orangered_fish = 35
        for i in range(num_orangered_fish):
            fish_x = random.randint(10, config.MAP_SIZE - 10)
            fish_z = random.randint(10, config.MAP_SIZE - 10)
            fish_y = self.height_map.get((fish_x, fish_z), 1) + random.uniform(3.5, 5.5)
            self.orangered_fish_school.append(OrangeRedFish(fish_x, fish_z, fish_y))
        print(f"Spawned {num_orangered_fish} orange red fish across the ocean")
        
        num_blueblack_fish = 35
        for i in range(num_blueblack_fish):
            fish_x = random.randint(10, config.MAP_SIZE - 10)
            fish_z = random.randint(10, config.MAP_SIZE - 10)
            fish_y = self.height_map.get((fish_x, fish_z), 1) + random.uniform(4.0, 6.0)
            self.blueblack_school.append(BlueBlackFish(fish_x, fish_z, fish_y))
        print(f"Spawned {num_blueblack_fish} blue black fish across the ocean")
        
        num_pink_fish = 35
        for i in range(num_pink_fish):
            fish_x = random.randint(10, config.MAP_SIZE - 10)
            fish_z = random.randint(10, config.MAP_SIZE - 10)
            fish_y = self.height_map.get((fish_x, fish_z), 1) + random.uniform(4.5, 7.0)
            self.pink_fish_school.append(PinkFish(fish_x, fish_z, fish_y))
        print(f"Spawned {num_pink_fish} pink fish across the ocean")
        
        num_yellowgray_fish = 35
        for i in range(num_yellowgray_fish):
            fish_x = random.randint(10, config.MAP_SIZE - 10)
            fish_z = random.randint(10, config.MAP_SIZE - 10)
            fish_y = self.height_map.get((fish_x, fish_z), 1) + random.uniform(3.0, 5.5)
            self.yellowgray_fish_school.append(YellowGrayFish(fish_x, fish_z, fish_y))
        print(f"Spawned {num_yellowgray_fish} yellow gray fish across the ocean")
        
        self._generate_caves()

    def is_occupied(self, x, y, z):
        return (int(x), int(y), int(z)) in self.blocks

    def draw(self, cam):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        t = now
        cam.visible = True
        if config.USE_VIEW_CULLING:
            px = int(cam.pos[0]); pz = int(cam.pos[2])
            r = config.DRAW_RADIUS; r2 = r * r
            def in_range(x, z):
                dx = x - px; dz = z - pz
                return dx*dx + dz*dz <= r2
        else:
            def in_range(x, z): return True
        for (x, y, z), b_id in self.blocks.items():
            if not in_range(x, z): 
                continue
            color, _ = config.BLOCK_TYPES[b_id]
            lx = self._lighting_factor(x, y, z)
            cx = self._caustics(x, z, t) if y <= 1 else 1.0
            if config.PHONG_ON and y == self.height_map.get((x, z), y):
                pf = self._phong_factor(x, y, z, cam)
                lx *= pf
            r = max(0.0, min(1.0, color[0] * lx * cx))
            g = max(0.0, min(1.0, color[1] * lx * cx))
            b = max(0.0, min(1.0, color[2] * lx * cx))
            glPushMatrix()
            glTranslatef(x + 0.5, y + 0.5, z + 0.5)
            glColor3f(r, g, b)
            glutSolidCube(1.0)
            glPopMatrix()
        for cx, cy, cz, w, h, col in self.coral_rects:
            if not in_range(int(cx), int(cz)):
                continue
            glPushMatrix()
            glTranslatef(cx, cy + h * 0.5, cz)
            glColor3f(*col)
            glScalef(w, h, w)
            glutSolidCube(1.0)
            glPopMatrix()
        for sw in self.seaweeds:
            if not in_range(int(sw.x), int(sw.z)):
                continue
            sw.draw(t, cam)
        
        for fish in self.orangered_fish_school:
            fish.update(t)
            if in_range(int(fish.x), int(fish.z)):
                fish.draw()
        
        for fish in self.blueblack_school:
            fish.update(t)
            if in_range(int(fish.x), int(fish.z)):
                fish.draw()
        
        for fish in self.pink_fish_school:
            fish.update(t)
            if in_range(int(fish.x), int(fish.z)):
                fish.draw()
        
        for fish in self.yellowgray_fish_school:
            fish.update(t)
            if in_range(int(fish.x), int(fish.z)):
                fish.draw()
        
        self._update_bubbles(dt)
        self._draw_bubbles()

    def draw_minimap(self, cam=None):
        cell = config.MINIMAP_CELL
        if cam is not None and config.USE_DYNAMIC_MINIMAP:
            px = max(0, min(config.MAP_SIZE - 1, int(cam.pos[0])))
            pz = max(0, min(config.MAP_SIZE - 1, int(cam.pos[2])))
            half = config.MINIMAP_VIEW_SIZE // 2
            x_start = max(0, px - half)
            z_start = max(0, pz - half)
            x_end = min(config.MAP_SIZE, x_start + config.MINIMAP_VIEW_SIZE)
            z_end = min(config.MAP_SIZE, z_start + config.MINIMAP_VIEW_SIZE)
            x_start = max(0, x_end - config.MINIMAP_VIEW_SIZE)
            z_start = max(0, z_end - config.MINIMAP_VIEW_SIZE)
            view_w = (x_end - x_start) * cell
            view_h = (z_end - z_start) * cell
        else:
            x_start = 0
            z_start = 0
            x_end = config.MAP_SIZE
            z_end = config.MAP_SIZE
            view_w = (x_end - x_start) * cell
            view_h = (z_end - z_start) * cell
        margin = config.MINIMAP_MARGIN
        origin_x = config.WINDOW_WIDTH - view_w - margin
        origin_y = config.WINDOW_HEIGHT - view_h - margin
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, config.WINDOW_WIDTH, 0, config.WINDOW_HEIGHT)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glBegin(GL_QUADS)
        for x in range(x_start, x_end):
            for z in range(z_start, z_end):
                top_id = self._top_block_id(x, z)
                color = config.BLOCK_TYPES[top_id][0] if top_id in config.BLOCK_TYPES else (1.0, 1.0, 1.0)
                glColor3f(*color)
                x0 = origin_x + (x - x_start) * cell
                y0 = origin_y + (z - z_start) * cell
                x1 = x0 + cell
                y1 = y0 + cell
                glVertex2f(x0, y0)
                glVertex2f(x1, y0)
                glVertex2f(x1, y1)
                glVertex2f(x0, y1)
        glEnd()
        if cam is not None:
            px = max(0, min(config.MAP_SIZE - 1, int(cam.pos[0])))
            pz = max(0, min(config.MAP_SIZE - 1, int(cam.pos[2])))
            cx = origin_x + (px - x_start) * cell + cell * 0.5
            cy = origin_y + (pz - z_start) * cell + cell * 0.5
            r = cell * 0.45
            ang = -math.radians(cam.yaw)
            tx = 0.0; ty = r
            lx = -r * 0.4; ly = -r * 0.5
            rx = r * 0.4; ry = -r * 0.5
            cosA = math.cos(ang); sinA = math.sin(ang)
            def rot(px_, py_):
                return (cx + px_ * cosA - py_ * sinA, cy + px_ * sinA + py_ * cosA)
            p1 = rot(tx, ty)
            p2 = rot(lx, ly)
            p3 = rot(rx, ry)
            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_TRIANGLES)
            glVertex2f(p1[0], p1[1])
            glVertex2f(p2[0], p2[1])
            glVertex2f(p3[0], p3[1])
            glEnd()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def get_spawn_position(self):
        for x in range(1, config.MAP_SIZE - 1):
            for z in range(1, config.MAP_SIZE - 1):
                top_id = self._top_block_id(x, z)
                if top_id == 10:
                    top_y = self.height_map.get((x, z), 1)
                    if not self._has_obstacle_near(x, z, 2):
                        return [x + 0.5, top_y + 2.0, z + 0.5]
        return [1.5, 2.0, 1.5]

    def create_random_structure(self, origin_x, origin_z, width, depth, max_height, palette_ids):
        for dx in range(width):
            for dz in range(depth):
                h = random.randint(1, max_height)
                b_id = random.choice(palette_ids)
                for y in range(h):
                    if origin_x + dx < config.MAP_SIZE and origin_z + dz < config.MAP_SIZE:
                        self.add_block(origin_x + dx, y, origin_z + dz, b_id)

    def _update_bubbles(self, dt):
        spawn_rate = 0.6
        if random.random() < spawn_rate * dt:
            x = random.randint(0, config.MAP_SIZE - 1) + 0.5
            z = random.randint(0, config.MAP_SIZE - 1) + 0.5
            y = 0.2
            speed = random.uniform(0.5, 1.2)
            radius = random.uniform(0.05, 0.12)
            self.bubbles.append([x, y, z, speed, radius])
        for b in self.bubbles:
            b[1] += b[3] * dt
        self.bubbles = [b for b in self.bubbles if b[1] < config.MAX_HEIGHT]

    def _draw_bubbles(self):
        for x, y, z, _, r in self.bubbles:
            glPushMatrix()
            glTranslatef(x, y, z)
            glColor3f(0.9, 0.95, 1.0)
            glutSolidSphere(r, 12, 12)
            glPopMatrix()

    def _lighting_factor(self, x, y, z):
        base = config.LIGHT_AMBIENT + (y * config.LIGHT_DEPTH_DARKEN)
        if self._is_cave_shadow(x, y, z):
            base *= config.CAVE_DARKEN
        return max(0.1, min(1.0, base))

    def _caustics(self, x, z, t):
        s = config.CAUSTICS_SCALE
        sp = config.CAUSTICS_SPEED
        v = self._perlin2d(x * s + t * sp, z * s + t * sp)
        return 1.0 + config.CAUSTICS_INTENSITY * v

    def _phong_factor(self, x, y, z, cam):
        hx0 = self.height_map.get((max(0, x - 1), z), y)
        hx1 = self.height_map.get((min(config.MAP_SIZE - 1, x + 1), z), y)
        hz0 = self.height_map.get((x, max(0, z - 1)), y)
        hz1 = self.height_map.get((x, min(config.MAP_SIZE - 1, z + 1)), y)
        dx = hx1 - hx0
        dz = hz1 - hz0
        nx, ny, nz = (-dx, 2.0, -dz)
        ldx, ldy, ldz = config.PHONG_LIGHT_DIR
        # normalize n and l
        nlen = max(1e-6, math.sqrt(nx*nx + ny*ny + nz*nz))
        nx /= nlen; ny /= nlen; nz /= nlen
        llen = max(1e-6, math.sqrt(ldx*ldx + ldy*ldy + ldz*ldz))
        ldx /= llen; ldy /= llen; ldz /= llen
        ndotl = max(0.0, nx*ldx + ny*ldy + nz*ldz)
        diffuse = config.PHONG_DIFF * ndotl
        spec = config.PHONG_SPEC * (ndotl ** config.PHONG_SHININESS)
        return config.PHONG_AMB + diffuse + spec

    def _is_cave_shadow(self, x, y, z):
        for dy in range(1, 3):
            if self.is_occupied(x, y + dy, z):
                return True
        return False

    def _has_obstacle_near(self, x, z, r):
        for dx in range(-r, r+1):
            for dz in range(-r, r+1):
                xx = x + dx; zz = z + dz
                if not (0 <= xx < config.MAP_SIZE and 0 <= zz < config.MAP_SIZE): 
                    continue
                top_id = self._top_block_id(xx, zz)
                if top_id != 10:
                    return True
        return False

    def _generate_caves(self):
        scale = 0.35
        for x in range(config.MAP_SIZE):
            for z in range(config.MAP_SIZE):
                top = self.height_map.get((x, z), 1)
                c = self._perlin2d(x * scale + 300.0, z * scale + 300.0)
                if c > 0.6 and top > 3:
                    h = random.randint(2, 4)
                    start_y = random.randint(1, max(1, top - h))
                    for y in range(start_y, min(top, start_y + h)):
                        key = (x, y, z)
                        if key in self.blocks:
                            del self.blocks[key]
    def _top_block_id(self, x, z):
        top = self.height_map.get((x, z), 1)
        for y in range(min(config.MAX_HEIGHT, top + 3), -1, -1):
            bid = self.blocks.get((x, y, z))
            if bid is not None:
                return bid
        return 10

    def _build_perm(self):
        p = list(range(256))
        random.shuffle(p)
        p = p + p
        return p

    def _fade(self, t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a, b, t):
        return a + t * (b - a)

    def _grad(self, hash_, x, y):
        h = hash_ & 3
        u = x if h < 2 else y
        v = y if h < 2 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

    def _perlin2d(self, x, y):
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        u = self._fade(xf)
        v = self._fade(yf)
        aa = self._noise_perm[xi] + yi
        ab = self._noise_perm[xi] + yi + 1
        ba = self._noise_perm[xi + 1] + yi
        bb = self._noise_perm[xi + 1] + yi + 1
        x1 = self._lerp(self._grad(self._noise_perm[aa], xf, yf),
                        self._grad(self._noise_perm[ba], xf - 1, yf), u)
        x2 = self._lerp(self._grad(self._noise_perm[ab], xf, yf - 1),
                        self._grad(self._noise_perm[bb], xf - 1, yf - 1), u)
        return self._lerp(x1, x2, v)

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random

class OrangeRedFish:
    def __init__(self, x, z, y):
        self.base_x = x
        self.base_z = z
        self.base_y = y
        self.wander_radius = random.uniform(5.0, 10.0)
        self.phase = random.uniform(0, 6.28318)
        self.speed = random.uniform(0.5, 1.0)
        self.vertical_speed = random.uniform(0.2, 0.4)
        self.size = random.uniform(0.3, 0.5)
        if random.random() < 0.5:
            self.body_color = (1.0, 0.3, 0.0)
        else:
            self.body_color = (0.9, 0.1, 0.1)
        self.spot_color = (1.0, 1.0, 1.0)
        self.angle = 0.0
        self.x = x
        self.y = y
        self.z = z
        self.prev_x = x
        self.prev_z = z

    def update(self, t):
        # Store previous position
        self.prev_x = self.x
        self.prev_z = self.z
        
        circle_x = math.cos(t * self.speed * 0.3 + self.phase) * self.wander_radius
        circle_z = math.sin(t * self.speed * 0.3 + self.phase) * self.wander_radius
        swim_offset_x = math.sin(t * self.speed + self.phase) * 2.0
        swim_offset_z = math.cos(t * self.speed * 0.7 + self.phase) * 2.0
        self.x = self.base_x + circle_x + swim_offset_x
        self.z = self.base_z + circle_z + swim_offset_z
        self.y = self.base_y + math.sin(t * self.vertical_speed + self.phase) * 1.5
        
        # Calculate direction from actual movement
        dx = self.x - self.prev_x
        dz = self.z - self.prev_z
        
        # Only update angle if fish is actually moving
        if abs(dx) > 0.001 or abs(dz) > 0.001:
            self.angle = math.atan2(dz, dx)

    def draw(self):
        # Main body
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glColor3f(*self.body_color)
        glScalef(self.size * 1.5, self.size * 0.8, self.size * 0.8)
        glutSolidSphere(1.0, 12, 12)
        glPopMatrix()
        
        # Tail section
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.2, 0, 0)
        glColor3f(*self.body_color)
        glScalef(self.size * 0.6, self.size * 0.5, self.size * 0.5)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Tail fin - BIGGER
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.7, 0, 0)
        glColor3f(1.0, 0.5, 0.1)
        glScalef(self.size * 0.3, self.size * 1.5, self.size * 0.1)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Dorsal fin (top) - BIGGER
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(0, self.size * 0.9, 0)
        glColor3f(1.0, 0.5, 0.1)
        glScalef(self.size * 1.2, self.size * 0.7, self.size * 0.08)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Left pectoral fin - BIGGER
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.3, -self.size * 0.2, self.size * 0.7)
        glRotatef(45, 1, 0, 0)
        glColor3f(1.0, 0.5, 0.1)
        glScalef(self.size * 0.15, self.size * 1.0, self.size * 0.08)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Right pectoral fin - BIGGER
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.3, -self.size * 0.2, -self.size * 0.7)
        glRotatef(-45, 1, 0, 0)
        glColor3f(1.0, 0.5, 0.1)
        glScalef(self.size * 0.15, self.size * 1.0, self.size * 0.08)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Left eye
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.9, self.size * 0.3, self.size * 0.4)
        glColor3f(0.0, 0.0, 0.0)
        glutSolidSphere(self.size * 0.12, 8, 8)
        glPopMatrix()
        
        # Right eye
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.9, self.size * 0.3, -self.size * 0.4)
        glColor3f(0.0, 0.0, 0.0)
        glutSolidSphere(self.size * 0.12, 8, 8)
        glPopMatrix()

# ====== Oxygen System Module ======
# This module manages:
#   - Oxygen level tracking (0-100%)
#   - Time-based depletion (3 minutes when moving)
#   - UI rendering for oxygen bar
# ===================================

from OpenGL.GL import *
from OpenGL.GLUT import *
import time


class OxygenSystem:
    """
    Manages oxygen level with time-based depletion.
    Oxygen depletes only when diver is moving, taking exactly 3 minutes (180 seconds).
    """
    
    def __init__(self):
        """Initialize oxygen system at full capacity."""
        self.level = 100.0  # Current oxygen percentage (0-100)
        self.depletion_rate = 100.0 / 180.0  # Depletes 100% in 180 seconds
        self.is_depleting = False  # Only deplete when moving
        # Passive depletion per second (small background drain)
        self.passive_depletion = 0.02  # ~1.2% per minute
        
        # UI properties
        self.bar_x = 20
        self.bar_y = 660  # Top-left area (visible in 720px window)
        self.bar_width = 220
        self.bar_height = 35
    
    
    def start_depletion(self):
        """Begin oxygen depletion (called when diver starts moving)."""
        self.is_depleting = True
    
    
    def stop_depletion(self):
        """Stop oxygen depletion (called when diver stops moving)."""
        self.is_depleting = False
    
    
    def update(self, delta_time):
        """
        Update oxygen level based on elapsed time.
        
        Args:
            delta_time: Time elapsed since last update in seconds
        """
        # Passive background depletion
        if self.level > 0:
            self.level -= self.passive_depletion * delta_time
        # Active depletion when moving
        if self.is_depleting and self.level > 0:
            self.level -= self.depletion_rate * delta_time

        self.level = max(0.0, self.level)  # Clamp to 0
    
    
    def is_critical(self):
        """
        Check if oxygen is at critical level (below 15%).
        Used to trigger health depletion.
        
        Returns:
            bool: True if oxygen is below 15%
        """
        return self.level < 15.0
    
    
    def is_depleted(self):
        """
        Check if oxygen is completely depleted.
        
        Returns:
            bool: True if oxygen level is 0
        """
        return self.level <= 0.0
    
    
    def draw_bar(self, window_width, window_height):
        """
        Draw oxygen bar with gradient, shadow, and shine effects.
        Minecraft-inspired blocky style with vibrant colors.
        
        Args:
            window_width: Window width for 2D projection
            window_height: Window height for 2D projection
        """
        # Set up 2D orthographic projection for UI
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        from OpenGL.GLU import gluOrtho2D
        gluOrtho2D(0, window_width, 0, window_height)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Disable depth testing so UI always renders on top
        glDisable(GL_DEPTH_TEST)
       

        # === Draw shadow for depth ===
        glColor3f(0, 0, 0)
        glBegin(GL_QUADS)
        glVertex2f(self.bar_x + 4, self.bar_y - 4)
        glVertex2f(self.bar_x + self.bar_width + 4, self.bar_y - 4)
        glVertex2f(self.bar_x + self.bar_width + 4, self.bar_y + self.bar_height - 4)
        glVertex2f(self.bar_x + 4, self.bar_y + self.bar_height - 4)
        glEnd()
        
        # === Draw background (empty bar) with gradient ===
        glBegin(GL_QUADS)
        # Bottom color - dark
        glColor3f(0.08, 0.12, 0.18)
        glVertex2f(self.bar_x, self.bar_y)
        glVertex2f(self.bar_x + self.bar_width, self.bar_y)
        # Top color - slightly lighter
        glColor3f(0.12, 0.16, 0.22)
        glVertex2f(self.bar_x + self.bar_width, self.bar_y + self.bar_height)
        glVertex2f(self.bar_x, self.bar_y + self.bar_height)
        glEnd()
        
        # === Draw filled portion with gradient ===
        filled_width = self.bar_width * (self.level / 100.0)
        
        if filled_width > 0:
            # Color changes based on oxygen level
            if self.level > 50:
                # High oxygen - bright cyan/blue
                color_bottom = (0.0, 0.75, 1.0)
                color_top = (0.3, 0.95, 1.0)
            elif self.level > 15:
                # Medium oxygen - yellow/orange warning
                color_bottom = (1.0, 0.7, 0.0)
                color_top = (1.0, 0.9, 0.3)
            else:
                # Critical oxygen - red danger
                color_bottom = (0.95, 0.15, 0.0)
                color_top = (1.0, 0.4, 0.2)
            
            glBegin(GL_QUADS)
            # Bottom gradient
            glColor3f(*color_bottom)
            glVertex2f(self.bar_x, self.bar_y)
            glVertex2f(self.bar_x + filled_width, self.bar_y)
            # Top gradient
            glColor3f(*color_top)
            glVertex2f(self.bar_x + filled_width, self.bar_y + self.bar_height)
            glVertex2f(self.bar_x, self.bar_y + self.bar_height)
            glEnd()
            
            # === Add shine/highlight effect on top ===
            glBegin(GL_QUADS)
            glColor3f(0.35, 0.35, 0.35)  # Semi-transparent white
            glVertex2f(self.bar_x, self.bar_y + self.bar_height * 0.65)
            glVertex2f(self.bar_x + filled_width, self.bar_y + self.bar_height * 0.65)
            glColor3f(0.08, 0.08, 0.08)  # More transparent at top
            glVertex2f(self.bar_x + filled_width, self.bar_y + self.bar_height)
            glVertex2f(self.bar_x, self.bar_y + self.bar_height)
            glEnd()
        
        # === Draw border (outline) ===
        glColor3f(0.85, 0.92, 1.0)  # Light cyan/white
        glLineWidth(4)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.bar_x, self.bar_y)
        glVertex2f(self.bar_x + self.bar_width, self.bar_y)
        glVertex2f(self.bar_x + self.bar_width, self.bar_y + self.bar_height)
        glVertex2f(self.bar_x, self.bar_y + self.bar_height)
        glEnd()
        
        # Restore matrix state
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        # Restore GL state
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
    
    
    def draw_text(self, window_width, window_height):
        """
        Draw oxygen percentage text with shadow effect.
        
        Args:
            window_width: Window width for 2D projection
            window_height: Window height for 2D projection
        """
        # Disable depth testing so text draws on top
        glDisable(GL_DEPTH_TEST)
        
        # Set up 2D projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        from OpenGL.GLU import gluOrtho2D
        gluOrtho2D(0, window_width, 0, window_height)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        text = f"O2: {int(self.level)}%"
        text_x = self.bar_x + 8
        text_y = self.bar_y + 15
        
        # Draw shadow
        glColor3f(0, 0, 0)
        glRasterPos2f(text_x + 2, text_y - 2)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Draw main text
        glColor3f(1, 1, 1)
        glRasterPos2f(text_x, text_y)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        # Restore GL state
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
    
    
    def render(self, window_width=1000, window_height=800):
        """
        Main render method for oxygen UI.
        Draws bar and text overlay.
        
        Args:
            window_width: Window width (default 1000)
            window_height: Window height (default 800)
        """
        self.draw_bar(window_width, window_height)
        self.draw_text(window_width, window_height)

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random

class PinkFish:
    def __init__(self, x, z, y):
        self.base_x = x
        self.base_z = z
        self.base_y = y
        self.wander_radius = random.uniform(6.0, 12.0)
        self.phase = random.uniform(0, 6.28318)
        self.speed = random.uniform(0.3, 0.6)
        self.vertical_speed = random.uniform(0.15, 0.3)
        self.size = random.uniform(0.35, 0.55)
        
        # Pink and purple gradient colors
        if random.random() < 0.5:
            self.body_color = (1.0, 0.4, 0.8)  # Bright pink
            self.accent_color = (0.8, 0.2, 0.9)  # Purple
        else:
            self.body_color = (0.9, 0.3, 0.9)  # Magenta
            self.accent_color = (1.0, 0.5, 0.9)  # Light pink
        
        self.angle = 0.0
        self.x = x
        self.y = y
        self.z = z
        self.prev_x = x
        self.prev_z = z

    def update(self, t):
        # Store previous position
        self.prev_x = self.x
        self.prev_z = self.z
        
        circle_x = math.cos(t * self.speed * 0.3 + self.phase) * self.wander_radius
        circle_z = math.sin(t * self.speed * 0.3 + self.phase) * self.wander_radius
        swim_offset_x = math.sin(t * self.speed + self.phase) * 2.0
        swim_offset_z = math.cos(t * self.speed * 0.7 + self.phase) * 2.0
        self.x = self.base_x + circle_x + swim_offset_x
        self.z = self.base_z + circle_z + swim_offset_z
        self.y = self.base_y + math.sin(t * self.vertical_speed + self.phase) * 1.5
        
        # Calculate direction from actual movement
        dx = self.x - self.prev_x
        dz = self.z - self.prev_z
        
        # Only update angle if fish is actually moving
        if abs(dx) > 0.001 or abs(dz) > 0.001:
            self.angle = math.atan2(dz, dx)

    def draw(self):
        import time
        t = time.time()
        flow_wave = math.sin(t * 2.5 + self.phase) * 8
        
        # Main body (elongated and elegant)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glColor3f(*self.body_color)
        glScalef(self.size * 1.3, self.size * 0.7, self.size * 0.6)
        glutSolidSphere(1.0, 14, 14)
        glPopMatrix()
        
        # Tail connector
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.0, 0, 0)
        glColor3f(*self.body_color)
        glScalef(self.size * 0.5, self.size * 0.5, self.size * 0.4)
        glutSolidSphere(1.0, 12, 12)
        glPopMatrix()
        
        # Long flowing tail - upper section
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.6, self.size * 0.2, 0)
        glRotatef(flow_wave, 0, 0, 1)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.8, self.size * 0.8, self.size * 0.05)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Long flowing tail - lower section
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.6, -self.size * 0.2, 0)
        glRotatef(-flow_wave, 0, 0, 1)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.8, self.size * 0.8, self.size * 0.05)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Flowing tail end - upper ribbon
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 2.8, self.size * 0.4, 0)
        glRotatef(flow_wave * 1.5, 0, 0, 1)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.2, self.size * 0.6, self.size * 0.03)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Flowing tail end - lower ribbon
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 2.8, -self.size * 0.4, 0)
        glRotatef(-flow_wave * 1.5, 0, 0, 1)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.2, self.size * 0.6, self.size * 0.03)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Upper dorsal fin (large and flowing)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.1, self.size * 0.8, 0)
        glRotatef(flow_wave * 0.5, 1, 0, 0)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.0, self.size * 1.2, self.size * 0.04)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Flowing side fins (like ribbons)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.4, 0, self.size * 0.5)
        glRotatef(30 + flow_wave * 0.7, 1, 0, 0)
        glRotatef(20, 0, 1, 0)
        glColor3f(*self.accent_color)
        glScalef(self.size * 0.12, self.size * 1.5, self.size * 0.04)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.4, 0, -self.size * 0.5)
        glRotatef(-30 - flow_wave * 0.7, 1, 0, 0)
        glRotatef(-20, 0, 1, 0)
        glColor3f(*self.accent_color)
        glScalef(self.size * 0.12, self.size * 1.5, self.size * 0.04)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Eyes with sparkle
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.9, self.size * 0.3, self.size * 0.35)
        glColor3f(0.2, 0.1, 0.3)
        glutSolidSphere(self.size * 0.15, 10, 10)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.9, self.size * 0.3, -self.size * 0.35)
        glColor3f(0.2, 0.1, 0.3)
        glutSolidSphere(self.size * 0.15, 10, 10)
        glPopMatrix()
        
        # Eye highlights
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.95, self.size * 0.35, self.size * 0.35)
        glColor3f(1.0, 1.0, 1.0)
        glutSolidSphere(self.size * 0.06, 8, 8)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.95, self.size * 0.35, -self.size * 0.35)
        glColor3f(1.0, 1.0, 1.0)
        glutSolidSphere(self.size * 0.06, 8, 8)
        glPopMatrix()

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import time


class ScoreSystem:
    def __init__(self):
        self.score = 0
        # shutter animation state
        self.shutter_duration = 0.6  # total seconds for close+open
        self.shutter_elapsed = 0.0
        self.shutter_active = False
        self._last_trigger = 0.0

    def add_point(self):
        self.score += 1

    def trigger_shutter(self):
        self.shutter_active = True
        self.shutter_elapsed = 0.0
        self._last_trigger = time.time()

    def update(self, dt):
        if not self.shutter_active:
            return
        self.shutter_elapsed += dt
        if self.shutter_elapsed >= self.shutter_duration:
            self.shutter_active = False
            self.shutter_elapsed = 0.0

    def draw(self, w, h):
        # Draw score text (top-right)
        # Ensure overlays draw on top
        glDisable(GL_DEPTH_TEST)
      
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, w, 0, h)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Score text
        text = f"Score: {self.score}"
        glColor3f(1.0, 1.0, 1.0)
        glRasterPos2f(w - 150, h - 40)
        for c in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

        # Draw shutter if active
        if self.shutter_active:
            t = self.shutter_elapsed / max(1e-6, self.shutter_duration)
            # progress goes 0->1->0 (closing then opening)
            if t <= 0.5:
                prog = (t / 0.5)  # 0..1 closing
            else:
                prog = ((1.0 - t) / 0.5)  # 1..0 opening
            prog = max(0.0, min(1.0, prog))

            half_h = (h * 0.5) * prog

            # Draw two black rectangles from top and bottom
            glColor3f(0.0, 0.0, 0.0)
            glBegin(GL_QUADS)
            # top quad
            glVertex2f(0, h)
            glVertex2f(w, h)
            glVertex2f(w, h - half_h)
            glVertex2f(0, h - half_h)
            # bottom quad
            glVertex2f(0, 0)
            glVertex2f(w, 0)
            glVertex2f(w, half_h)
            glVertex2f(0, half_h)
            glEnd()

            # brief white flash at midpoint when fully closed
            if prog > 0.98:
              
                glColor3f(1.0*0.6, 1.0*0.6, 1.0*0.6)
                glBegin(GL_QUADS)
                glVertex2f(0, 0)
                glVertex2f(w, 0)
                glVertex2f(w, h)
                glVertex2f(0, h)
                glEnd()
                glDisable(GL_BLEND)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        # Restore GL state
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
# import config

class SettingsMenu:
    def __init__(self, background=None):
        self.is_open = False
        self.selected_option = 0
        self.selected_preset = 0
        self.editing_variable = None
        self.edit_value = ""
        self.background = background  # Reference to background for regeneration
        
        # Graphics presets
        self.presets = [
            {
                "name": "Low",
                "DRAW_RADIUS": 30,
                "USE_VIEW_CULLING": True,
            },
            {
                "name": "Medium",
                "DRAW_RADIUS": 50,
                "USE_VIEW_CULLING": True,
            },
            {
                "name": "High",
                "DRAW_RADIUS": 70,
                "USE_VIEW_CULLING": True,
            },
            {
                "name": "Ultra",
                "DRAW_RADIUS": 100,
                "USE_VIEW_CULLING": False,
            }
        ]
        
        # Graphics variables that can be adjusted
        self.adjustable_vars = [
            ("DRAW_RADIUS", "Draw Distance", 10, 150, int),
        ]
    
    def toggle(self):
        """Toggle menu open/closed."""
        self.is_open = not self.is_open
        if not self.is_open:
            self.editing_variable = None
            self.edit_value = ""
    
    def handle_key(self, key):
        """Handle keyboard input in menu."""
        if not self.is_open:
            return False
        
        if key == b'\x1b':  # ESC to close
            self.toggle()
            return True
        
        if self.editing_variable is not None:
            # Editing a variable value
            if key == b'\r' or key == b'\n':  # Enter to confirm
                self._apply_edit()
                return True
            elif key == b'\x08' or key == b'\x7f':  # Backspace
                self.edit_value = self.edit_value[:-1]
                return True
            elif key >= b'0' and key <= b'9' or key == b'.' or key == b'-':
                self.edit_value += key.decode('utf-8')
                return True
        else:
            # Navigating menu
            if key == b'w' or key == b'W':
                self.selected_option = max(0, self.selected_option - 1)
                return True
            elif key == b's' or key == b'S':
                self.selected_option = min(len(self.adjustable_vars) + len(self.presets) + 1, self.selected_option + 1)
                return True
            elif key == b'\r' or key == b'\n':  # Enter to select
                self._handle_select()
                return True
            elif key >= b'1' and key <= b'4':  # Quick preset selection
                preset_idx = int(key) - 1
                if preset_idx < len(self.presets):
                    self._apply_preset(preset_idx)
                    return True
        
        return False
    
    def _handle_select(self):
        """Handle menu option selection."""
        total_options = len(self.presets) + len(self.adjustable_vars) + 1
        
        if self.selected_option < len(self.presets):
            # Select preset
            self._apply_preset(self.selected_option)
        elif self.selected_option < len(self.presets) + len(self.adjustable_vars):
            # Edit variable
            var_idx = self.selected_option - len(self.presets)
            var_name, _, _, _, _ = self.adjustable_vars[var_idx]
            current_value = getattr(config, var_name, 0)
            self.editing_variable = var_name
            self.edit_value = str(current_value)
        # Last option is "Close" which is handled by ESC
    
    def _apply_preset(self, preset_idx):
        """Apply a graphics preset."""
        preset = self.presets[preset_idx]
        for key, value in preset.items():
            if key != "name" and hasattr(config, key):
                setattr(config, key, value)
        self.selected_preset = preset_idx
        print(f"Applied {preset['name']} graphics preset")
    
    def _apply_edit(self):
        """Apply edited variable value."""
        if self.editing_variable is None:
            return
        
        var_name = self.editing_variable
        var_info = next((v for v in self.adjustable_vars if v[0] == var_name), None)
        
        if var_info:
            _, _, min_val, max_val, var_type = var_info
            try:
                new_value = var_type(self.edit_value)
                new_value = max(min_val, min(max_val, new_value))
                setattr(config, var_name, new_value)
                print(f"Set {var_name} to {new_value}")
            except ValueError:
                print(f"Invalid value for {var_name}")
        
        self.editing_variable = None
        self.edit_value = ""
    
    def draw(self):
        """Draw the settings menu."""
        if not self.is_open:
            return
        
        # Switch to 2D rendering
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, config.WINDOW_WIDTH, 0, config.WINDOW_HEIGHT)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Draw background
        glColor3f(0.0, 0.0, 0.0)  # Black background
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(config.WINDOW_WIDTH, 0)
        glVertex2f(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        glVertex2f(0, config.WINDOW_HEIGHT)
        glEnd()
        
        # Draw menu box
        menu_x = config.WINDOW_WIDTH // 2 - 200
        menu_y = config.WINDOW_HEIGHT // 2 - 250
        menu_w = 400
        menu_h = 500
        
        glColor3f(0.2, 0.3, 0.4)
        glBegin(GL_QUADS)
        glVertex2f(menu_x, menu_y)
        glVertex2f(menu_x + menu_w, menu_y)
        glVertex2f(menu_x + menu_w, menu_y + menu_h)
        glVertex2f(menu_x, menu_y + menu_h)
        glEnd()
        
        # Draw border
        glColor3f(0.5, 0.7, 0.9)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(menu_x, menu_y)
        glVertex2f(menu_x + menu_w, menu_y)
        glVertex2f(menu_x + menu_w, menu_y + menu_h)
        glVertex2f(menu_x, menu_y + menu_h)
        glEnd()
        
        # Draw title
        self._draw_text(menu_x + 150, menu_y + 450, "GRAPHICS SETTINGS", 1.0, 1.0, 1.0)
        
        # Draw presets section
        y_offset = 400
        self._draw_text(menu_x + 20, menu_y + y_offset, "PRESETS (Press 1-4):", 0.8, 0.9, 1.0)
        y_offset -= 30
        
        for i, preset in enumerate(self.presets):
            color = (0.9, 0.9, 0.9) if i == self.selected_option else (0.7, 0.7, 0.7)
            marker = "> " if i == self.selected_option else "  "
            self._draw_text(menu_x + 30, menu_y + y_offset, f"{marker}{i+1}. {preset['name']}", *color)
            y_offset -= 25
        
        y_offset -= 10
        self._draw_text(menu_x + 20, menu_y + y_offset, "ADJUSTABLE VARIABLES:", 0.8, 0.9, 1.0)
        y_offset -= 30
        
        # Draw adjustable variables
        var_start_idx = len(self.presets)
        for i, (var_name, display_name, _, _, _) in enumerate(self.adjustable_vars):
            option_idx = var_start_idx + i
            color = (0.9, 0.9, 0.9) if option_idx == self.selected_option else (0.7, 0.7, 0.7)
            marker = "> " if option_idx == self.selected_option else "  "
            
            current_value = getattr(config, var_name, "N/A")
            if self.editing_variable == var_name:
                display_text = f"{marker}{display_name}: [{self.edit_value}]"
                color = (1.0, 1.0, 0.0)  # Yellow when editing
            else:
                display_text = f"{marker}{display_name}: {current_value}"
            
            self._draw_text(menu_x + 30, menu_y + y_offset, display_text, *color)
            y_offset -= 25
        
        # Draw close option
        y_offset -= 10
        close_idx = len(self.presets) + len(self.adjustable_vars)
        color = (0.9, 0.3, 0.3) if close_idx == self.selected_option else (0.7, 0.3, 0.3)
        marker = "> " if close_idx == self.selected_option else "  "
        self._draw_text(menu_x + 30, menu_y + y_offset, f"{marker}Close (ESC)", *color)
        
        # Draw instructions
        y_offset = 50
        self._draw_text(menu_x + 20, menu_y + y_offset, "W/S: Navigate  Enter: Select", 0.6, 0.6, 0.6)
        y_offset -= 20
        self._draw_text(menu_x + 20, menu_y + y_offset, "1-4: Quick Preset  ESC: Close", 0.6, 0.6, 0.6)
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    def _draw_text(self, x, y, text, r, g, b):
        """Draw text using bitmap characters."""
        glColor3f(r, g, b)
        glRasterPos2f(x, y)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))

from OpenGL.GL import *
from OpenGL.GLUT import *
import math
import random
import time

class Shark:
    def __init__(self, x, y, z, yaw=0.0):
        self.x = x
        self.y = y
        self.z = z
        # speed in world units per second
        self.speed = 1.6
        self.last_attack = 0
        # facing yaw in degrees (model forward is +X)
        self.yaw = yaw

    def update(self, cam, health, dt):
        # cam: camera object with `pos` and `yaw` attributes
        # compute camera right vector from yaw (degrees)
        rad = math.radians(cam.yaw)
        right_x = math.cos(rad)
        right_z = math.sin(rad)
        # move left across the screen (right -> left)
        dir_x = -right_x
        dir_z = -right_z

        # update facing yaw so model front (+X) points along movement dir
        self.yaw = math.degrees(math.atan2(dir_z, dir_x))

        # Advance shark; scale by dt to make movement time-based
        self.x += dir_x * self.speed * dt
        self.z += dir_z * self.speed * dt

        # Collision check with player
        dx = cam.pos[0] - self.x
        dz = cam.pos[2] - self.z
        dist = math.sqrt(dx*dx + dz*dz)

        if dist < 1.4 and time.time() - self.last_attack > 0.5:
            dmg = 15
            try:
                if hasattr(health, 'take_damage'):
                    # prefer a dedicated method if present
                    health.take_damage(dmg)
                elif hasattr(health, 'level'):
                    health.level = max(0.0, health.level - dmg)
                    # update death flag if helper exists
                    if hasattr(health, 'is_depleted'):
                        try:
                            health.is_depleted()
                        except Exception:
                            pass
            except Exception as e:
                print("Error applying shark damage:", e)
            self.last_attack = time.time()
            try:
                print(f"Shark hit player: health={getattr(health, 'level', None)}")
            except Exception:
                pass
            return True
        return False

    def draw(self, cam=None):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)

        # Orient shark by its movement yaw so the front (+X) points forward along movement direction
        try:
            glRotatef(self.yaw, 0.0, 1.0, 0.0)
        except Exception:
            pass
        # Main body (elongated sphere)
        glPushMatrix()
        glColor3f(0.18, 0.18, 0.18)
        glScalef(1.5, 0.65, 1.0)
        glutSolidSphere(1.0, 20, 20)
        glPopMatrix()

        # Head (smaller forward sphere) to give a clear snout
        glPushMatrix()
        glTranslatef(0.9, 0.05, 0.0)
        glColor3f(0.16, 0.16, 0.16)
        glutSolidSphere(0.45, 16, 12)
        glPopMatrix()

        # Tail (two triangular lobes) - slightly larger and more tapered
        glPushMatrix()
        glTranslatef(-1.18, 0.0, 0.0)
        glColor3f(0.08, 0.08, 0.08)
        # top lobe
        glBegin(GL_TRIANGLES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(-0.8, 0.45, 0.18)
        glVertex3f(-0.8, 0.0, -0.18)
        glEnd()
        # bottom lobe
        glBegin(GL_TRIANGLES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(-0.8, -0.45, -0.18)
        glVertex3f(-0.8, 0.0, 0.18)
        glEnd()
        glPopMatrix()

        # Dorsal fin (larger, more swept back)
        glPushMatrix()
        glTranslatef(0.08, 0.44, 0.0)
        glRotatef(-12, 0, 1, 0)
        glColor3f(0.12, 0.12, 0.12)
        glBegin(GL_TRIANGLES)
        glVertex3f(-0.35, 0.0, 0.0)
        glVertex3f(0.55, 0.9, 0.0)
        glVertex3f(0.35, 0.0, 0.0)
        glEnd()
        glPopMatrix()

        # Pectoral fins (left/right) - more pronounced and angled
        glPushMatrix()
        glTranslatef(0.25, -0.14, 0.6)
        glRotatef(28, 0, 1, 0)
        glColor3f(0.09, 0.09, 0.09)
        glBegin(GL_TRIANGLES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.7, -0.18, 0.0)
        glVertex3f(-0.4, 0.08, 0.0)
        glEnd()
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.25, -0.14, -0.6)
        glRotatef(-28, 0, 1, 0)
        glColor3f(0.09, 0.09, 0.09)
        glBegin(GL_TRIANGLES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.7, -0.18, 0.0)
        glVertex3f(-0.4, 0.08, 0.0)
        glEnd()
        glPopMatrix()

        # Eyes on both sides for visibility
        # Eyes on both sides for visibility (draw mirrored)
        # Move eyes further forward/outward and make larger so they sit on the head surface
        eye_white_radius = 0.16
        eye_pupil_radius = 0.05
        eye_white_color = (1.0, 1.0, 1.0)
        eye_x = 1.05  # forward along nose (on head surface)
        eye_y = 0.14
        eye_z_offset = 0.48

        # left eye
        glPushMatrix()
        glTranslatef(eye_x, eye_y, -eye_z_offset)
        glColor3f(*eye_white_color)
        glutSolidSphere(eye_white_radius, 12, 10)
        glColor3f(0.0, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(0.03, 0.0, 0.0)
        glutSolidSphere(eye_pupil_radius, 10, 8)
        glPopMatrix()
        glPopMatrix()

        # right eye (mirror)
        glPushMatrix()
        glTranslatef(eye_x, eye_y, eye_z_offset)
        glColor3f(*eye_white_color)
        glutSolidSphere(eye_white_radius, 12, 10)
        glColor3f(0.0, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(0.03, 0.0, 0.0)
        glutSolidSphere(eye_pupil_radius, 10, 8)
        glPopMatrix()
        glPopMatrix()

        glPopMatrix()


class SharkManager:
    def __init__(self):
        self.sharks = []
        # prevent spawn at start: initialize last_spawn to current time
        self.last_spawn = time.time()
        # fixed spawn interval in seconds (sharks appear every 12 seconds)
        self.spawn_interval = 12.0

    def update(self, cam, health, oxygen, dt):
        # Spawn at fixed intervals (no spawn at game start)
        if time.time() - self.last_spawn > self.spawn_interval:
            # spawn to the right of camera so it moves left across the screen
            rad = math.radians(cam.yaw)
            right_x = math.cos(rad)
            right_z = math.sin(rad)
            forward_x = math.sin(rad)
            forward_z = -math.cos(rad)
            spawn_dist = 18.0
            sx = cam.pos[0] + right_x * spawn_dist + forward_x * random.uniform(-6, 6)
            sz = cam.pos[2] + right_z * spawn_dist + forward_z * random.uniform(-6, 6)
            sy = cam.pos[1]
            # determine movement direction (to the left of camera) and yaw
            dir_x = -right_x
            dir_z = -right_z
            yaw = math.degrees(math.atan2(dir_z, dir_x))
            self.sharks.append(Shark(sx, sy, sz, yaw=yaw))
            self.last_spawn = time.time()

        collisions = 0
        for shark in self.sharks:
            hit = shark.update(cam, health, dt)
            if hit:
                # also reduce oxygen strongly on contact
                if oxygen is not None:
                    oxygen.level = max(0.0, oxygen.level - 30.0)
                collisions += 1
        return collisions

    def draw(self, cam=None):
        """Draw all sharks; if `cam` provided, rotate each shark to face it."""
        for shark in self.sharks:
            if cam is not None:
                shark.draw(cam)
            else:
                # fallback: pass a dummy camera with position at origin
                shark.draw(type('C', (), {'pos': (0.0, 0.0, 0.0)}))

from OpenGL.GL import *
from OpenGL.GLUT import *
import math

class SubmarineBase:
    def __init__(self, x=10, y=3, z=10):
        self.x = x
        self.y = y
        self.z = z
        self.radius = 3.0  # refill zone (reduced so player must approach closer)

    def draw(self):
        # Draw submarine at its world position (static orientation)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)

        # Main body (ellipsoid)
        glPushMatrix()
        glColor3f(0.35, 0.36, 0.4)
        glScalef(1.8, 0.8, 0.9)
        glutSolidSphere(1.0, 24, 24)
        glPopMatrix()

        # Front circular window/dome placed centered on the body's front
        glPushMatrix()
        # translate forward along the local +X axis (body length ~1.8 -> half ~0.9)
        glTranslatef(0.95, 0.05, 0.0)
        glColor3f(0.18, 0.5, 0.7)
        # small rounded dome
        glutSolidSphere(0.28, 16, 12)
        glPopMatrix()

        # Side domes (small domes near the front on both sides)
        side_dome_offset_x = 0.8
        side_dome_y = 0.08
        side_dome_z = 0.6
        glColor3f(0.18, 0.5, 0.7)
        # right side dome
        glPushMatrix()
        glTranslatef(side_dome_offset_x, side_dome_y, side_dome_z)
        glutSolidSphere(0.16, 12, 10)
        glPopMatrix()
        # left side dome
        glPushMatrix()
        glTranslatef(side_dome_offset_x, side_dome_y, -side_dome_z)
        glutSolidSphere(0.16, 12, 10)
        glPopMatrix()

        # Add circular portholes along both sides (three per side)
        # Draw as a framed window: outer frame (darker), inner glass (cyan)
        frame_radius = 0.11
        glass_radius = 0.08
        frame_color = (0.12, 0.12, 0.14)
        glass_color = (0.18, 0.5, 0.7)
        for i, ofs in enumerate([-0.4, 0.0, 0.4]):
            # right side: frame then glass inset
            glPushMatrix()
            glTranslatef(0.05 + ofs, 0.0, 0.65)
            glColor3f(*frame_color)
            glutSolidSphere(frame_radius, 14, 12)
            glColor3f(*glass_color)
            glutSolidSphere(glass_radius, 12, 10)
            glPopMatrix()

            # left side (mirror)
            glPushMatrix()
            glTranslatef(0.05 + ofs, 0.0, -0.65)
            glColor3f(*frame_color)
            glutSolidSphere(frame_radius, 14, 12)
            glColor3f(*glass_color)
            glutSolidSphere(glass_radius, 12, 10)
            glPopMatrix()

        # Small periscope/stem on top
        glPushMatrix()
        glTranslatef(0.25, 0.5, 0.0)
        glRotatef(-10, 0, 0, 1)
        glColor3f(0.25, 0.25, 0.28)
        glBegin(GL_QUADS)
        glVertex3f(-0.03, -0.18, 0.0)
        glVertex3f(0.03, -0.18, 0.0)
        glVertex3f(0.03, 0.18, 0.0)
        glVertex3f(-0.03, 0.18, 0.0)
        glEnd()
        # periscope head
        glTranslatef(0.06, 0.18, 0.0)
        glColor3f(0.2, 0.2, 0.22)
        glutSolidSphere(0.05, 8, 8)
        glPopMatrix()

        # Add symmetric small periscopes on both sides (for visual balance)
        periscope_x = 0.15
        periscope_y = 0.45
        periscope_z = 0.38
        for zsign in (periscope_z, -periscope_z):
            glPushMatrix()
            glTranslatef(periscope_x, periscope_y, zsign)
            glRotatef(-10 if zsign > 0 else 10, 0, 0, 1)
            glColor3f(0.25, 0.25, 0.28)
            glBegin(GL_QUADS)
            glVertex3f(-0.02, -0.12, 0.0)
            glVertex3f(0.02, -0.12, 0.0)
            glVertex3f(0.02, 0.12, 0.0)
            glVertex3f(-0.02, 0.12, 0.0)
            glEnd()
            # periscope head
            glTranslatef(0.04, 0.12, 0.0)
            glColor3f(0.2, 0.2, 0.22)
            glutSolidSphere(0.035, 8, 8)
            glPopMatrix()

        # Small symmetric fin/hatch detail on the other side (for visual balance)
        glPushMatrix()
        glTranslatef(-0.05, -0.12, -0.6)
        glRotatef(8, 0, 1, 0)
        glColor3f(0.25, 0.25, 0.28)
        glBegin(GL_QUADS)
        glVertex3f(-0.02, -0.05, 0.0)
        glVertex3f(0.02, -0.05, 0.0)
        glVertex3f(0.02, 0.05, 0.0)
        glVertex3f(-0.02, 0.05, 0.0)
        glEnd()
        glPopMatrix()

        glPopMatrix()

    def is_inside(self, cam_pos):
        dx = cam_pos[0] - self.x
        dy = cam_pos[1] - self.y
        dz = cam_pos[2] - self.z
        return math.sqrt(dx*dx + dy*dy + dz*dz) <= self.radius

    def refill_player(self, oxygen, health):
        # Refill oxygen and health to full and stop oxygen depletion
        if hasattr(oxygen, 'level'):
            oxygen.level = 100.0
        if hasattr(oxygen, 'stop_depletion'):
            try:
                oxygen.stop_depletion()
            except Exception:
                oxygen.is_depleting = False
        # Use health.reset() if available to properly reset death flag
        if hasattr(health, 'reset'):
            try:
                health.reset()
            except Exception:
                health.level = 100.0
                health.is_dead = False
        else:
            if hasattr(health, 'level'):
                health.level = 100.0
            if hasattr(health, 'is_dead'):
                health.is_dead = False

"""create a map where the x-axis represents the width (horizontal axis) , 
z-xis represents the depth axis and 
y-axis represents the height (vertical axis)"""

worldMap = [[[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]],
            [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
            ]

world_X_Max = len(worldMap)
world_Y_Max = len(worldMap[0])

print(world_X_Max)
print(world_Y_Max)

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random

class YellowGrayFish:
    def __init__(self, x, z, y):
        self.base_x = x
        self.base_z = z
        self.base_y = y
        self.wander_radius = random.uniform(5.0, 10.0)
        self.phase = random.uniform(0, 6.28318)
        self.speed = random.uniform(0.4, 0.7)
        self.vertical_speed = random.uniform(0.2, 0.35)
        self.size = random.uniform(0.3, 0.5)
        
        # Yellow and gray color combinations
        if random.random() < 0.5:
            self.body_color = (1.0, 0.9, 0.2)  # Bright yellow
            self.accent_color = (0.5, 0.5, 0.5)  # Medium gray
        else:
            self.body_color = (0.9, 0.85, 0.3)  # Golden yellow
            self.accent_color = (0.6, 0.6, 0.6)  # Light gray
        
        self.angle = 0.0
        self.x = x
        self.y = y
        self.z = z
        self.prev_x = x
        self.prev_z = z

    def update(self, t):
        # Store previous position
        self.prev_x = self.x
        self.prev_z = self.z
        
        circle_x = math.cos(t * self.speed * 0.3 + self.phase) * self.wander_radius
        circle_z = math.sin(t * self.speed * 0.3 + self.phase) * self.wander_radius
        swim_offset_x = math.sin(t * self.speed + self.phase) * 1.8
        swim_offset_z = math.cos(t * self.speed * 0.7 + self.phase) * 1.8
        self.x = self.base_x + circle_x + swim_offset_x
        self.z = self.base_z + circle_z + swim_offset_z
        self.y = self.base_y + math.sin(t * self.vertical_speed + self.phase) * 1.2
        
        # Calculate direction from actual movement
        dx = self.x - self.prev_x
        dz = self.z - self.prev_z
        
        # Only update angle if fish is actually moving
        if abs(dx) > 0.001 or abs(dz) > 0.001:
            self.angle = math.atan2(dz, dx)

    def draw(self):
        import time
        t = time.time()
        tail_wave = math.sin(t * 3.0 + self.phase) * 12
        
        # Main diamond body
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glRotatef(45, 0, 0, 1)
        glColor3f(*self.body_color)
        glScalef(self.size * 1.5, self.size * 1.5, self.size * 0.7)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Gray stripe across middle
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glRotatef(45, 0, 0, 1)
        glColor3f(*self.accent_color)
        glScalef(self.size * 1.5, self.size * 0.5, self.size * 0.75)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Simple tail fin
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(-self.size * 1.3, 0, 0)
        glRotatef(tail_wave, 0, 1, 0)
        glColor3f(*self.body_color)
        glScalef(self.size * 1.0, self.size * 1.0, self.size * 0.08)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Side fins
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.3, 0, self.size * 0.6)
        glColor3f(*self.accent_color)
        glScalef(self.size * 0.1, self.size * 0.8, self.size * 0.05)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.3, 0, -self.size * 0.6)
        glColor3f(*self.accent_color)
        glScalef(self.size * 0.1, self.size * 0.8, self.size * 0.05)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.3, 0, -self.size * 0.6)
        glColor3f(*self.accent_color)
        glScalef(self.size * 0.1, self.size * 0.8, self.size * 0.05)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Eyes
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.8, self.size * 0.3, self.size * 0.4)
        glColor3f(0.0, 0.0, 0.0)
        glutSolidSphere(self.size * 0.14, 10, 10)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(math.degrees(self.angle), 0, 1, 0)
        glTranslatef(self.size * 0.8, self.size * 0.3, -self.size * 0.4)
        glColor3f(0.0, 0.0, 0.0)
        glutSolidSphere(self.size * 0.14, 10, 10)
        glPopMatrix()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    glutCreateWindow(b"Underwater Simulator")
    
    # Basic GL state
    glEnable(GL_DEPTH_TEST)

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

