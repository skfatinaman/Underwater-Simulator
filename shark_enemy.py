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
