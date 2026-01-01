from OpenGL.GL import *
from OpenGL.GLUT import *

class FirstPersonView:
    """Handles the first-person camera and arm rendering."""
    
    def draw(self):
        """Draw camera model in first person view (blocky hand holding camera)."""
        glPushMatrix()
        
        # Position in bottom-right corner of view (camera shifted left of hand)
        glTranslatef(0.5, -0.35, -1.5)  # Hand stays in place
        glRotatef(-15, 0, 1, 0)  # Slight angle for natural look
        glRotatef(-8, 1, 0, 0)
        glRotatef(5, 0, 0, 1)
        
        # ARM - One simple rectangle coming from bottom
        glPushMatrix()
        glColor3f(0.88, 0.68, 0.58)  # Skin tone
        glBegin(GL_QUADS)
        # Front face
        glVertex3f(-0.05, -0.8, -0.05)
        glVertex3f(0.05, -0.8, -0.05)
        glVertex3f(0.05, 0.05, -0.05)
        glVertex3f(-0.05, 0.05, -0.05)
        # Back face
        glVertex3f(-0.05, -0.8, 0.05)
        glVertex3f(0.05, -0.8, 0.05)
        glVertex3f(0.05, 0.05, 0.05)
        glVertex3f(-0.05, 0.05, 0.05)
        # Left face
        glVertex3f(-0.05, -0.8, -0.05)
        glVertex3f(-0.05, -0.8, 0.05)
        glVertex3f(-0.05, 0.05, 0.05)
        glVertex3f(-0.05, 0.05, -0.05)
        # Right face
        glVertex3f(0.05, -0.8, -0.05)
        glVertex3f(0.05, -0.8, 0.05)
        glVertex3f(0.05, 0.05, 0.05)
        glVertex3f(0.05, 0.05, -0.05)
        glEnd()
        glPopMatrix()
        
        # Camera body (main rectangular body)
        glPushMatrix()
        glTranslatef(-0.1, 0.02, 0.0)  # Shifted left from hand
        
        # Main camera body
        glColor3f(0.35, 0.35, 0.4)
        glScalef(0.65, 0.45, 0.5)
        glutSolidCube(0.35)
        glPopMatrix()
        
        # Top section (viewfinder hump)
        glPushMatrix()
        glTranslatef(-0.12, 0.1, 0.0)  # Shifted left
        glColor3f(0.3, 0.3, 0.35)
        glScalef(0.5, 0.25, 0.42)
        glutSolidCube(0.3)
        glPopMatrix()
        
        # Lens housing (protruding section)
        glPushMatrix()
        glTranslatef(-0.02, 0.02, 0.0)  # Shifted left
        glColor3f(0.25, 0.25, 0.3)
        glScalef(0.35, 0.35, 0.35)
        glutSolidCube(0.35)
        glPopMatrix()
        
        # Lens glass (dark cube instead of sphere)
        glPushMatrix()
        glTranslatef(0.04, 0.02, 0.0)  # Shifted left
        glColor3f(0.05, 0.05, 0.1)
        glScalef(0.13, 0.13, 0.13)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Lens rim (metallic cube frame instead of torus)
        glPushMatrix()
        glTranslatef(0.04, 0.02, 0.0)  # Shifted left
        glColor3f(0.7, 0.7, 0.75)
        glScalef(0.15, 0.15, 0.08)
        glutWireCube(1.0)
        glPopMatrix()
        
        # Shutter button (red cube instead of cylinder)
        glPushMatrix()
        glTranslatef(-0.13, 0.12, 0.05)  # Shifted left
        glColor3f(0.9, 0.2, 0.15)
        glScalef(0.03, 0.03, 0.03)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Flash (small silver rectangle)
        glPushMatrix()
        glTranslatef(-0.07, 0.1, 0.07)  # Shifted left
        glColor3f(0.9, 0.9, 0.95)
        glScalef(0.2, 0.15, 0.15)
        glutSolidCube(0.15)
        glPopMatrix()
        
        # Grip texture (small dark rectangle on front)
        glPushMatrix()
        glTranslatef(-0.17, 0.0, 0.09)  # Shifted left
        glColor3f(0.15, 0.15, 0.2)
        glScalef(0.3, 0.35, 0.08)
        glutSolidCube(0.25)
        glPopMatrix()
        
        glPopMatrix()
