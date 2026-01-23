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
font = pygame.font.Font('freesansbold.ttf', 20)
pygame.display.set_caption('PACMANY')


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
powerup = False
lives = 4

#PowerUps
powerup = False
power_counter = 0

#Startup delay variables
startup_counter = 0
moving = False

#Eaten ghosts tracker
eaten_ghosts = [False, False,False,False]

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
    score_text = font.render(f'Score: {score}', True, 'white')
    screen.blit(score_text,(10, 920))
    if powerup:
        pygame.draw.circle(screen, "blue", (140,930),15)
    for i in range(lives):
        # REMOVE: player_images[2].set_colorkey(pygame.Color("magenta"))
        screen.blit(pygame.transform.scale(pacman_right2,(30,30)), (650 + i * 40, 915))    


run = True
while run: 
    #Sets maz fps and fills background black
    timer.tick(fps)
    screen.fill("black")
    draw_boards(level)
    draw_player()
    draw_ui()

    #Wall colision checker
    centre_x = player_x + 23
    centre_y = player_y +24
    turns_allowed = check_position(centre_x,centre_y)

    #player movement
    if moving:
        player_x,player_y = move_player(player_x,player_y)

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
    
    #Startup delay manager
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_p:
                moving = True
            else:
                moving = False



    #Managing the exit function 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
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

