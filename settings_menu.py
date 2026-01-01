from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import config

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
