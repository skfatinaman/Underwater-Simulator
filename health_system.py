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
        return self.level <= 0.0
    
    
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
            glColor4f(1, 1, 1, 0.32)
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
    
    
    def draw_text(self, window_width, window_height):
        """
        Draw health percentage text with shadow.
        
        Args:
            window_width: Window width for 2D projection
            window_height: Window height for 2D projection
        """
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
