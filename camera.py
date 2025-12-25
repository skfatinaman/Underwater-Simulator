from OpenGL.GLU import gluLookAt
import math
import config

class Camera:
    def __init__(self):
        self.pos = [0.0, 10.0, 30.0]
        self.yaw = -90.0
        self.pitch = 0.0
        self.look_dir = [0.0, 0.0, -1.0]
        self.speed = 0.8

    def update_vectors(self):
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)
        self.look_dir[0] = math.cos(rad_yaw) * math.cos(rad_pitch)
        self.look_dir[1] = math.sin(rad_pitch)
        self.look_dir[2] = math.sin(rad_yaw) * math.cos(rad_pitch)

    def apply_view(self):
        self.update_vectors()
        gluLookAt(self.pos[0], self.pos[1], self.pos[2],
                  self.pos[0] + self.look_dir[0], 
                  self.pos[1] + self.look_dir[1], 
                  self.pos[2] + self.look_dir[2],
                  0, 1, 0)

    def move(self, direction):
        self.pos[0] += self.look_dir[0] * self.speed * direction
        self.pos[1] += self.look_dir[1] * self.speed * direction
        self.pos[2] += self.look_dir[2] * self.speed * direction

    def clamp_to_ground(self, seabed_obj):
        ground_y = seabed_obj.get_height_at(self.pos[0], self.pos[2])
        min_h = ground_y + 2.5
        if self.pos[1] < min_h:
            self.pos[1] = min_h