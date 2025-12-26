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
