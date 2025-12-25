import random
import math
import time
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import config

class BaseFish:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        # Larger size (1.5x - 3.0x)
        self.size = random.uniform(1.5, 3.0)
        self.speed = random.uniform(0.05, 0.2)
        self.angle = random.uniform(0, 360)
        self.anim_offset = random.uniform(0, 100)
        
        # Base colors (subclasses can override or use these)
        self.color1 = [random.uniform(0.3, 1.0), random.uniform(0.3, 1.0), random.uniform(0.3, 1.0)]
        self.color2 = [random.uniform(0.3, 1.0), random.uniform(0.3, 1.0), random.uniform(0.3, 1.0)]

    def update(self, floor=None):
        # Move forward based on angle
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.z += math.sin(rad) * self.speed
        
        # Wrap around
        limit = config.SEABED_SIZE
        if self.x > limit: self.x = -limit
        if self.x < -limit: self.x = limit
        if self.z > limit: self.z = -limit
        if self.z < -limit: self.z = limit
        
        # Random turn
        if random.random() < 0.02:
            self.angle += random.uniform(-15, 15)

    def draw(self):
        pass

class Fish(BaseFish):
    """Standard round fish with single stripe"""
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.tail_color = [random.uniform(0.3, 1.0), random.uniform(0.3, 1.0), random.uniform(0.3, 1.0)]

    def draw_body_sphere(self):
        radius = 1.0
        stacks = 12
        slices = 12
        
        # Define stripe range (e.g., middle 3 stacks)
        stripe_start = stacks // 2 - 1
        stripe_end = stacks // 2 + 1
        
        for i in range(stacks):
            # Single stripe in the middle
            if stripe_start <= i <= stripe_end:
                glColor3f(*self.color2) # Stripe color
            else:
                glColor3f(*self.color1) # Body color

            lat0 = math.pi * (-0.5 + float(i) / stacks)
            z0 = math.sin(lat0) * radius
            zr0 = math.cos(lat0) * radius
            lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
            z1 = math.sin(lat1) * radius
            zr1 = math.cos(lat1) * radius
            
            glBegin(GL_QUADS)
            for j in range(slices):
                lng0 = 2 * math.pi * float(j) / slices
                x0 = math.cos(lng0)
                y0 = math.sin(lng0)
                
                lng1 = 2 * math.pi * float(j + 1) / slices
                x1 = math.cos(lng1)
                y1 = math.sin(lng1)

                # Draw quad (no normals as per strict list)
                glVertex3f(x0 * zr0, y0 * zr0, z0)
                glVertex3f(x0 * zr1, y0 * zr1, z1)
                glVertex3f(x1 * zr1, y1 * zr1, z1)
                glVertex3f(x1 * zr0, y1 * zr0, z0)
            glEnd()

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(-self.angle, 0, 1, 0)
        glScalef(self.size, self.size, self.size)
        
        # Body
        glPushMatrix()
        glScalef(1.0, 0.6, 0.3)
        self.draw_body_sphere()
        glPopMatrix()
        
        # Animation
        t = time.time() * 10 + self.anim_offset
        tail_angle = math.sin(t) * 20
        
        # Tail
        glColor3f(*self.tail_color)
        glPushMatrix()
        glTranslatef(-0.8, 0, 0)
        glRotatef(tail_angle, 0, 1, 0)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0); glVertex3f(-1.0, 0.5, 0); glVertex3f(-1.0, -0.5, 0)
        glEnd()
        glPopMatrix()
        
        # Fins
        for side in [1, -1]:
            glPushMatrix()
            glTranslatef(0.2, 0, 0.25 * side)
            glRotatef(-15 * side + tail_angle * 0.5, 0, 1, 0)
            glRotatef(-30 * side, 1, 0, 0)
            glBegin(GL_TRIANGLES)
            glVertex3f(0, 0, 0); glVertex3f(0.5, 0, 0.5 * side); glVertex3f(-0.2, 0, 0.5 * side)
            glEnd()
            glPopMatrix()
            
        glPopMatrix()

class TriangularFish(BaseFish):
    """Fish with a triangular prism body"""
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(-self.angle, 0, 1, 0)
        glScalef(self.size, self.size, self.size)
        
        t = time.time() * 10 + self.anim_offset
        tail_angle = math.sin(t) * 20

        # Triangular Body
        glColor3f(*self.color1)
        glBegin(GL_TRIANGLES)
        # Top
        glVertex3f(1.0, 0.0, 0.0)
        glVertex3f(-0.5, 0.5, 0.3)
        glVertex3f(-0.5, 0.5, -0.3)
        # Bottom
        glColor3f(*self.color2)
        glVertex3f(1.0, 0.0, 0.0)
        glVertex3f(-0.5, -0.5, 0.3)
        glVertex3f(-0.5, -0.5, -0.3)
        # Sides
        glColor3f(*self.color1)
        glVertex3f(1.0, 0.0, 0.0)
        glVertex3f(-0.5, 0.5, 0.3)
        glVertex3f(-0.5, -0.5, 0.3)
        
        glVertex3f(1.0, 0.0, 0.0)
        glVertex3f(-0.5, 0.5, -0.3)
        glVertex3f(-0.5, -0.5, -0.3)
        # Back
        glColor3f(*self.color2)
        glVertex3f(-0.5, 0.5, 0.3)
        glVertex3f(-0.5, -0.5, 0.3)
        glVertex3f(-0.5, -0.5, -0.3)
        glVertex3f(-0.5, 0.5, 0.3)
        glVertex3f(-0.5, -0.5, -0.3)
        glVertex3f(-0.5, 0.5, -0.3)
        glEnd()
        
        # Tail
        glPushMatrix()
        glTranslatef(-0.5, 0, 0)
        glRotatef(tail_angle, 0, 1, 0)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0); glVertex3f(-0.8, 0.6, 0); glVertex3f(-0.8, -0.6, 0)
        glEnd()
        glPopMatrix()
        
        glPopMatrix()

class Octopus(BaseFish):
    def update(self, floor=None):
        super().update(floor)
        # Bob up and down
        self.y += math.sin(time.time() * 2 + self.anim_offset) * 0.02

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glScalef(self.size, self.size, self.size)
        
        # Head
        glColor3f(*self.color1)
        glPushMatrix()
        glScalef(1.0, 1.2, 1.0)
        glutSolidSphere(0.6, 10, 10)
        glPopMatrix()
        
        # Legs (Bigger and longer)
        t = time.time() * 5 + self.anim_offset
        glColor3f(*self.color2)
        for i in range(8):
            angle = i * (360 / 8)
            
            glPushMatrix()
            glRotatef(angle, 0, 1, 0)
            glTranslatef(0.4, -0.2, 0) # Start further out
            
            # Wiggle
            wiggle = math.sin(t + i) * 30
            glRotatef(wiggle, 0, 1, 0)
            # Make legs hang down vertically (Align X axis to point down)
            glRotatef(-80, 0, 0, 1) 
            
            # Draw Leg (Longer)
            glBegin(GL_QUADS)
            # Segment 1
            glVertex3f(0, 0, -0.15); glVertex3f(1.5, -0.1, -0.1)
            glVertex3f(1.5, -0.1, 0.1); glVertex3f(0, 0, 0.15)
            # Segment 2 (Tip)
            glVertex3f(1.5, -0.1, -0.1); glVertex3f(2.5, 0.2, -0.05)
            glVertex3f(2.5, 0.2, 0.05); glVertex3f(1.5, -0.1, 0.1)
            glEnd()
            
            glPopMatrix()
            
        glPopMatrix()

class SchoolOfFish(BaseFish):
    """A group of small fishes moving together"""
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.offsets = []
        for _ in range(10): # 10 fish in the school
            ox = random.uniform(-3, 3)
            oy = random.uniform(-1, 1)
            oz = random.uniform(-3, 3)
            self.offsets.append((ox, oy, oz))
            
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(-self.angle, 0, 1, 0)
        
        # Draw the school
        glColor3f(*self.color1)
        for ox, oy, oz in self.offsets:
            glPushMatrix()
            glTranslatef(ox, oy, oz)
            # Wiggle individual fish
            t = time.time() * 10 + ox
            glRotatef(math.sin(t)*10, 0, 1, 0)
            
            # Simple small fish shape
            glScalef(0.5, 0.5, 0.5)
            glBegin(GL_TRIANGLES)
            # Body
            glVertex3f(0.5, 0, 0)
            glVertex3f(-0.5, 0.3, 0)
            glVertex3f(-0.5, -0.3, 0)
            # Tail
            glVertex3f(-0.5, 0, 0)
            glVertex3f(-0.8, 0.3, 0)
            glVertex3f(-0.8, -0.3, 0)
            glEnd()
            glPopMatrix()
            
        glPopMatrix()

class Crab(BaseFish):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.y_offset = 0.5 # Height above ground
        self.speed = 0.05 # Slower
        self.quad = gluNewQuadric()

    def update(self, floor=None):
        super().update(floor)
        if floor:
            h = floor.get_height_at(self.x, self.z)
            self.y = h + self.y_offset

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(-self.angle, 0, 1, 0)
        glScalef(self.size, self.size, self.size)
        
        # Body
        glColor3f(1.0, 0.4, 0.4) # Reddish
        glPushMatrix()
        glScalef(1.0, 0.4, 0.7)
        glutSolidSphere(0.6, 10, 10)
        glPopMatrix()
        
        # Legs
        t = time.time() * 10 + self.anim_offset
        glColor3f(0.8, 0.2, 0.2)
        for side in [1, -1]:
            for i in range(3):
                leg_phase = t + i * 2 if side == 1 else t + i * 2 + math.pi
                leg_lift = abs(math.sin(leg_phase)) * 0.2
                
                glPushMatrix()
                glTranslatef(0.2 * i - 0.2, 0, 0.4 * side)
                glRotatef(30 * side, 1, 0, 0) # Angle out
                
                # Draw thick leg segments using cylinders
                
                # Segment 1: (0,0,0) to (0, leg_lift, 0.5*side)
                dy1 = leg_lift
                dz1 = 0.5 * side
                dist1 = math.sqrt(dy1**2 + dz1**2)
                angle1 = math.degrees(math.atan2(dy1, dz1)) # Angle from Z axis
                # glutSolidCylinder draws along +Z.
                # atan2(y, x) -> atan2(dy, dz).
                # We need to rotate around X axis.
                # Positive rotation around X moves Y towards Z.
                # Actually, standard rotation: glRotatef(-angle, 1, 0, 0) might be needed depending on coord sys.
                # Let's try:
                
                glPushMatrix()
                # Rotate so Z aligns with vector
                # Vector is (0, dy1, dz1)
                # We want (0, 0, dist1)
                glRotatef(-angle1, 1, 0, 0) # Rotate X to bring Z up to vector? 
                # If angle is 90 (up), we want to rotate -90?
                # atan2(1, 0) = 90. cylinder is (0,0,1).
                # We want (0,1,0). glRotatef(-90, 1,0,0) -> y becomes z? No.
                # y' = y cos - z sin
                # z' = y sin + z cos
                # (0,0,1) -> (0, -sin(-90), cos(-90)) = (0, 1, 0). Yes. -90 works.
                
                gluCylinder(self.quad, 0.04, 0.04, dist1, 6, 1)
                glPopMatrix()
                
                # Segment 2: from (0, leg_lift, 0.5*side) to (0, -0.5, 0.8*side)
                dy2 = -0.5 - leg_lift
                dz2 = (0.8 * side) - (0.5 * side)
                dist2 = math.sqrt(dy2**2 + dz2**2)
                angle2 = math.degrees(math.atan2(dy2, dz2))
                
                glPushMatrix()
                glTranslatef(0, leg_lift, 0.5 * side)
                glRotatef(-angle2, 1, 0, 0)
                gluCylinder(self.quad, 0.03, 0.03, dist2, 6, 1)
                glPopMatrix()
                
                glPopMatrix()
        glPopMatrix()

class Eel(BaseFish):
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(-self.angle, 0, 1, 0)
        glScalef(self.size, self.size, self.size)
        
        t = time.time() * 5 + self.anim_offset
        
        glColor3f(*self.color1)
        
        # Draw segments
        prev_x, prev_z = 0, 0
        segments = 15
        for i in range(segments):
            # Snake motion
            wave = math.sin(t - i * 0.5) * 0.3
            curr_x = -i * 0.3
            curr_z = wave
            
            if i > 0:
                # Draw segment connecting prev to curr
                glBegin(GL_LINES)
                glVertex3f(prev_x, 0, prev_z)
                glVertex3f(curr_x, 0, curr_z)
                glEnd()
                
                # Draw sphere at joint
                glPushMatrix()
                glTranslatef(curr_x, 0, curr_z)
                glutSolidSphere(0.15 - (i * 0.005), 6, 6) # Taper
                glPopMatrix()
                
            prev_x, prev_z = curr_x, curr_z
            
        glPopMatrix()

class FishManager:
    def __init__(self, count=20):
        self.fishes = []
        self.target_count = count
        # No initial spawn, updated in loop
            
    def set_count(self, count):
        self.target_count = count

    def update(self, floor=None, cam_pos=None):
        # 1. Remove far away fish
        if cam_pos:
            spawn_radius = 80.0
            despawn_radius = 120.0
            
            # Keep only fish within despawn radius
            self.fishes = [f for f in self.fishes if 
                           math.sqrt((f.x - cam_pos[0])**2 + (f.z - cam_pos[2])**2) < despawn_radius]
            
            # 2. Add new fish near player if count is low
            current_count = len(self.fishes)
            if current_count < self.target_count:
                for _ in range(self.target_count - current_count):
                    # Spawn in a ring around the player (visible but not on top)
                    angle = random.uniform(0, 2 * math.pi)
                    dist = random.uniform(20, spawn_radius)
                    
                    x = cam_pos[0] + math.cos(angle) * dist
                    z = cam_pos[2] + math.sin(angle) * dist
                    
                    # Pick a random type (No Eels)
                    r = random.random()
                    if r < 0.5:
                        y = random.uniform(5, 30)
                        self.fishes.append(Fish(x, y, z))
                    elif r < 0.7:
                        y = random.uniform(5, 30)
                        self.fishes.append(TriangularFish(x, y, z))
                    elif r < 0.8:
                        y = random.uniform(5, 30)
                        self.fishes.append(Octopus(x, y, z))
                    elif r < 0.9:
                        # School of fish
                        y = random.uniform(5, 30)
                        self.fishes.append(SchoolOfFish(x, y, z))
                    else:
                        # Crab
                        self.fishes.append(Crab(x, 0, z))

        for fish in self.fishes:
            fish.update(floor)
            
    def draw(self):
        for fish in self.fishes:
            fish.draw()
