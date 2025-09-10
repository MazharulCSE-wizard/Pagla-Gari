from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time
import math
import os

cam_dist = 300
cam_height = 150
fovY = 60 
GRID_LENGTH = 2000

lane_positions = [-100, 0, 100]
car_lane = 1  # 1 mane middle lane e
car_x = lane_positions[car_lane]
initial_speed = 300.0
speed = initial_speed
speed_increment = 5.0 
coins = 0
distance = 0.0
fuel = 100.0
fuel_max = 100.0
fuel_decrease_rate = 5.0  
paused = False
game_over = False
objects = []  # shob objects stored thakbe 
active_powerups = {}  # {powerup : variable}
powerup_duration = 15.0  
ghost_distance = 1000.0 


spawn_interval = 300.0  # Distance units between spawns
next_spawn_distance = 0.0
visible_distance = 2000.0  # Distance AHEAD -> jekhane objects create hoise

fuel_interval = 1000.0  # Minimum distance for fuel spawns
powerup_interval = 2500.0  # Minimum distance for power-up spawns

# Next guaranteed spawn distances (guarantee at least one at these distances)
next_fuel_spawn_distance = fuel_interval
next_powerup_spawn_distance = powerup_interval

last_time = time.time()

wheel_angle = 0.0

road_offset = 0.0

# High score stored rakhar jonne
high_score_file = "highscore.txt"
if os.path.exists(high_score_file):
    with open(high_score_file, "r") as f:
        high_score = int(f.read().strip() or 0)
else:
    high_score = 0

# Random seed
random.seed(423)

def get_car_x():
    return lane_positions[car_lane]

def reset_game():
    global car_lane, car_x, speed, coins, distance, fuel, paused, game_over, objects, active_powerups, next_spawn_distance, wheel_angle, road_offset, next_fuel_spawn_distance, next_powerup_spawn_distance
    car_lane = 1
    car_x = get_car_x()
    speed = initial_speed
    coins = 0
    distance = 0.0
    fuel = fuel_max
    paused = False
    game_over = False
    objects = []
    active_powerups = {}
    next_spawn_distance = 0.0
    wheel_angle = 0.0
    road_offset = 0.0
    next_fuel_spawn_distance = fuel_interval
    next_powerup_spawn_distance = powerup_interval



def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_car():
    glPushMatrix()
    glTranslatef(car_x, 0, 0)
    # Body
    glColor3f(0.8, 0.2, 0.2)
    glPushMatrix()
    glScalef(0.8, 1.5, 0.4)
    glutSolidCube(50)
    glPopMatrix()
    # Cabin
    glColor3f(0.2, 0.2, 0.8)
    glPushMatrix()
    glTranslatef(0, 20, 20)
    glScalef(0.6, 0.8, 0.4)
    glutSolidCube(50)
    glPopMatrix()
    # Wheels
    glColor3f(0, 0, 0)
    # Left back
    glPushMatrix()
    glTranslatef(-25, -40, -15)
    glRotatef(90, 0, 1, 0)
    glRotatef(wheel_angle, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 15, 15, 10, 10, 10)
    glPopMatrix()
    # Right back
    glPushMatrix()
    glTranslatef(25, -40, -15)
    glRotatef(90, 0, 1, 0)
    glRotatef(wheel_angle, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 15, 15, 10, 10, 10)
    glPopMatrix()
    # Left front
    glPushMatrix()
    glTranslatef(-25, 40, -15)
    glRotatef(90, 0, 1, 0)
    glRotatef(wheel_angle, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 15, 15, 10, 10, 10)
    glPopMatrix()
    # Right front
    glPushMatrix()
    glTranslatef(25, 40, -15)
    glRotatef(90, 0, 1, 0)
    glRotatef(wheel_angle, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 15, 15, 10, 10, 10)
    glPopMatrix()
    glPopMatrix()

def draw_object(obj):
    glPushMatrix()
    glTranslatef(obj['x'], obj['y'], 0)
    rotation = math.degrees(time.time() * 2) % 360  # Simple rotation for cool effect UwU
    if obj['type'] == 'obstacle':
        glColor3f(0.5, 0.5, 0.5)
        glutSolidCube(60)
    elif obj['type'] == 'coin':
        glColor3f(1, 1, 0)
        glRotatef(rotation, 0, 1, 0)
        glutSolidSphere(20, 10, 10)
    elif obj['type'] == 'fuel':
        # Reverted to original fuel shape
        glColor3f(0, 1, 0)
        gluCylinder(gluNewQuadric(), 15, 15, 40, 10, 10)
        glPushMatrix()
        glTranslatef(0, 0, 0)
        gluDisk(gluNewQuadric(), 0, 15, 10, 10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 0, 40)
        gluDisk(gluNewQuadric(), 0, 15, 10, 10)
        glPopMatrix()
    elif obj['type'] == 'doubler':
        glColor3f(0, 0, 1)
        glRotatef(rotation, 0, 1, 0)
        glutSolidSphere(25, 10, 10)
    elif obj['type'] == 'reducer':
        glColor3f(1, 0, 0)
        gluCylinder(gluNewQuadric(), 20, 0, 40, 10, 10)
    elif obj['type'] == 'ghost':
        glColor3f(1, 1, 1)
        glRotatef(rotation, 0, 1, 0)
        glutSolidSphere(20)
    glPopMatrix()

def draw_road():
    glBegin(GL_QUADS)
    glColor3f(0.3, 0.3, 0.3)
    glVertex3f(-150, -GRID_LENGTH, 0)
    glVertex3f(150, -GRID_LENGTH, 0)
    glVertex3f(150, GRID_LENGTH * 2, 0)
    glVertex3f(-150, GRID_LENGTH * 2, 0)
    glEnd()
    # Lane lines scrolling
    glLineWidth(5)
    glBegin(GL_LINES)
    glColor3f(1, 1, 1)
    start_y = -GRID_LENGTH - road_offset
    while start_y < GRID_LENGTH * 2:
        # Left lane line
        glVertex3f(-50, start_y, 0.1)
        glVertex3f(-50, start_y + 50, 0.1)
        # Right lane line
        glVertex3f(50, start_y, 0.1)
        glVertex3f(50, start_y + 50, 0.1)
        start_y += 100
    glEnd()

def keyboardListener(key, x, y):
    global paused, game_over, car_lane, car_x
    
    if key == b'a' or key == b'A':
        if not game_over and not paused:
            car_lane = max(0, car_lane - 1)
            car_x = get_car_x()
    elif key == b'd' or key == b'D':
        if not game_over and not paused:
            car_lane = min(2, car_lane + 1)
            car_x = get_car_x()
    elif key == b'r' or key == b'R':
        if game_over:
            reset_game()
    elif key == b'\x1b':  # ESC
        if not game_over:
            paused = not paused

def specialKeyListener(key, x, y):
    global car_lane, car_x
    
    if game_over:
        return
    
    if key == GLUT_KEY_LEFT:
        car_lane = max(0, car_lane - 1)
        car_x = get_car_x()
    elif key == GLUT_KEY_RIGHT:
        car_lane = min(2, car_lane + 1)
        car_x = get_car_x()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(car_x, -cam_dist, cam_height,  # Camera position
              car_x, 100, 0,  # Look-at point (ahead of car)
              0, 0, 1)  # Up vector




def main():
    global last_time
    last_time = time.time()
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"Pagla Gari")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
