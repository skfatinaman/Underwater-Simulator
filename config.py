# 0: Low, 1: Medium, 2: High, 3: Ultra
GRAPHICS_LEVEL = 1  

# States: "GAME" or "MENU"
STATE = "GAME"

# Colors
SEABED_BASE_COLOR = [0.46, 0.71, 0.77]
WATER_VOID_COLOR = [0.11, 0.63, 0.85]
SHADOW_BLUE_COLOR = [0.05, 0.15, 0.35]

SEABED_SIZE = 250
HILL_INTENSITY = 2.5

# Fish Settings
FISH_COUNT = 80

def get_detail_amount(base_amount):
    """
    Scales any quantity (like particle counts or plant density) 
    based on the current graphics level.
    """
    multipliers = {0: 0.25, 1: 0.5, 2: 1.0, 3: 2.0}
    return int(base_amount * multipliers.get(GRAPHICS_LEVEL, 1.0))