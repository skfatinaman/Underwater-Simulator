from OpenGL.GL import *

class UnderwaterBackground:
    """Draws an underwater gradient background from dark blue (bottom) to light blue (top)."""
    
    def __init__(self):
        # Define gradient colors from darkest (bottom) to lightest (top)
        self.num_layers = 50  # More layers = smoother gradient
        
    def draw(self):
        """Draw gradient background using multiple horizontal rectangles."""
        glPushMatrix()
        glLoadIdentity()
        
        # Position far behind the scene
        z_position = -100
        size = 150  # Large size to cover entire view
        
        # Y range for gradient
        y_min = -size
        y_max = size
        layer_height = (y_max - y_min) / self.num_layers
        
        # Color range: dark blue at bottom to light blue at top
        # Deep underwater navy (bottom) - darker and more blue-green
        r_start, g_start, b_start = 0.0, 0.05, 0.15
        # Bright aqua blue (top) - more vibrant underwater feel
        r_end, g_end, b_end = 0.3, 0.7, 0.85
        
        # Draw each horizontal layer with gradually lighter color
        for i in range(self.num_layers):
            # Calculate position
            y_bottom = y_min + (i * layer_height)
            y_top = y_min + ((i + 1) * layer_height)
            
            # Interpolate color (progress from 0 to 1)
            progress = i / (self.num_layers - 1)
            r = r_start + (r_end - r_start) * progress
            g = g_start + (g_end - g_start) * progress
            b = b_start + (b_end - b_start) * progress
            
            glColor3f(r, g, b)
            
            # Draw rectangle for this layer
            glBegin(GL_QUADS)
            glVertex3f(-size, y_bottom, z_position)
            glVertex3f(size, y_bottom, z_position)
            glVertex3f(size, y_top, z_position)
            glVertex3f(-size, y_top, z_position)
            glEnd()
        
        glPopMatrix()
