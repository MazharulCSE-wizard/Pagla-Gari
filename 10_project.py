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


def spawn_objects(spawn_dist):
    
    global next_fuel_spawn_distance, next_powerup_spawn_distance
    types = ['nothing', 'coin', 'obstacle']
    powerups = ['doubler', 'reducer', 'ghost']
    spawned_types = []

    # small random offset jate objects same place e spawn na kore
    y_offset = random.uniform(-50, 50)
    spawn_y = visible_distance + y_offset

    # Determine forced lanes for guaranteed spawns
    fuel_lane = None
    powerup_lane = None
    forced_powerup_type = None

    if spawn_dist >= next_fuel_spawn_distance:
        fuel_lane = random.randrange(3)
        # advance next guaranteed fuel spawn
        next_fuel_spawn_distance += fuel_interval

    if spawn_dist >= next_powerup_spawn_distance:
        powerup_lane = random.randrange(3)
        forced_powerup_type = random.choice(powerups)
        
        # if collides with fuel_lane -> put powerup in different lane
        if fuel_lane is not None and powerup_lane == fuel_lane:
            choices = [l for l in range(3) if l != fuel_lane]
            powerup_lane = random.choice(choices)
        next_powerup_spawn_distance += powerup_interval

    # lanes
    for lane in range(3):
        if lane == fuel_lane:
            obj_type = 'fuel'
        elif lane == powerup_lane:
            obj_type = forced_powerup_type
        else:
            # avoid too many obstacles in a row
            if len(spawned_types) >= 2 and spawned_types[-1] == 'obstacle' and spawned_types[-2] == 'obstacle':
                obj_type = random.choice(['nothing', 'coin'])
            elif lane > 0 and 'obstacle' in spawned_types:
                obj_type = random.choice(['nothing', 'coin'])
            else:
                r = random.random()
                if r < 0.6:
                    obj_type = 'coin'
                elif r < 0.9:
                    obj_type = 'obstacle'
                else:
                    obj_type = 'nothing'

        if obj_type != 'nothing':
            obj_x = lane_positions[lane]
            objects.append({'type': obj_type, 'x': obj_x, 'y': spawn_y})
            spawned_types.append(obj_type)


def update_game(dt):
    global distance, fuel, game_over, speed, coins, high_score, next_spawn_distance, wheel_angle, road_offset
    if paused or game_over:
        return

    distance += speed * dt
    fuel -= fuel_decrease_rate * dt
    if fuel <= 0:
        fuel = 0
        game_over = True

    # Update wheel angle for rotation
    wheel_angle += speed * dt * 2  # Adjust factor for rotation speed

    # Update road offset for scrolling lines
    road_offset = (road_offset + speed * dt) % 100

    # Update active powerups
    if 'doubler' in active_powerups:
        active_powerups['doubler'] -= dt
        if active_powerups['doubler'] <= 0:
            del active_powerups['doubler']

    if 'reducer' in active_powerups:
        active_powerups['reducer'] -= dt
        if active_powerups['reducer'] <= 0:
            del active_powerups['reducer']
        else:
            speed = initial_speed * 0.5  # speed reduce korbe
    else:
        # compute normal speed from coins
        speed = initial_speed + coins * speed_increment

    if 'ghost' in active_powerups:
        active_powerups['ghost'] -= speed * dt
        if active_powerups['ghost'] <= 0:
            del active_powerups['ghost']

    # Move objects towards car
    for obj in objects:
        obj['y'] -= speed * dt

    # Spawn new objects if needed (based on distance travelled)
    while distance >= next_spawn_distance:
        spawn_objects(next_spawn_distance)
        next_spawn_distance += spawn_interval

    # Remove off-screen objects
    objects[:] = [obj for obj in objects if obj['y'] > -200]

    # Check collisions
    for obj in objects[:]:
        if abs(obj['y']) < 50 and abs(obj['x'] - car_x) < 1.0: 
            if obj['type'] == 'obstacle':
                if 'ghost' not in active_powerups:
                    game_over = True
                objects.remove(obj)
            elif obj['type'] == 'coin':
                coin_value = 2 if 'doubler' in active_powerups else 1
                coins += coin_value
                objects.remove(obj)
            elif obj['type'] == 'fuel':
                # refill fuel, cap to max
                fuel = min(fuel + 20, fuel_max)
                objects.remove(obj)
            elif obj['type'] == 'doubler':
                active_powerups['doubler'] = powerup_duration
                objects.remove(obj)
            elif obj['type'] == 'reducer':
                active_powerups['reducer'] = powerup_duration
                objects.remove(obj)
            elif obj['type'] == 'ghost':
                active_powerups['ghost'] = ghost_distance
                objects.remove(obj)

    if game_over:
        current_score = coins
        high_score = max(high_score, current_score)
        with open(high_score_file, "w") as f:
            f.write(str(high_score))



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
        glutSolidSphere(25, 16, 16)
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

def idle():
    global last_time
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    update_game(dt)
    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()

    draw_road()
    draw_car()
    for obj in objects:
        draw_object(obj)

    # HUD
    scaled_distance = int(distance / 10)
    draw_text(10, 750, f"Coins: {coins}")
    draw_text(10, 730, f"Distance: {scaled_distance}")
    draw_text(10, 710, f"Fuel: {int(fuel)}")
    draw_text(10, 690, f"Speed: {int(speed)}")
    
    draw_text(450, 750, "PAGLA GARI", font=GLUT_BITMAP_HELVETICA_18)

    if paused:
        draw_text(400, 400, "Pause")

    if game_over:
        draw_text(450, 450, "Game Over")
        draw_text(450, 420, f"Coins: {coins}")
        draw_text(450, 390, f"Distance: {scaled_distance}")
        draw_text(450, 360, f"High Score: {high_score}")

    glutSwapBuffers()

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




