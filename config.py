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
