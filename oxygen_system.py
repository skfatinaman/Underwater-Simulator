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
        
        # Enable blending for transparency effects
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
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
            glColor4f(1, 1, 1, 0.35)  # Semi-transparent white
            glVertex2f(self.bar_x, self.bar_y + self.bar_height * 0.65)
            glVertex2f(self.bar_x + filled_width, self.bar_y + self.bar_height * 0.65)
            glColor4f(1, 1, 1, 0.08)  # More transparent at top
            glVertex2f(self.bar_x + filled_width, self.bar_y + self.bar_height)
            glVertex2f(self.bar_x, self.bar_y + self.bar_height)
            glEnd()
        
        glDisable(GL_BLEND)
        
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
    
    
    def draw_text(self, window_width, window_height):
        """
        Draw oxygen percentage text with shadow effect.
        
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
