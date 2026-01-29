# initialising libraries
import copy
import pygame
from board import boards
import math 
import spritesheet
from collections import deque
import leaderboard


#initialising key variables
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

from audio_manager import AudioManager
audio = AudioManager()


pygame.init()
WIDTH = 900
HEIGHT = 950
screen = pygame.display.set_mode([WIDTH, HEIGHT])
timer = pygame.time.Clock()
fps = 60

conslives = 3

#level variables
LEVELS = []
def get_levels():
    for i in range(len(boards)):
        LEVELS.append(boards[i])
    return LEVELS
LEVELS = get_levels()
current_level = 0
level_colour = ["blue","green","red"]
def get_colour(lvl):
    for i in range(len(LEVELS)):
        return level_colour[lvl % len(level_colour)]

# Menu system
MENU_MAIN = "main"
MENU_DIFFICULTY = "difficulty"
MENU_CONTROLS = "controls"
MENU_LEADERBOARD = "leaderboard"
game_over_sfx_played = False
win_sfx_played = False

#leaderboard settings
enter_name_active = False
name_buffer = ""
score_submitted = False

run_start_ticks = None
final_time_seconds = 0.0

new_highscore_flag = False
new_highscore_ticks = 0  # to time the message




cover_active = True           # start with cover menu on
menu_screen = MENU_MAIN
menu_index = 0

difficulty_names = ["EASY", "NORMAL", "HARD"]
difficulty_index = 1          # default NORMAL

# simple placeholder leaderboard data
leaderboard_rows = leaderboard.get_menu_rows()


#Tile size calculations
TILE_H = (HEIGHT - 50) // 32
TILE_W = WIDTH // 30

# Pick the tile you want dead ghosts to reach.
BOX_TARGET_TILE = (16, 15)  # (row, col) 



#Font settings
font = pygame.font.Font('freesansbold.ttf', 20)
pygame.display.set_caption('PACMANY')
big_font = pygame.font.Font('freesansbold.ttf', 50)


#Variablees for maze drawing
level = copy.deepcopy(LEVELS[current_level])
colour = "blue"
PI = math.pi
flicker_counter = 0
flicker = False

#Used for movement/ direction logic/ collsions
#r, l, u, d
turns_allowed = [False, False,False,False]
direction_command = 0
moving  = False

#entities speed
ghost_speeds  = [2,2,2,2]
player_speed = 2


#Used for sprit sheet logic
sprite_sheet_image = pygame.image.load('Assets/spritesheet.png').convert_alpha()
sprite_sheet = spritesheet.SpriteSheet(sprite_sheet_image)

pacman_base = sprite_sheet.get_image(4,0, 32,32, 1.40625,"magenta")
pacman_right = sprite_sheet.get_image(1,0, 32,32, 1.40625,"magenta")
pacman_right2 = sprite_sheet.get_image(1,1, 32,32, 1.40625,"magenta")

player_images = [pacman_right,pacman_base,pacman_right,pacman_right2]
player_x = 450 
player_y = 663
direction = 0
counter = 0

# Variables for scoring
score = 0

#Draw ui sections
lives = conslives 

#PowerUps
powerup = False
power_counter = 0
powerup_duration_frames = 600          
powerup_flash_frames = 3 * 60          # last 3 seconds = 180 frames
flash_toggle_rate = 10                 # change every 10 frames (~6 flashes/sec)


#Startup delay variables
moving = False

#Eaten ghosts tracker
eaten_ghosts = [False, False,False,False]

# Ghost positions
blinky_x = 440#56
blinky_y = 388#58
blinky_direction = 0
inky_x = 440
inky_y = 388
inky_direction = 2
pinky_x = 440
pinky_y = 438
pinky_direction = 2
clyde_x = 440
clyde_y = 438
clyde_direction = 2

#set ghost targets to player start position
targets = [(player_x, player_y),(player_x, player_y),(player_x, player_y),(player_x, player_y)]
#Ghost states
blinky_dead = False
inky_dead = False
clyde_dead = False
pinky_dead = False
blinky_box = False
inky_box = False
clyde_box = False
pinky_box = False

#game won/ over flags
game_over = False
game_won = False


# Ghost sprite loading function
def load_ghosts(sprite_sheet):
    ghost_data = {}
    colors = ["red", "pink", "blue", "yellow", "dark"]
    for i, color in enumerate(colors):
        ghost_data[color] = {
            "up": sprite_sheet.get_image(i, 2, 32, 32, 1.40625, "magenta"),
            "down": sprite_sheet.get_image(i, 3, 32, 32, 1.40625, "magenta"),
            "left": sprite_sheet.get_image(i, 4, 32, 32, 1.40625, "magenta"),
            "right": sprite_sheet.get_image(i, 5, 32, 32, 1.40625, "magenta"),
        }
    return ghost_data
ghost_sprites = load_ghosts(sprite_sheet)


def get_ghost_facing_image(color, direction):
    # converts your numeric direction to the dict key
    dir_key = {0: "right", 1: "left", 2: "up", 3: "down"}[direction]
    return ghost_sprites[color][dir_key]


def load_dead_ghosts(sprite_sheet):
    return {
        "up": sprite_sheet.get_image(4, 2, 32, 32, 1.40625, "magenta"),
        "down": sprite_sheet.get_image(4, 3, 32, 32, 1.40625, "magenta"),
        "left": sprite_sheet.get_image(4, 4, 32, 32, 1.40625, "magenta"),
        "right": sprite_sheet.get_image(4, 5, 32, 32, 1.40625, "magenta"),
    }
ghost_dead_sprites = load_dead_ghosts(sprite_sheet)

ghost_spooked =sprite_sheet.get_image(5, 3,32,32,1.40625,"magenta")
ghost_spooked2 =sprite_sheet.get_image(5, 2,32,32,1.40625,"magenta")
ghost_dead =sprite_sheet.get_image(5, 2,32,32,1.40625,"magenta")

# Utility functions for ghost pathfinding
def pix_to_tile(cx, cy):
    row = int(cy // TILE_H)
    col = int(cx // TILE_W)
    return row, col

def is_walkable_for_dead(val):
    # walls are 3 to 8 in map, walkable are 0,1,2
    # dead ghosts can also go through gate (9) to re-enter box
    return val < 3 or val == 9

def build_dead_distance_map(level, target_tile):
    rows = len(level)
    cols = len(level[0])
    dist = [[-1 for _ in range(cols)] for _ in range(rows)]

    tr, tc = target_tile
    q = deque()
    dist[tr][tc] = 0
    q.append((tr, tc))

    while q:
        r, c = q.popleft()
        for dr, dc in ((0,1),(0,-1),(1,0),(-1,0)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == -1:
                if is_walkable_for_dead(level[nr][nc]):
                    dist[nr][nc] = dist[r][c] + 1
                    q.append((nr, nc))
    return dist

DEAD_DIST = build_dead_distance_map(level, BOX_TARGET_TILE)

def apply_difficulty(difficulty_index):
    """
    Applies difficulty by changing speeds (you can expand this later).
    Called when leaving the difficulty screen or starting the game.
    """
    global player_speed, ghost_speeds

    # Base presets (tweak to taste)
    if difficulty_index == 0:       # EASY
        player_speed = 2
        ghost_speeds = [1, 1, 1, 1]
    elif difficulty_index == 1:     # NORMAL
        player_speed = 2
        ghost_speeds = [2, 2, 2, 2]
    else:                            # HARD
        player_speed = 2
        ghost_speeds = [5,5,5,5]

    return ghost_speeds
def draw_cover_overlay():
    """Dark full-screen overlay."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))  # RGBA (alpha=220)
    screen.blit(overlay, (0, 0))


def draw_menu_text_center(text, y, is_selected=False, size="small"):
    color = "yellow" if is_selected else "white"
    f = big_font if size == "big" else font
    surf = f.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=(WIDTH // 2, y)))


def draw_cover_menu():
    draw_cover_overlay()

        # title
    draw_menu_text_center("PACMANY", 180, size="big")

        # Only show difficulty status on relevant screens
    if menu_screen in (MENU_MAIN, MENU_DIFFICULTY):
        draw_menu_text_center(
            f"DIFFICULTY: {difficulty_names[difficulty_index]}",
            250,
            size="small"
        )

    if menu_screen == MENU_MAIN:
        options = ["START GAME", "DIFFICULTY", "LEADERBOARD", "CONTROLS", "QUIT"]
        y0 = 340
        gap = 45
        for i, opt in enumerate(options):
            draw_menu_text_center(opt, y0 + i * gap, is_selected=(i == menu_index))
        draw_menu_text_center("Use UP/DOWN to choose, ENTER to select", 750)

    elif menu_screen == MENU_DIFFICULTY:
        draw_menu_text_center("DIFFICULTY", 320, size="big")
        draw_menu_text_center("Use LEFT/RIGHT to change", 420)
        draw_menu_text_center("ESC to go back", 470)

    elif menu_screen == MENU_CONTROLS:
        draw_menu_text_center("CONTROLS", 280, size="big")
        lines = [
            "ARROWS: Move",
            "POWER PELLET: Eat ghosts temporarily",
            "ENTER (in menu): Select",
            "ESC: Back",
        ]
        y = 380
        for line in lines:
            draw_menu_text_center(line, y)
            y += 35

    elif menu_screen == MENU_LEADERBOARD:
        draw_menu_text_center("LEADERBOARD", 260, size="big")
        y = 360
        for name, s in leaderboard_rows:
            draw_menu_text_center(f"{name}  -  {s}", y)
            y += 35
        draw_menu_text_center("ESC to go back", 590)


def handle_menu_key(event):
    """
    Returns True if it consumed input.
    """
    global cover_active, menu_screen, menu_index, difficulty_index, run, moving
    global run_start_ticks, score_submitted, enter_name_active


    if event.type != pygame.KEYDOWN:
        return False

    if menu_screen == MENU_MAIN:
        options_count = 5  # START, DIFFICULTY, LEADERBOARD, CONTROLS, QUIT

        if event.key == pygame.K_UP:
            menu_index = (menu_index - 1) % options_count
            audio.menu_move()
            return True
        if event.key == pygame.K_DOWN:
            menu_index = (menu_index + 1) % options_count
            audio.menu_move()
            return True

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if menu_index == 0:  # START GAME
                apply_difficulty(difficulty_index)
                cover_active = False
                moving = True          # start immediately
                audio.start()
                cover_active = False
                moving = True
                run_start_ticks = pygame.time.get_ticks()
                score_submitted = False
                enter_name_active = False
                return True
            if menu_index == 1:  # DIFFICULTY
                menu_screen = MENU_DIFFICULTY
                audio.menu_select()
                return True
            if menu_index == 2:  # LEADERBOARD
                menu_screen = MENU_LEADERBOARD
                audio.menu_select()
                return True
            if menu_index == 3:  # CONTROLS
                menu_screen = MENU_CONTROLS
                audio.menu_select()
                return True
            if menu_index == 4:  # QUIT
                audio.menu_select()
                run = False
                return True

        return False

    # difficulty screen
    if menu_screen == MENU_DIFFICULTY:
        if event.key == pygame.K_LEFT:
            difficulty_index = (difficulty_index - 1) % len(difficulty_names)
            apply_difficulty(difficulty_index)
            audio.menu_move()
            return True
        if event.key == pygame.K_RIGHT:
            difficulty_index = (difficulty_index + 1) % len(difficulty_names)
            apply_difficulty(difficulty_index)
            audio.menu_move()
            return True
        if event.key == pygame.K_ESCAPE:
            menu_screen = MENU_MAIN
            return True
        return False

    # controls / leaderboard screens
    if menu_screen in (MENU_CONTROLS, MENU_LEADERBOARD):
        if event.key == pygame.K_ESCAPE:
            audio.menu_back()
            menu_screen = MENU_MAIN
            return True
        return False

    return False



# Ghost class
class Ghost:
    def __init__(self, x_coord, y_coord, target, speed, img, direct, dead, box, id):
        self.x_pos = x_coord
        self.y_pos = y_coord
        self.center_x = self.x_pos + 22
        self.center_y = self.y_pos + 22
        self.target = target
        self.speed = speed
        self.in_box = box
        self.img = img
        self.direction = direct
        self.dead = dead
        self.id = id
        self.turns, self.in_box = self.check_collisons()
        self.rect = self.draw() # get rect for collision detection
    def draw(self):
        if (not powerup and not self.dead) or (eaten_ghosts[self.id]and powerup and not self.dead):
            screen.blit(self.img,(self.x_pos,self.y_pos)) 
        elif powerup and not self.dead and not eaten_ghosts[self.id]:
            # Flash in the last 3 seconds of frightened mode
            if power_counter >= (powerup_duration_frames - powerup_flash_frames):
                if (power_counter // flash_toggle_rate) % 2 == 0:
                    screen.blit(ghost_spooked, (self.x_pos, self.y_pos))
                else:
                    screen.blit(ghost_spooked2, (self.x_pos, self.y_pos))
            else:
                screen.blit(ghost_spooked, (self.x_pos, self.y_pos))
        else:
            dir_key = {0: "right", 1: "left", 2: "up", 3: "down"}[self.direction]
            screen.blit(ghost_dead_sprites[dir_key], (self.x_pos, self.y_pos))
        ghost_rect  = pygame.rect.Rect((self.center_x - 18, self.center_y - 18), (36,36))
        return ghost_rect
    def check_collisons(self):

        # Calculate tile sizes based on screen dimensions
        num1 = ((HEIGHT - 50) // 32)   # height of each maze tile
        num2 = (WIDTH // 30)           # width of each maze tile
        num3 = 15                      # small offset used for collision checking

        # Reset allowed turning directions
        # Order: [right, left, up, down]
        self.turns = [False, False, False, False]

        # Check that the ghost is within the horizontal bounds of the maze
        if 0 < self.center_x // 30 < 29:

            # Check if the tile above is a gate (value 9)
            if level[(self.center_y - num3) // num1][self.center_x // num2] == 9:
                self.turns[2] = True

            # Check if the ghost can move left
            # Movement is allowed if the tile is empty (<3)
            # or if it is a gate (9) and the ghost is dead or in the box
            if level[self.center_y // num1][(self.center_x - num3) // num2] < 3 \
                    or (level[self.center_y // num1][(self.center_x - num3) // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[1] = True

            # Check if the ghost can move right
            if level[self.center_y // num1][(self.center_x + num3) // num2] < 3 \
                    or (level[self.center_y // num1][(self.center_x + num3) // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[0] = True

            # Check if the ghost can move down
            if level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                    or (level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[3] = True

            # Check if the ghost can move up
            if level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                    or (level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[2] = True

            # Additional alignment checks when moving vertically
            if self.direction == 2 or self.direction == 3:
                # Ensure the ghost is centred in the tile horizontally
                if 12 <= self.center_x % num2 <= 18:
                    if level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                            or (level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                            or (level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True

                # Allow turning left or right when vertically aligned
                if 12 <= self.center_y % num1 <= 18:
                    if level[self.center_y // num1][(self.center_x - num2) // num2] < 3 \
                            or (level[self.center_y // num1][(self.center_x - num2) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if level[self.center_y // num1][(self.center_x + num2) // num2] < 3 \
                            or (level[self.center_y // num1][(self.center_x + num2) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True

            # Additional alignment checks when moving horizontally
            if self.direction == 0 or self.direction == 1:
                if 12 <= self.center_x % num2 <= 18:
                    if level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                            or (level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                            or (level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True

                # Allow turning up or down when horizontally aligned
                if 12 <= self.center_y % num1 <= 18:
                    if level[self.center_y // num1][(self.center_x - num3) // num2] < 3 \
                            or (level[self.center_y // num1][(self.center_x - num3) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if level[self.center_y // num1][(self.center_x + num3) // num2] < 3 \
                            or (level[self.center_y // num1][(self.center_x + num3) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True

        # Allow wrap-around movement at the maze edges
        else:
            self.turns[0] = True
            self.turns[1] = True

        # Check whether the ghost is inside the ghost box area
        if 350 < self.x_pos < 550 and 370 < self.y_pos < 470:
            self.in_box = True
        else:
            self.in_box = False

        # Return the allowed turns and the ghost box state
        return self.turns, self.in_box
    #def move_clyde(self):
        # turns list order: [right, left, up, down]
        # Clyde attempts take turns whenever advantageous toward target


        # Moving RIGHT
        if self.direction == 0:
            # If target is to the right and the path is open, keep moving right
            if self.target[0] > self.x_pos and self.turns[0]:
                self.x_pos += self.speed

            # If cannot move right, choose a new direction based on target and available turns
            elif not self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                # Fallback choices if target-based choices fail
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed

            # If right is still available, allow an “advantageous” turn at a junction
            else:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos += self.speed

        # Moving LEFT
        elif self.direction == 1:
            # If target is below and down is open, turn down (and move)
            if self.target[1] > self.y_pos and self.turns[3]:
                self.direction = 3
                self.y_pos += self.speed

            # Otherwise, if target is left and left is open, keep moving left
            elif self.target[0] < self.x_pos and self.turns[1]:
                self.x_pos -= self.speed

            # If cannot move left, choose a new direction based on target and available turns
            elif not self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                # Fallback choices
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed

            # If left is still available, allow an “advantageous” turn at a junction
            else:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos -= self.speed

        # Moving UP
        elif self.direction == 2:
            # Prefer turning left toward target if possible
            if self.target[0] < self.x_pos and self.turns[1]:
                self.direction = 1
                self.x_pos -= self.speed

            # Otherwise keep moving up if possible and target is above
            elif self.target[1] < self.y_pos and self.turns[2]:
                self.y_pos -= self.speed

            # If cannot move up, choose a new direction
            elif not self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                # Fallback choices
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed

            # If up is still open, allow an “advantageous” turn at junctions
            else:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos -= self.speed

        # Moving DOWN
        elif self.direction == 3:
            # If target is below and down is open, keep moving down
            if self.target[1] > self.y_pos and self.turns[3]:
                self.y_pos += self.speed

            # If cannot move down, choose a new direction
            elif not self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                # Fallback choices
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed

             # If down is still open, allow an “advantageous” turn at junctions
            else:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos += self.speed


        # Tunnel wrap-around (left/right edges)
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos = -30  

        self.center_x = self.x_pos + 22
        self.center_y = self.y_pos + 22


        return self.x_pos, self.y_pos, self.direction
    def move_clyde(self):
        # r, l, u, d
        # clyde is going to turn whenever advantageous for pursuit
        if self.direction == 0:
            if self.target[0] > self.x_pos and self.turns[0]:
                self.x_pos += self.speed
            elif not self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                if self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos += self.speed
        elif self.direction == 1:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.direction = 3
            elif self.target[0] < self.x_pos and self.turns[1]:
                self.x_pos -= self.speed
            elif not self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                if self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos -= self.speed
        elif self.direction == 2:
            if self.target[0] < self.x_pos and self.turns[1]:
                self.direction = 1
                self.x_pos -= self.speed
            elif self.target[1] < self.y_pos and self.turns[2]:
                self.direction = 2
                self.y_pos -= self.speed
            elif not self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos -= self.speed
        elif self.direction == 3:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.y_pos += self.speed
            elif not self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos += self.speed
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos = -30
        return self.x_pos, self.y_pos, self.direction
    def move_blinky(self):
        # r, l, u, d
        # blinky is going to turn whenever colliding with walls, otherwise continue straight
        if self.direction == 0:
            if self.target[0] > self.x_pos and self.turns[0]:
                self.x_pos += self.speed
            elif not self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[0]:
                self.x_pos += self.speed
        elif self.direction == 1:
            if self.target[0] < self.x_pos and self.turns[1]:
                self.x_pos -= self.speed
            elif not self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[1]:
                self.x_pos -= self.speed
        elif self.direction == 2:
            if self.target[1] < self.y_pos and self.turns[2]:
                self.direction = 2
                self.y_pos -= self.speed
            elif not self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[2]:
                self.y_pos -= self.speed
        elif self.direction == 3:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.y_pos += self.speed
            elif not self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[3]:
                self.y_pos += self.speed
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos = -30
        return self.x_pos, self.y_pos, self.direction
    def move_inky(self):
        # r, l, u, d
        # inky turns up or down at any point to pursue, but left and right only on collision
        if self.direction == 0:
            if self.target[0] > self.x_pos and self.turns[0]:
                self.x_pos += self.speed
            elif not self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                if self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos += self.speed
        elif self.direction == 1:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.direction = 3
            elif self.target[0] < self.x_pos and self.turns[1]:
                self.x_pos -= self.speed
            elif not self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                if self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                else:
                    self.x_pos -= self.speed
        elif self.direction == 2:
            if self.target[1] < self.y_pos and self.turns[2]:
                self.direction = 2
                self.y_pos -= self.speed
            elif not self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[2]:
                self.y_pos -= self.speed
        elif self.direction == 3:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.y_pos += self.speed
            elif not self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[3]:
                self.y_pos += self.speed
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos = -30
        return self.x_pos, self.y_pos, self.direction
    def move_pinky(self):
        # r, l, u, d
        # inky is going to turn left or right whenever advantageous, but only up or down on collision
        if self.direction == 0:
            if self.target[0] > self.x_pos and self.turns[0]:
                self.x_pos += self.speed
            elif not self.turns[0]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
            elif self.turns[0]:
                self.x_pos += self.speed
        elif self.direction == 1:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.direction = 3
            elif self.target[0] < self.x_pos and self.turns[1]:
                self.x_pos -= self.speed
            elif not self.turns[1]:
                if self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[1]:
                self.x_pos -= self.speed
        elif self.direction == 2:
            if self.target[0] < self.x_pos and self.turns[1]:
                self.direction = 1
                self.x_pos -= self.speed
            elif self.target[1] < self.y_pos and self.turns[2]:
                self.direction = 2
                self.y_pos -= self.speed
            elif not self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] > self.y_pos and self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[3]:
                    self.direction = 3
                    self.y_pos += self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[2]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos -= self.speed
        elif self.direction == 3:
            if self.target[1] > self.y_pos and self.turns[3]:
                self.y_pos += self.speed
            elif not self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.target[1] < self.y_pos and self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[2]:
                    self.direction = 2
                    self.y_pos -= self.speed
                elif self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                elif self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
            elif self.turns[3]:
                if self.target[0] > self.x_pos and self.turns[0]:
                    self.direction = 0
                    self.x_pos += self.speed
                elif self.target[0] < self.x_pos and self.turns[1]:
                    self.direction = 1
                    self.x_pos -= self.speed
                else:
                    self.y_pos += self.speed
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos = -30
        return self.x_pos, self.y_pos, self.direction         
    def move_dead_to_box(self, dead_dist):
        # Update centers
        self.center_x = self.x_pos + 22
        self.center_y = self.y_pos + 22

        r, c = pix_to_tile(self.center_x, self.center_y)

        # If somehow off grid, just don't move
        if not (0 <= r < len(dead_dist) and 0 <= c < len(dead_dist[0])):
            return self.x_pos, self.y_pos, self.direction

        # Choose the best neighbor (lowest distance)
        best_dir = None
        best_val = None

        # directions: 0 right, 1 left, 2 up, 3 down
        candidates = [
            (0, 0, 1),
            (1, 0, -1),
            (2, -1, 0),
            (3, 1, 0),
        ]

        for d, dr, dc in candidates:
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(dead_dist) and 0 <= nc < len(dead_dist[0]):
                v = dead_dist[nr][nc]
                if v != -1:
                    if best_val is None or v < best_val:
                        best_val = v
                        best_dir = d

        # If no path found, do nothing
        if best_dir is None:
            return self.x_pos, self.y_pos, self.direction

        # Move in the chosen direction using your style
        self.direction = best_dir
        if self.direction == 0:
            self.x_pos += self.speed
        elif self.direction == 1:
            self.x_pos -= self.speed
        elif self.direction == 2:
            self.y_pos -= self.speed
        elif self.direction == 3:
            self.y_pos += self.speed

        # tunnel wrap
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos = -30

        return self.x_pos, self.y_pos, self.direction
   
# draw board using different shape orientations
def draw_boards(level):
    #The heigh of th board and width seperated by the amount of tiles
    num1 = ((HEIGHT - 50) // 32)
    num2 = ((WIDTH // 30))
    #Goes through every tile in level
    for i in range(len(level)):
        for j in range(len(level[i])):
            if level[i][j] == 1:
                pygame.draw.circle(screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 4)
            if level[i][j] == 2 and not flicker:
                pygame.draw.circle(screen, 'white', (j * num2 + (0.5 * num2) , i * num1 +(0.5 * num1)),10)        
            if level[i][j] == 3:
                pygame.draw.line(screen, colour, (j * num2 + (0.5 * num2), i *num1), (j * num2 + (0.5*num2), i*num1 + num1), 3)
            if level[i][j] == 4:
                pygame.draw.line(screen, colour, (j * num2, (0.5 * num1) + i *num1), (j * num2 + num2, i*num1 + (0.5*num1)), 3)
            if level[i][j] == 5:
                pygame.draw.arc(screen,colour, [(j*num2 - (num2*0.4)) - 2, (i *num1 + (0.5*num1 )), num2, num1], 0, PI/2, 3)
            if level[i][j] == 6:
                pygame.draw.arc(screen,colour, [(j*num2 + (num2*0.5)), (i *num1 + (0.5*num1 )), num2, num1], PI/2,PI, 3)
           
            if level[i][j] == 7:
                pygame.draw.arc(screen,colour, [(j*num2 + (num2*0.5)), (i *num1 - (0.4*num1)), num2, num1], PI,3*PI/2, 3)
           
            if level[i][j] == 8:
                pygame.draw.arc(screen,colour, [(j*num2 - (num2*0.4))-2, (i *num1 - (0.4*num1 )), num2, num1], 3*PI/2,2*PI, 3)

            if level[i][j] == 9:
                pygame.draw.line(screen, "white", (j * num2, (0.5 * num1) + i *num1), (j * num2 + num2, i*num1 + (0.5*num1)), 3)

def draw_player():
    # different pacman images per orientation
    image = player_images[counter // 5]
    if direction == 0:
        transformed_image = image
    elif direction == 1:
        transformed_image = pygame.transform.flip(image, True, False)
    elif direction == 2:
        transformed_image = pygame.transform.rotate(image, 90)
    elif direction == 3:
        transformed_image = pygame.transform.rotate(image, -90)
    else:
        transformed_image = image  
    transformed_image.set_colorkey(pygame.Color("magenta"))
    screen.blit(transformed_image, (player_x, player_y))

def check_position(centrex, centrey):
    turns = [False, False, False, False]
    num1 = (HEIGHT - 50) // 32
    num2 = (WIDTH // 30)
    num3 = 15
    # check collisions based on centre x and centre y of pacman +/- fudge number
    if centrex // 30 < 29:
        if direction == 0:
            if level[centrey // num1][(centrex - num3) // num2] < 3:
                turns[1] = True
        if direction == 1:
            if level[centrey // num1][(centrex + num3) // num2] < 3:
                turns[0] = True
        if direction == 2:
            if level[(centrey + num3) // num1][centrex // num2] < 3:
                turns[3] = True
        if direction == 3:
            if level[(centrey - num3) // num1][centrex // num2] < 3:
                turns[2] = True

        if direction == 2 or direction == 3:
            if 12 <= centrex % num2 <= 18:
                if level[(centrey + num3) // num1][centrex // num2] < 3:
                    turns[3] = True
                if level[(centrey - num3) // num1][centrex // num2] < 3:
                    turns[2] = True
            if 12 <= centrey % num1 <= 18:
                if level[centrey // num1][(centrex - num2) // num2] < 3:
                    turns[1] = True
                if level[centrey // num1][(centrex + num2) // num2] < 3:
                    turns[0] = True
        if direction == 0 or direction == 1:
            if 12 <= centrex % num2 <= 18:
                if level[(centrey + num1) // num1][centrex // num2] < 3:
                    turns[3] = True
                if level[(centrey - num1) // num1][centrex // num2] < 3:
                    turns[2] = True
            if 12 <= centrey % num1 <= 18:
                if level[centrey // num1][(centrex - num3) // num2] < 3:
                    turns[1] = True
                if level[centrey // num1][(centrex + num3) // num2] < 3:
                    turns[0] = True
    else:
        turns[0] = True
        turns[1] = True

    return turns

def move_player(play_x, play_y):
    # r, l, u, d
    if direction == 0 and turns_allowed[0]:
        play_x += player_speed
    elif direction == 1 and turns_allowed[1]:
        play_x -= player_speed
    if direction == 2 and turns_allowed[2]:
        play_y -= player_speed
    elif direction == 3 and turns_allowed[3]:
        play_y += player_speed
    return play_x, play_y


def check_collisions(scor, power,power_count,eaten_ghosts):
    num1 = (HEIGHT - 50) // 32
    num2= WIDTH//30
    ate_pellet = False
    ate_power = False
    # chceks player is within constraints 
    if 0< player_x < 870:
        if level[centre_y//num1][centre_x//num2] == 1: #checks position in maze / changes orb value to 0(background)
            level[centre_y//num1][centre_x//num2] = 0
            scor += 10  #increments score counter
            ate_pellet = True
        if level[centre_y//num1][centre_x//num2] == 2:
            level[centre_y//num1][centre_x//num2] = 0
            scor += 50    # Larger score incremetn for 2(big orbs)
            power = True
            power_count = 0
            eaten_ghosts = [False,False,False,False]
            ate_power = True


    return scor, power, power_count, eaten_ghosts, ate_pellet, ate_power

def draw_ui():
    # Score
    score_text = font.render(f'Score: {score}', True, 'white')
    screen.blit(score_text, (10, 920))

    # Power-up indicator
    if powerup:
        pygame.draw.circle(screen, "blue", (140, 930), 15)

    # Lives display
    for i in range(lives):
        screen.blit(
            pygame.transform.scale(pacman_right2, (30, 30)),
            (650 + i * 40, 915)
        )

    # Start game prompt
    if not moving and not game_over and not game_won:
        start_text = big_font.render("PRESS P TO START", True, "green")
        text_rect = start_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(start_text, text_rect)
    
    if game_over:
        pygame.draw.rect(screen, "white", [50,200,800,300],0,10)
        pygame.draw.rect(screen, "black", [70,220,760,260],0,10)
        over_text = big_font.render("GAME OVER", True, "white")
        over_text2 = big_font.render("PRESS SPACE BAR TO MENU", True, "white")
        screen.blit(over_text, (300, 275))
        screen.blit(over_text2, (100, 375))
    if game_won:
        
        pygame.draw.rect(screen, "white", [50,200,800,300],0,10)
        pygame.draw.rect(screen, "black", [70,220,760,260],0,10)
        over_text = big_font.render("VICTORY", True, "white")
        over_text2 = big_font.render("SPACE BAR TO NEXT LEVEL", True, "white")
        screen.blit(over_text, (300, 275))
        screen.blit(over_text2, (100, 375))
    lvl_text = font.render(f'Level: {current_level + 1}', True, 'white')
    screen.blit(lvl_text, (250, 920))
def draw_name_entry_popup():
    # Larger box for readability
    pygame.draw.rect(screen, "white", [100, 500, 700, 220], 0, 12)
    pygame.draw.rect(screen, "black", [120, 520, 660, 180], 0, 12)

    title = big_font.render("ENTER YOUR NAME", True, "white")
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 555)))

    hint = font.render("Press ENTER to submit  |  SPACE to skip", True, "white")
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 595)))

    shown = name_buffer if name_buffer else "_"
    name_text = big_font.render(shown, True, "yellow")
    screen.blit(name_text, name_text.get_rect(center=(WIDTH // 2, 650)))



def get_targets(blink_x, blink_y, ink_x, ink_y, pink_x, pink_y, clyd_x, clyd_y):
    
    if player_x < 450:
        runaway_x = 900
    else:
        runaway_x = 0

    if player_y < 450:
        runaway_y = 900
    else:
        runaway_y = 0

    return_target = (380, 400)
    
    if powerup:
        if not blinky.dead and not eaten_ghosts[0]:
            blink_target = (runaway_x, runaway_y)
        elif not blinky.dead and eaten_ghosts[0]:
            if 340 < blink_x < 560 and 340 < blink_y < 500:
                blink_target = (400, 100)
            else:
                blink_target = (player_x, player_y)
        else:
            blink_target = return_target
        if not inky.dead and not eaten_ghosts[1]:
            ink_target = (runaway_x, player_y)
        elif not inky.dead and eaten_ghosts[1]:
            if 340 < ink_x < 560 and 340 < ink_y < 500:
                ink_target = (400, 100)
            else:
                ink_target = (player_x, player_y)
        else:
            ink_target = return_target
        if not pinky.dead:
            pink_target = (player_x, runaway_y)
        elif not pinky.dead and eaten_ghosts[2]:
            if 340 < pink_x < 560 and 340 < pink_y < 500:
                pink_target = (400, 100)
            else:
                pink_target = (player_x, player_y)
        else:
            pink_target = return_target
        if not clyde.dead and not eaten_ghosts[3]:
            clyd_target = (450, 450)
        elif not clyde.dead and eaten_ghosts[3]:
            if 340 < clyd_x < 560 and 340 < clyd_y < 500:
                clyd_target = (400, 100)
            else:
                clyd_target = (player_x, player_y)
        else:
            clyd_target = return_target
    else:
        if not blinky.dead:
            if 340 < blink_x < 560 and 340 < blink_y < 500:
                blink_target = (400, 100)
            else:
                blink_target = (player_x, player_y)
        else:
            blink_target = return_target
        if not inky.dead:
            if 340 < ink_x < 560 and 340 < ink_y < 500:
                ink_target = (400, 100)
            else:
                ink_target = (player_x, player_y)
        else:
            ink_target = return_target
        if not pinky.dead:
            if 340 < pink_x < 560 and 340 < pink_y < 500:
                pink_target = (400, 100)
            else:
                pink_target = (player_x, player_y)
        else:
            pink_target = return_target
        if not clyde.dead:
            if 340 < clyd_x < 560 and 340 < clyd_y < 500:
                clyd_target = (400, 100)
            else:
                clyd_target = (player_x, player_y)
        else:
            clyd_target = return_target
    return [blink_target, ink_target, pink_target, clyd_target]

    
    
    
    
    return target_list
def reset_entities_for_level():
    global player_x, player_y, direction, direction_command, moving
    global blinky_x, blinky_y, blinky_direction
    global inky_x, inky_y, inky_direction
    global pinky_x, pinky_y, pinky_direction
    global clyde_x, clyde_y, clyde_direction
    global eaten_ghosts
    global blinky_dead, inky_dead, pinky_dead, clyde_dead
    global powerup, power_counter
    global colour

    powerup = False
    power_counter = 0

    player_x, player_y = 450, 663
    direction = 0
    direction_command = 0

    blinky_x, blinky_y, blinky_direction = 440, 388, 0
    inky_x, inky_y, inky_direction = 440, 388, 2
    pinky_x, pinky_y, pinky_direction = 440, 438, 2
    clyde_x, clyde_y, clyde_direction = 440, 438, 2

    eaten_ghosts = [False, False, False, False]
    blinky_dead = inky_dead = pinky_dead = clyde_dead = False

    colour = get_colour(current_level)
    # IMPORTANT: next level should not auto-run
    moving = False

#counter2 = 0

run = True
while run: 
    #Sets maz fps and fills background black
    timer.tick(fps)
    screen.fill("black")
    draw_boards(level)
    
    if cover_active:
        audio.play_music("menu")
    else:
        audio.play_music("level")

    if game_won and not win_sfx_played:
            audio.win()
            win_sfx_played = True

    #Wall colision checker
    centre_x = player_x + 23
    centre_y = player_y +24
    turns_allowed = check_position(centre_x,centre_y)

    if powerup:
        ghost_speeds = [1, 1, 1, 1]
    else:
        ghost_speeds = [2, 2, 2, 2]
    if eaten_ghosts[0]:
        ghost_speeds[0] = 2
    if eaten_ghosts[1]:
        ghost_speeds[1] = 2
    if eaten_ghosts[2]:
        ghost_speeds[2] = 2
    if eaten_ghosts[3]:
        ghost_speeds[3] = 2
    if blinky_dead:
        ghost_speeds[0] = 4
    if inky_dead:
        ghost_speeds[1] = 4
    if pinky_dead:
        ghost_speeds[2] = 4
    if clyde_dead:
        ghost_speeds[3] = 4

    game_won = True
    for i in range(len(level)):
        if 1 in level[i] or 2 in level[i]:
            game_won = False

    player_circle = pygame.draw.circle(screen, "black", (centre_x, centre_y), 20, 2)
    draw_player()

    # Ghost drawing section
    blinky = Ghost(blinky_x, blinky_y, targets[0], ghost_speeds[0],get_ghost_facing_image("red", blinky_direction), blinky_direction, blinky_dead, blinky_box, 0 )
    inky = Ghost(inky_x, inky_y, targets[1], ghost_speeds[1], get_ghost_facing_image("blue", inky_direction), inky_direction, inky_dead, inky_box, 1 )
    pinky = Ghost(pinky_x, pinky_y, targets[2], ghost_speeds[2], get_ghost_facing_image("pink", pinky_direction), pinky_direction, pinky_dead, pinky_box, 2 )
    clyde = Ghost(clyde_x, clyde_y, targets[3], ghost_speeds[3], get_ghost_facing_image("yellow", clyde_direction), clyde_direction, clyde_dead, clyde_box, 3)

    #Ghost.move_clyde(clyde)
    

    # counter2 += 1
    # if counter2 >= 30:  # change direction every 30 frames (~0.5s at 60fps)
    #     inky_direction += 1
    #     counter2 = 0

    #     if inky_direction > 3:
    #         inky_direction = 0

    
            #Wall colision checker
    centre_x = player_x + 23
    centre_y = player_y +24
    turns_allowed = check_position(centre_x,centre_y)

    
    player_circle = pygame.draw.circle(screen, "black", (centre_x, centre_y), 20, 2)
    draw_player()
            
    if cover_active:
        moving= False

    #player movement
    if (not cover_active) and moving and (not game_over) and (not game_won):
        player_x, player_y = move_player(player_x, player_y)

        if blinky_dead:
            blinky_x, blinky_y, blinky_direction = blinky.move_dead_to_box(DEAD_DIST)
        elif not blinky.in_box:
            blinky_x, blinky_y, blinky_direction = blinky.move_blinky()
        else:
            blinky_x, blinky_y, blinky_direction = blinky.move_clyde()

        if inky_dead:
            inky_x, inky_y, inky_direction = inky.move_dead_to_box(DEAD_DIST)
        elif not inky.in_box:
            inky_x, inky_y, inky_direction = inky.move_inky()
        else:
            inky_x, inky_y, inky_direction = inky.move_clyde()

        if pinky_dead:
            pinky_x, pinky_y, pinky_direction = pinky.move_dead_to_box(DEAD_DIST)
        elif not pinky.in_box:
            pinky_x, pinky_y, pinky_direction = pinky.move_pinky()
        else:
            pinky_x, pinky_y, pinky_direction = pinky.move_clyde()

        if clyde_dead:
            clyde_x, clyde_y, clyde_direction = clyde.move_dead_to_box(DEAD_DIST)
        elif not clyde.in_box:
            clyde_x, clyde_y, clyde_direction = clyde.move_clyde()
        else:
            clyde_x, clyde_y, clyde_direction = clyde.move_clyde()
        run_start_ticks = pygame.time.get_ticks()
        score_submitted = False
        enter_name_active = False


   # print("plinky tile:", pix_to_tile(pinky.center_x, pinky.center_y))

    #score checker
    score,powerup, power_counter,eaten_ghosts,ate_pellet, ate_power = check_collisions(score,powerup, power_counter,eaten_ghosts)
    #print("score:", score)

    if ate_pellet:
        audio.pellet()
    if ate_power:
        audio.power()


    #Managing Pacman animations
    if counter < 19:
        counter+= 1
    else:
        counter = 0

    # Manage orb flicker rater
    flicker_counter +=1
    if flicker_counter >= 60: 
        flicker_counter = 0
    flicker = flicker_counter<15

        # Power up timer manager
    if powerup and power_counter < 600:  # 10 seconds at 60 fps
        power_counter += 1
    elif powerup and power_counter >= 600:
        power_counter = 0
        powerup = False

        # reset "already eaten during this power-up" tracking only
        eaten_ghosts = [False, False, False, False]

        # DO NOT revive dead ghosts here.
        # They must return to the box to revive (handled below).


   
    # UI drawing section
    draw_ui()
    if enter_name_active:
        draw_name_entry_popup()
    targets = get_targets(blinky_x, blinky_y, inky_x, inky_y, pinky_x, pinky_y, clyde_x, clyde_y)
    if cover_active:
        draw_cover_menu()

    if new_highscore_flag:
        if pygame.time.get_ticks() - new_highscore_ticks < 2000:
            msg = big_font.render("NEW HIGHSCORE!", True, "yellow")
            screen.blit(msg, msg.get_rect(center=(WIDTH//2, 120)))
        else:
            new_highscore_flag = False


    if not powerup:
        if (player_circle.colliderect(blinky.rect) and not blinky.dead) or \
                (player_circle.colliderect(inky.rect) and not inky.dead) or \
                (player_circle.colliderect(pinky.rect) and not pinky.dead) or \
                (player_circle.colliderect(clyde.rect) and not clyde.dead):
            if lives > 0:
                lives -= 1
                audio.player_die()
                startup_counter = 0
                powerup = False
                power_counter = 0
                player_x = 450
                player_y = 663
                direction = 0
                direction_command = 0
                blinky_x = 440
                blinky_y = 388
                blinky_direction = 0
                inky_x = 440
                inky_y = 388
                inky_direction = 2
                pinky_x = 440
                pinky_y = 438
                pinky_direction = 2
                clyde_x = 440
                clyde_y = 438
                clyde_direction = 2
                eaten_ghosts= [False, False, False, False]
                blinky_dead = False
                inky_dead = False
                clyde_dead = False
                pinky_dead = False
                moving = False
            else:
                game_over = True
                moving = False
                if not game_over_sfx_played:
                    audio.game_over()
                    game_over_sfx_played = True
                startup_counter = 0
    if powerup and player_circle.colliderect(blinky.rect) and eaten_ghosts[0] and not blinky.dead:
        if lives > 0:
            powerup = False
            power_counter = 0
            lives -= 1
            startup_counter = 0
            player_x = 450
            player_y = 663
            direction = 0
            direction_command = 0
            blinky_x = 440
            blinky_y = 388
            blinky_direction = 0
            inky_x = 440
            inky_y = 388
            inky_direction = 2
            pinky_x = 440
            pinky_y = 438
            pinky_direction = 2
            clyde_x = 440
            clyde_y = 438
            clyde_direction = 2
            eaten_ghosts = [False, False, False, False]
            blinky_dead = False
            inky_dead = False
            clyde_dead = False
            pinky_dead = False
            moving = False
        else:
            game_over = True
            moving = False
            startup_counter = 0
    if powerup and player_circle.colliderect(inky.rect) and eaten_ghosts[1] and not inky.dead:
        if lives > 0:
            powerup = False
            power_counter = 0
            lives -= 1
            startup_counter = 0
            player_x = 450
            player_y = 663
            direction = 0
            direction_command = 0
            blinky_x = 440
            blinky_y = 388
            blinky_direction = 0
            inky_x = 440
            inky_y = 388
            inky_direction = 2
            pinky_x = 440
            pinky_y = 438
            pinky_direction = 2
            clyde_x = 440
            clyde_y = 438
            clyde_direction = 2
            eaten_ghosts = [False, False, False, False]
            blinky_dead = False
            inky_dead = False
            clyde_dead = False
            pinky_dead = False
            moving = False
        else:
            game_over = True
            moving = False
            startup_counter = 0
    if powerup and player_circle.colliderect(pinky.rect) and eaten_ghosts[2] and not pinky.dead:
        if lives > 0:
            powerup = False
            power_counter = 0
            lives -= 1
            startup_counter = 0
            player_x = 450
            player_y = 663
            direction = 0
            direction_command = 0
            blinky_x = 440
            blinky_y = 388
            blinky_direction = 0
            inky_x = 440
            inky_y = 388
            inky_direction = 2
            pinky_x = 440
            pinky_y = 438
            pinky_direction = 2
            clyde_x = 440
            clyde_y = 438
            clyde_direction = 2
            eaten_ghosts = [False, False, False, False]
            blinky_dead = False
            inky_dead = False
            clyde_dead = False
            pinky_dead = False
            moving = False
        else:
            game_over = True
            moving = False
            startup_counter = 0
    if powerup and player_circle.colliderect(clyde.rect) and eaten_ghosts[3] and not clyde.dead:
        if lives > 0:
            powerup = False
            power_counter = 0
            lives -= 1
            startup_counter = 0
            player_x = 450
            player_y = 663
            direction = 0
            direction_command = 0
            blinky_x = 440
            blinky_y = 388
            blinky_direction = 0
            inky_x = 440
            inky_y = 388
            inky_direction = 2
            pinky_x = 440
            pinky_y = 438
            pinky_direction = 2
            clyde_x = 440
            clyde_y = 438
            clyde_direction = 2
            eaten_ghosts = [False, False, False, False]
            blinky_dead = False
            inky_dead = False
            clyde_dead = False
            pinky_dead = False
            moving = False
        else:
            game_over = True
            moving = False
            startup_counter = 0
    if powerup and player_circle.colliderect(blinky.rect) and not blinky.dead and not eaten_ghosts[0]:
        blinky_dead = True
        eaten_ghosts[0] = True
        score += (2 ** eaten_ghosts.count(True)) * 100
        audio.ghost_eaten()

    if powerup and player_circle.colliderect(inky.rect) and not inky.dead and not eaten_ghosts[1]:
        inky_dead = True
        eaten_ghosts[1] = True
        score += (2 ** eaten_ghosts.count(True)) * 100
        audio.ghost_eaten()

    if powerup and player_circle.colliderect(pinky.rect) and not pinky.dead and not eaten_ghosts[2]:
        pinky_dead = True
        eaten_ghosts[2] = True
        score += (2 ** eaten_ghosts.count(True)) * 100
        audio.ghost_eaten()

    if powerup and player_circle.colliderect(clyde.rect) and not clyde.dead and not eaten_ghosts[3]:
        clyde_dead = True
        eaten_ghosts[3] = True
        score += (2 ** eaten_ghosts.count(True)) * 100
        audio.ghost_eaten()

    
    if game_over and (not cover_active) and (not score_submitted) and (not enter_name_active):
        enter_name_active = True
        name_buffer = ""

        # compute final time once
        if run_start_ticks is not None:
            final_time_seconds = (pygame.time.get_ticks() - run_start_ticks) / 1000.0
        else:
            final_time_seconds = 0.0

     
    



    # Event manager
    #Managing the exit function 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN and enter_name_active:
            if event.key == pygame.K_RETURN:
                rows, is_new = leaderboard.add_score(
                    name_buffer,
                    score,
                    current_level + 1
                )

                leaderboard_rows = leaderboard.get_menu_rows()

                new_highscore_flag = is_new
                new_highscore_ticks = pygame.time.get_ticks()

                score_submitted = True
                enter_name_active = False

            elif event.key == pygame.K_BACKSPACE:
                name_buffer = name_buffer[:-1]
            else:
                ch = event.unicode.upper()
                if ch.isalnum() and len(name_buffer) < leaderboard.NAME_MAXLEN:
                    name_buffer += ch

            continue  # important: don't let this keypress also move Pac-Man/menu


        # If cover menu is active, it owns the input
        if cover_active:
            if handle_menu_key(event):
                continue


        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p and not moving and not game_over and not game_won:
                moving = True
                if run_start_ticks is None:
                    run_start_ticks = pygame.time.get_ticks()

            if event.key == pygame.K_SPACE:
                if event.key == pygame.K_SPACE and game_over:
                 
                    enter_name_active = False
                    score_submitted = True

                    cover_active = True
                    menu_screen = MENU_MAIN
                    menu_index = 0

                    current_level = 0
                    level = copy.deepcopy(LEVELS[current_level])
                    DEAD_DIST = build_dead_distance_map(level, BOX_TARGET_TILE)

                    score = 0
                    lives = conslives
                    game_over = False
                    game_won = False
                    moving = False

                    reset_entities_for_level()
                    continue

                elif game_won:
                    # advance to next level, then show READY screen (not menu)
                    current_level += 1
                    colour = get_colour(current_level)
                    win_sfx_played = False
                    gameover_sfx_played = False

                    if current_level >= len(LEVELS):
                        current_level = 0  # loop back (or add final victory screen later)

                    level = copy.deepcopy(LEVELS[current_level])
                    DEAD_DIST = build_dead_distance_map(level, BOX_TARGET_TILE)

                    game_won = False
                    game_over = False
                    moving = False

                    reset_entities_for_level()

        


        
        # Input and direction manager
        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_RIGHT:
                direction_command = 0
            if event.key == pygame.K_LEFT:
                direction_command = 1
            if event.key == pygame.K_UP:
                direction_command = 2
            if event.key == pygame.K_DOWN:
                direction_command = 3
        if event.type == pygame.KEYUP: 
            if event.key == pygame.K_RIGHT and direction_command == 0:
                direction_command = direction
            if event.key == pygame.K_LEFT and direction_command == 1:
                direction_command =  direction
            if event.key == pygame.K_UP and direction_command == 2:
                direction_command = direction
            if event.key == pygame.K_DOWN and direction_command == 3:
                direction_command = direction

    #Joystick style movement condition 
    if direction_command == 0 and turns_allowed[0]:
        direction = 0   
    if direction_command == 1 and turns_allowed[1]:
        direction = 1 
    if direction_command == 2 and turns_allowed[2]:
        direction = 2
    if direction_command == 3 and turns_allowed[3]:
        direction = 3

    # pushes pacman into the map when at borders
    if player_x > WIDTH:
        player_x = -47
    elif player_x < -50:
        player_x = WIDTH - 3

    # Revive ghosts when they reach the ghost box
    if blinky.in_box and blinky_dead:
        blinky_dead = False
    if inky.in_box and inky_dead:
        inky_dead = False
    if pinky.in_box and pinky_dead:
        pinky_dead = False
    if clyde.in_box and clyde_dead:
        clyde_dead = False
    



    # flips the display which in turn changes the screen to the next frame
    pygame.display.flip()
pygame.quit()


