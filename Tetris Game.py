from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
from enum import Enum
import sys
import math

# Game Variables
grid_width, grid_height = 10, 20
cell_size = 35  # Increased cell size
sidebar_width = 200  # Width of the sidebar
top_bar_height = 60  # Height of the top bar
grid = [[0] * grid_width for _ in range(grid_height)]
current_piece = None
next_piece = None
piece_x, piece_y = 4, 0
score = 0
game_over = False
paused = False
celebration_timer = 0

# Window dimensions
window_width = grid_width * cell_size + sidebar_width
window_height = grid_height * cell_size + top_bar_height

# Button dimensions
button_width = 160  # Made wider for sidebar
button_height = 30
pause_button = {'x': window_width - sidebar_width + 20, 'y': 200, 'text': "PAUSE"}
restart_button = {'x': window_width - sidebar_width + 20, 'y': 150, 'text': "RESTART"}

combo_effect_timer = 0
game_over_timer = 0

# Tetrimino Shapes
tetrimino_shapes = [
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1, 1]],          # I
    [[1, 1], [1, 1]],        # O
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]]   # J
]

def midpoint_line(x1, y1, x2, y2):
    """Midpoint line algorithm implementation"""
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x, y = x1, y1
    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1
    
    if dx > dy:
        err = dx / 2.0
        while x != x2:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y2:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    points.append((x, y))
    return points

class GameMode(Enum):
    EASY = 500    # Update interval in milliseconds (slower)
    MEDIUM = 300  # Medium speed
    HARD = 100    # Faster speed

current_mode = GameMode.MEDIUM
main_window = 0
menu_window = 0
highest_score = 0

def load_highest_score():
    """Load highest score from file"""
    global highest_score
    try:
        with open('highest_score.txt', 'r') as file:
            highest_score = int(file.read().strip())
    except:
        highest_score = 0
        save_highest_score()

def save_highest_score():
    """Save highest score to file"""
    with open('highest_score.txt', 'w') as file:
        file.write(str(highest_score))

def draw_menu_button(x, y, width, height, text):
    """Draw a button in the menu"""
    glColor3f(0.5, 0.5, 0.5)
    
    glBegin(GL_POINTS)
    points = []
    points.extend(midpoint_line(x, y, x + width, y))
    points.extend(midpoint_line(x, y, x, y + height))
    points.extend(midpoint_line(x + width, y, x + width, y + height))
    points.extend(midpoint_line(x, y + height, x + width, y + height))
    
    for px, py in points:
        glVertex2f(px, py)
    glEnd()
    
    glColor3f(1.0, 1.0, 1.0)
    text_x = x + (width - len(text) * 9) // 2  # Center text
    text_y = y + (height - 15) // 2
    glRasterPos2f(text_x, text_y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))

def display_menu():
    """Display function for menu window"""
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    menu_width = 400
    menu_height = 500
    gluOrtho2D(0, menu_width, 0, menu_height)
    
    # Draw title
    glColor3f(1.0, 1.0, 1.0)
    title = "TETRIS"
    glRasterPos2f((menu_width - len(title) * 15) // 2, menu_height - 50)
    for char in title:
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
    
    # Draw buttons
    button_width = 200
    button_height = 40
    start_y = menu_height - 150
    spacing = 60
    
    buttons = [
        "Start New Game",
        f"Easy Mode {'[Selected]' if current_mode == GameMode.EASY else ''}",
        f"Medium Mode {'[Selected]' if current_mode == GameMode.MEDIUM else ''}",
        f"Hard Mode {'[Selected]' if current_mode == GameMode.HARD else ''}",
        f"Highest Score: {highest_score}",
        "Exit"
    ]
    
    for i, text in enumerate(buttons):
        x = (menu_width - button_width) // 2
        y = start_y - i * spacing
        draw_menu_button(x, y, button_width, button_height, text)
    
    glutSwapBuffers()

def handle_menu_mouse(button, state, x, y):
    """Handle mouse clicks in menu"""
    global current_mode, menu_window, highest_score, main_window
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        menu_width = 400
        menu_height = 500
        button_width = 200
        button_height = 40
        start_y = menu_height - 150
        spacing = 60
        
        # Convert window coordinates
        y = menu_height - y
        button_x = (menu_width - button_width) // 2
        
        # Check which button was clicked
        for i in range(6):  # 6 buttons
            button_y = start_y - i * spacing
            if (button_x <= x <= button_x + button_width and
                button_y <= y <= button_y + button_height):
                if i == 0:  # Start New Game
                    glutDestroyWindow(menu_window)  # Destroy menu window first
                    create_game_window()  # Then create game window
                elif i == 1:  # Easy Mode
                    current_mode = GameMode.EASY
                elif i == 2:  # Medium Mode
                    current_mode = GameMode.MEDIUM
                elif i == 3:  # Hard Mode
                    current_mode = GameMode.HARD
                elif i == 5:  # Exit
                    glutDestroyWindow(menu_window)
                    sys.exit()
                
                glutPostRedisplay()
                break

def create_menu_window():
    """Create the menu window"""
    global menu_window
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(400, 500)
    glutInitWindowPosition(100, 100)
    menu_window = glutCreateWindow(b"Tetris Menu")
    
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glPointSize(2.0)
    
    glutDisplayFunc(display_menu)
    glutMouseFunc(handle_menu_mouse)

def create_game_window():
    """Create the game window"""
    global main_window
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    main_window = glutCreateWindow(b"Tetris")
    
    init()
    restart_game()
    
    # Register all callbacks for the game window
    glutDisplayFunc(display)
    glutKeyboardFunc(handle_keyboard)
    glutMouseFunc(handle_mouse)
    glutTimerFunc(current_mode.value, update, 0)

# Add a function to handle game window closing
def handle_game_close():
    """Handle game window closing"""
    global main_window, menu_window
    glutDestroyWindow(main_window)
    create_menu_window()


def draw_button(button):
    """Draw a button with text"""
    glColor3f(1.0, 1.0, 1.0)  # Changed to white for better visibility
    
    # Draw button rectangle outline
    glBegin(GL_POINTS)
    points = []
    x, y = button['x'], button['y']
    
    # Draw more points for thicker border
    for i in range(2):
        offset = i
        points.extend(midpoint_line(x-offset, y-offset, x + button_width+offset, y-offset))
        points.extend(midpoint_line(x-offset, y-offset, x-offset, y + button_height+offset))
        points.extend(midpoint_line(x + button_width+offset, y-offset, x + button_width+offset, y + button_height+offset))
        points.extend(midpoint_line(x-offset, y + button_height+offset, x + button_width+offset, y + button_height+offset))
    
    for px, py in points:
        glVertex2f(px, py)
    glEnd()
    
    # Draw button text
    glRasterPos2f(x + 10, y + button_height//2 + 5)  # Adjusted text position
    for char in button['text']:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))


def draw_block(x, y):
    """Draw a block using midpoint line algorithm"""
    screen_x = x * cell_size
    screen_y = window_height - ((y + 1) * cell_size + top_bar_height)  # Added +1 to fix offset
    
    glBegin(GL_POINTS)
    glColor3f(0.0, 1.0, 0.0)  # Green color
    
    points = []
    points.extend(midpoint_line(screen_x, screen_y, screen_x + cell_size, screen_y))
    points.extend(midpoint_line(screen_x, screen_y, screen_x, screen_y + cell_size))
    points.extend(midpoint_line(screen_x + cell_size, screen_y, screen_x + cell_size, screen_y + cell_size))
    points.extend(midpoint_line(screen_x, screen_y + cell_size, screen_x + cell_size, screen_y + cell_size))
    
    for px, py in points:
        glVertex2f(px, py)
    glEnd()

def draw_piece_preview(piece, start_x, start_y):
    """Draw piece preview in sidebar"""
    if piece:
        for row_idx, row in enumerate(reversed(piece)):  # Reverse rows for top-down display
            for col_idx, cell in enumerate(row):
                if cell:
                    x = start_x + col_idx * (cell_size * 0.8)
                    y = start_y + row_idx * (cell_size * 0.8)
                    
                    glBegin(GL_POINTS)
                    glColor3f(0.0, 1.0, 0.0)
                    
                    points = []
                    size = cell_size * 0.8
                    points.extend(midpoint_line(x, y, x + size, y))
                    points.extend(midpoint_line(x, y, x, y + size))
                    points.extend(midpoint_line(x + size, y, x + size, y + size))
                    points.extend(midpoint_line(x, y + size, x + size, y + size))
                    
                    for px, py in points:
                        glVertex2f(px, py)
                    glEnd()

def draw_grid():
    """Draw the game grid"""
    for y in range(grid_height):
        for x in range(grid_width):
            if grid[y][x] == 1:
                draw_block(x, y)

def draw_sidebar():
    """Draw the sidebar with next piece preview"""
    # Draw sidebar background border
    glBegin(GL_POINTS)
    glColor3f(1.0, 1.0, 1.0)  # Changed to white for better visibility
    x = window_width - sidebar_width
    points = []
    points.extend(midpoint_line(x, 0, x, window_height))
    for px, py in points:
        glVertex2f(px, py)
    glEnd()
    
    # Draw "Next Piece" text
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(window_width - sidebar_width + 20, window_height - 30)
    for char in f"Score: {score}":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
    
    glRasterPos2f(window_width - sidebar_width + 20, window_height - 60)
    for char in f"Highest Score: {highest_score}":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
    
    # Draw "Next Piece" text
    glRasterPos2f(window_width - sidebar_width + 20, window_height - 100)
    for char in "Next Piece:":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
    
    # Draw next piece preview
    preview_x = window_width - sidebar_width + 40
    preview_y = window_height - 180
    draw_piece_preview(next_piece, preview_x, preview_y)
    
    # Draw buttons
    draw_button(pause_button)
    draw_button(restart_button)

def clear_rows():
    """Clear completed rows and update score"""
    global grid, score, combo_effect_timer
    cleared_rows = 0
    y = grid_height - 1
    while y >= 0:
        if all(grid[y]):
            cleared_rows += 1
            del grid[y]
            grid.insert(0, [0] * grid_width)
        else:
            y -= 1
    
    # Add score and check for combo
    if cleared_rows >= 2:
        combo_effect_timer = 30  # Will show effect for 30 frames
        score += cleared_rows * 10  # Double points for combo
    else:
        score += cleared_rows * 5

def spawn_piece():
    """Spawn a new tetrimino piece at the top of the screen"""
    global current_piece, next_piece, piece_x, piece_y, game_over
    
    if next_piece is None:
        next_piece = random.choice(tetrimino_shapes)
    
    current_piece = next_piece
    next_piece = random.choice(tetrimino_shapes)
    piece_x = grid_width // 2 - len(current_piece[0]) // 2
    piece_y = -1  # Changed from 0 to -1 to start one row higher
    
    if not can_place_piece(current_piece, piece_x, piece_y):
        game_over = True

def can_place_piece(piece, x, y):
    """Check if piece can be placed at given position"""
    for row_idx, row in enumerate(piece):
        for col_idx, cell in enumerate(row):
            if cell:
                new_x, new_y = x + col_idx, y + row_idx
                # Check if piece has reached the bottom
                if new_y >= grid_height:
                    return False
                # Check if piece is within horizontal bounds and not colliding
                if (new_x < 0 or new_x >= grid_width or 
                    (new_y >= 0 and grid[new_y][new_x])):
                    return False
    return True

def place_piece():
    """Place the current piece on the grid"""
    global current_piece
    for row_idx, row in enumerate(current_piece):
        for col_idx, cell in enumerate(row):
            if cell and piece_y + row_idx >= 0:
                grid[piece_y + row_idx][piece_x + col_idx] = cell
    clear_rows()
    spawn_piece()

def move_piece(dx, dy):
    """Move the current piece"""
    global piece_x, piece_y
    if not paused and can_place_piece(current_piece, piece_x + dx, piece_y + dy):
        piece_x += dx
        piece_y += dy
        return True
    elif dy > 0:  # Piece has landed
        # Make sure the piece is placed at the bottom or on top of other pieces
        if piece_y + len(current_piece) <= grid_height:
            place_piece()
    return False


def rotate_piece():
    """Rotate the current piece"""
    global current_piece
    if not paused:
        rotated = list(zip(*reversed(current_piece)))
        if can_place_piece(rotated, piece_x, piece_y):
            current_piece = rotated

def draw_current_piece():
    """Draw the currently falling piece"""
    if current_piece:
        for row_idx, row in enumerate(current_piece):
            for col_idx, cell in enumerate(row):
                if cell:
                    draw_block(piece_x + col_idx, piece_y + row_idx)

def restart_game():
    """Restart the game"""
    global grid, score, game_over, paused, current_piece, next_piece
    grid = [[0] * grid_width for _ in range(grid_height)]
    score = 0
    game_over = False
    paused = False
    current_piece = None
    next_piece = None
    spawn_piece()
    load_highest_score()  # Load highest score when game restarts

def toggle_pause():
    """Toggle game pause state"""
    global paused
    if not game_over:
        paused = not paused

def handle_mouse(button, state, x, y):
    """Handle mouse clicks"""
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Convert window coordinates
        y = window_height - y
        
        # Check pause button
        if (pause_button['x'] <= x <= pause_button['x'] + button_width and
            pause_button['y'] <= y <= pause_button['y'] + button_height):
            toggle_pause()
        
        # Check restart button
        if (restart_button['x'] <= x <= restart_button['x'] + button_width and
            restart_button['y'] <= y <= restart_button['y'] + button_height):
            restart_game()
        
        glutPostRedisplay()

def handle_keyboard(key, x, y):
    """Handle keyboard input"""
    if game_over:
        return
    
    if key == b' ':  # Space bar for pause
        toggle_pause()
    elif key == b'p':  # 'p' for restart
        restart_game()
    
    if not paused:
        if key == b'a':
            move_piece(-1, 0)
        elif key == b'd':
            move_piece(1, 0)
        elif key == b's':
            move_piece(0, 1)
        elif key == b'w':
            rotate_piece()
    
    glutPostRedisplay()


def update(value):
    """Game update function"""
    global highest_score, combo_effect_timer, game_over_timer, celebration_timer
    
    if not game_over and not paused:
        move_piece(0, 1)
        
        # Update combo effect timer
        if combo_effect_timer > 0:
            combo_effect_timer -= 1
            
        # Update celebration effect timer
        if celebration_timer > 0:
            celebration_timer -= 1
    
    if game_over:
        # Game over timer logic
        game_over_timer += 1
        
        # After 3 seconds (180 frames at 60 FPS)
        if game_over_timer >= 20:
            game_over_timer = 0
            if score > highest_score:
                highest_score = score
                save_highest_score()  # Save new highest score
            handle_game_close()
            return
    
    glutPostRedisplay()
    glutTimerFunc(current_mode.value, update, 0)

def draw_combo_effect():
    """Draw combo blast effect"""
    if combo_effect_timer > 0:
        # Create a pulsing effect
        alpha = combo_effect_timer / 30.0  # Fade out over time
        glColor4f(1.0, 1.0, 0.0, alpha)
        
        center_x = (grid_width * cell_size) / 2
        center_y = window_height / 2
        radius = (30 - combo_effect_timer) * 5  # Expanding radius
        
        # Draw expanding circle using points
        glBegin(GL_POINTS)
        for angle in range(0, 360, 5):
            x = center_x + radius * math.cos(math.radians(angle))
            y = center_y + radius * math.sin(math.radians(angle))
            glVertex2f(x, y)
        glEnd()

def draw_celebration_effect():
    """Draw celebration effect for high score"""
    glPointSize(2.0)
    # Draw multiple particle effects
    for i in range(20):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(50, 150)
        x = window_width // 2 + radius * math.cos(angle)
        y = window_height // 2 + radius * math.sin(angle)
        
        # Random colors for particles
        glColor3f(random.uniform(0.5, 1.0), 
                 random.uniform(0.5, 1.0), 
                 random.uniform(0.5, 1.0))
        
        glBegin(GL_POINTS)
        for j in range(10):
            particle_x = x + random.uniform(-10, 10)
            particle_y = y + random.uniform(-10, 10)
            glVertex2f(particle_x, particle_y)
        glEnd()


def display():
    """Display function"""
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    
    # Draw game elements
    draw_grid()
    draw_current_piece()
    draw_sidebar()
    
    # Draw score at the top
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(window_width - sidebar_width + 20, window_height - 30)
    for char in f"Score: {score}":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
    
    # Draw high score
    glRasterPos2f(window_width - sidebar_width + 20, window_height - 60)
    for char in f"Highest Score: {highest_score}":
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))

    if score > highest_score and not game_over:
        # Set celebration timer
        global celebration_timer
        if celebration_timer <= 0:
            celebration_timer = 20  # 2 seconds
        
        # Yellow glow effect
        glColor3f(1.0, 1.0, 0.0)
        glPointSize(3.0)
        glRasterPos2f(window_width - sidebar_width + 20, window_height - 90)
        for char in "New High Score!":
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        glPointSize(2.0)
        
        # Draw celebration effect if timer is active
        if celebration_timer > 0:
            draw_celebration_effect()
    
    if game_over:
        # Don't update highest_score here, wait until game actually ends
        temp_highest = highest_score  # Use current highest_score for comparison
        
        if score > temp_highest:
            # Draw celebration effect
            draw_celebration_effect()
            
            # Draw congratulations message with special styling
            glColor3f(1.0, 1.0, 0.0)  # Yellow color
            messages = [
                "GAME OVER",
                "Congratulations!",
                f"New High Score: {score}!",
                f"Previous Best: {temp_highest}"
            ]
            y_pos = window_height // 2 + 50
            
            for i, msg in enumerate(messages):
                text_width = len(msg) * (15 if i == 0 else 9)  # Bigger font for GAME OVER
                x_pos = (grid_width * cell_size - text_width) // 2
                
                if i == 0:  # GAME OVER with special effect
                    # Draw glowing outline
                    glPointSize(3.0)
                    glColor3f(1.0, 0.0, 0.0)  # Red outline
                    glRasterPos2f(x_pos, y_pos)
                    for char in msg:
                        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
                    glPointSize(2.0)
                else:  # Other messages with different styling
                    if i == 1:  # Congratulations
                        glColor3f(1.0, 1.0, 0.0)  # Yellow
                    else:  # Score messages
                        glColor3f(0.0, 1.0, 0.0)  # Green
                    
                    glRasterPos2f(x_pos, y_pos)
                    for char in msg:
                        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
                
                y_pos -= 30
        else:
            # Regular game over message with styling
            messages = [
                "GAME OVER",
                f"Your Score: {score}",
                f"Highest Score: {temp_highest}"
            ]
            y_pos = window_height // 2 + 40
            
            for i, msg in enumerate(messages):
                text_width = len(msg) * (15 if i == 0 else 9)
                x_pos = (grid_width * cell_size - text_width) // 2
                
                if i == 0:  # GAME OVER with special effect
                    glPointSize(3.0)
                    glColor3f(1.0, 0.0, 0.0)
                    glRasterPos2f(x_pos, y_pos)
                    for char in msg:
                        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
                    glPointSize(2.0)
                else:
                    glColor3f(1.0, 1.0, 1.0)
                    glRasterPos2f(x_pos, y_pos)
                    for char in msg:
                        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
                
                y_pos -= 30
    
    elif paused:
        glColor3f(1.0, 1.0, 0.0)
        text = "PAUSED"
        text_width = len(text) * 15
        x_pos = (grid_width * cell_size - text_width) // 2
        glRasterPos2f(x_pos, window_height // 2)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
    
    if combo_effect_timer > 0:
        draw_combo_effect()
    
    glutSwapBuffers()

def init():
    """Initialize OpenGL settings"""
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glPointSize(2.0)

def main():
    """Main function"""
    try:
        load_highest_score()  # Load highest score when game starts
        create_menu_window()
        glutMainLoop()
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()