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
    def __init__(self, x, z, base_y, color=(0.1, 0.6, 0.2)):
        self.x = x + 0.5
        self.z = z + 0.5
        self.base_y = base_y + 0.5
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

        sway_top = math.sin(t + self.phase + 0.8) * (self.amp * 1.3)
        glPushMatrix()
        glTranslatef(self.x + sway_top, self.base_y + self.seg_len * 1.5, self.z)
        glColor3f(*self.color)
        glScalef(self.width, self.seg_len, self.width)
        glutSolidCube(1.0)
        glPopMatrix()

        if self._contains(cam.pos, sway, sway_top):
            cam.visible = False

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
        weed_threshold = 0.5
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
                    self.seaweeds.append(Seaweed(x, z, top_y))

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
