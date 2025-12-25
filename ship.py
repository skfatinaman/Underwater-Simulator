from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math

class Ship:
    def __init__(self):
        self.quad = gluNewQuadric()

    def draw(self):
        glPushMatrix()
        glTranslatef(0, 2, 0) # Position near center
        glScalef(2, 2, 2)
        
        # Part 1: Stern (Back) - Tilted back
        glPushMatrix()
        glTranslatef(0, 0, 3)
        glRotatef(-20, 1, 0, 0) # Tilt back
        glRotatef(15, 0, 0, 1) # Tilt side
        
        glColor3f(0.4, 0.25, 0.1) # Wood
        # Hull Box
        glPushMatrix()
        glScalef(2.0, 2.0, 2.5)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Upper Deck (Triangle top)
        glPushMatrix()
        glTranslatef(0, 1.0, 0)
        glBegin(GL_TRIANGLES)
        # Simple roof/deck structure
        glVertex3f(-1, 0, 1); glVertex3f(1, 0, 1); glVertex3f(0, 1, 0)
        glVertex3f(-1, 0, -1); glVertex3f(1, 0, -1); glVertex3f(0, 1, 0)
        glEnd()
        glPopMatrix()
        glPopMatrix()
        
        # Part 2: Bow (Front) - Broken off and tilted forward
        glPushMatrix()
        glTranslatef(0, -1, -3)
        glRotatef(30, 1, 0, 0) # Tilt forward
        glRotatef(-10, 0, 0, 1) # Tilt side
        
        # Hull Box
        glPushMatrix()
        glScalef(1.8, 1.8, 2.5)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Pointy front (Pyramid)
        glPushMatrix()
        glTranslatef(0, 0, -1.25)
        glBegin(GL_TRIANGLES)
        # Sides meeting at point
        glVertex3f(0.9, 0.9, 0); glVertex3f(-0.9, 0.9, 0); glVertex3f(0, 0, -2)
        glVertex3f(0.9, -0.9, 0); glVertex3f(-0.9, -0.9, 0); glVertex3f(0, 0, -2)
        glVertex3f(0.9, 0.9, 0); glVertex3f(0.9, -0.9, 0); glVertex3f(0, 0, -2)
        glVertex3f(-0.9, 0.9, 0); glVertex3f(-0.9, -0.9, 0); glVertex3f(0, 0, -2)
        glEnd()
        glPopMatrix()
        glPopMatrix()
        
        # Broken Mast (Long Cylinder)
        glColor3f(0.3, 0.15, 0.05)
        glPushMatrix()
        glTranslatef(2, 0, 0) # Lying on side
        glRotatef(90, 0, 1, 0)
        glRotatef(80, 0, 0, 1) # Almost flat
        gluCylinder(self.quad, 0.15, 0.1, 8, 8, 1) # Long pole
        
        # Cross beam
        glPushMatrix()
        glTranslatef(0, 0, 5)
        glRotatef(90, 1, 0, 0)
        glTranslatef(0, 0, -1.5)
        gluCylinder(self.quad, 0.1, 0.08, 3, 6, 1)
        glPopMatrix()
        
        glPopMatrix()
        
        # Moss (Green patches)
        glColor3f(0.1, 0.5, 0.1)
        glBegin(GL_TRIANGLES)
        for i in range(15):
            mx = math.sin(i * 3) * 3
            mz = math.cos(i * 5) * 5
            my = abs(math.sin(i * 7)) * 1.5
            glVertex3f(mx, my, mz)
            glVertex3f(mx+0.5, my, mz+0.2)
            glVertex3f(mx-0.2, my+0.5, mz-0.2)
        glEnd()
        
        glPopMatrix()
