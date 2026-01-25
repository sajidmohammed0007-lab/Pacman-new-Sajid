# initialising libraries
import pygame
from board import boards
import math 
import spritesheet
#initialising key variables
pygame.init()
WIDTH = 900
HEIGHT = 950
screen = pygame.display.set_mode([WIDTH, HEIGHT])
timer = pygame.time.Clock()
fps = 60

#Font settings
font = pygame.font.Font('freesansbold.ttf', 20)
pygame.display.set_caption('PACMANY')
big_font = pygame.font.Font('freesansbold.ttf', 50)


#Variablees for maze drawing
level = boards #current board only 1
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
ghost_speed = 2
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
lives = 4

#PowerUps
powerup = False
power_counter = 0

#Startup delay variables
moving = False

#Eaten ghosts tracker
eaten_ghosts = [False, False,False,False]

# Ghost positions
blinky_x = 56
blinky_y = 58
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
        "up": sprite_sheet.get_image(5, 0, 32, 32, 1.40625, "magenta"),
        "down": sprite_sheet.get_image(5, 1, 32, 32, 1.40625, "magenta"),
        "left": sprite_sheet.get_image(5, 2, 32, 32, 1.40625, "magenta"),
        "right": sprite_sheet.get_image(5, 3, 32, 32, 1.40625, "magenta"),
    }
ghost_dead_sprites = load_dead_ghosts(sprite_sheet)

ghost_spooked =sprite_sheet.get_image(5, 3,32,32,1.40625,"magenta")
ghost_dead =sprite_sheet.get_image(5, 2,32,32,1.40625,"magenta")

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
            screen.blit(ghost_spooked,(self.x_pos,self.y_pos)) 
        else:
            screen.blit(ghost_dead,(self.x_pos,self.y_pos)) 
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
        if 350 < self.x_pos < 550 and 370 < self.y_pos < 480:
            self.in_box = True
        else:
            self.in_box = False

        # Return the allowed turns and the ghost box state
        return self.turns, self.in_box
    def move_clyde(self):
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
    # chceks player is within constraints 
    if 0< player_x < 870:
        if level[centre_y//num1][centre_x//num2] == 1: #checks position in maze / changes orb value to 0(background)
            level[centre_y//num1][centre_x//num2] = 0
            scor += 10  #increments score counter
        if level[centre_y//num1][centre_x//num2] == 2:
            level[centre_y//num1][centre_x//num2] = 0
            scor += 50    # Larger score incremetn for 2(big orbs)
            power = True
            power_count = 0
            eaten_ghosts = [False,False,False,False]

    return scor, power, power_count, eaten_ghosts

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
    if not moving:
        start_text = big_font.render("PRESS P TO START", True, "green")
        text_rect = start_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(start_text, text_rect)

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
        if not blinky.dead:
            blink_target = (runaway_x, runaway_y)
        elif not blinky.dead:
            if 340 < blink_x < 560 and 340 < blink_y < 500:
                blink_target = (400, 100)
            else:
                blink_target = (player_x, player_y)
        else:
            blink_target = return_target

        if not inky.dead:
            ink_target = (runaway_x, player_y)
        elif not inky.dead:
            if 340 < ink_x < 560 and 340 < ink_y < 500:
                ink_target = (400, 100)
            else:
                ink_target = (player_x, player_y)
        else:
            ink_target = return_target
        if not pinky.dead:
            pink_target = (player_x, runaway_y)
        elif not pinky.dead:
            if 340 < pink_x < 560 and 340 < pink_y < 500:
                pink_target = (400, 100)
            else:
                pink_target = (player_x, player_y)
        else:
            pink_target = return_target
        if not clyde.dead:
            clyd_target = (450, 450)
        elif not clyde.dead:
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

#counter2 = 0

run = True
while run: 
    #Sets maz fps and fills background black
    timer.tick(fps)
    screen.fill("black")
    draw_boards(level)
    draw_player()
    

    # Ghost drawing section
    blinky = Ghost(blinky_x, blinky_y, targets[0], ghost_speed,get_ghost_facing_image("red", blinky_direction), blinky_direction, blinky_dead, blinky_box, 0 )
    inky = Ghost(inky_x, inky_y, targets[1], ghost_speed, get_ghost_facing_image("blue", inky_direction), inky_direction, inky_dead, inky_box, 1 )
    pinky = Ghost(pinky_x, pinky_y, targets[2], ghost_speed, get_ghost_facing_image("pink", pinky_direction), pinky_direction, pinky_dead, pinky_box, 2 )
    clyde = Ghost(clyde_x, clyde_y, targets[3], ghost_speed, get_ghost_facing_image("yellow", clyde_direction), clyde_direction, clyde_dead, clyde_box, 3)

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

    
    player_circle = pygame.draw.circle(screen, "red", (centre_x, centre_y), 20, 2)

    #player movement
    if moving:
        player_x,player_y = move_player(player_x,player_y)
        blinky_x, blinky_y, blinky_direction = blinky.move_clyde()
        inky_x, inky_y, inky_direction = inky.move_clyde() 
        pinky_x, pinky_y, pinky_direction = pinky.move_clyde()
        clyde_x, clyde_y, clyde_direction = clyde.move_clyde()

    #score checker
    score,powerup, power_counter,eaten_ghosts = check_collisions(score,powerup, power_counter,eaten_ghosts)
    print("score:", score)

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
    if powerup and power_counter < 600: #10 seconds at 60 fps
        power_counter += 1
    elif powerup and power_counter >- 600:
        power_counter = 0
        powerup = False
        eaten_ghosts = [False, False, False,False] #reset eaten ghosts
    
   
    # UI drawing section
    draw_ui()
    targets = get_targets(blinky_x, blinky_y, inky_x, inky_y, pinky_x, pinky_y, clyde_x, clyde_y)
    # Event manager
    #Managing the exit function 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                moving = True

        
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

    # flips the display which in turn changes the screen to the next frame
    pygame.display.flip()
pygame.quit()

