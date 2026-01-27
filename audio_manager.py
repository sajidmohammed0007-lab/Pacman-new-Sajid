import pygame

class AudioManager:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()

        # Music
        self.menu_music = "Assets/audio/menu_music.ogg"
        self.level_music = "Assets/audio/level_music.ogg"
        self.current_music = None

        # Sound effects
        self.sfx_pellet = pygame.mixer.Sound("Assets/audio/pellet.wav")
        self.sfx_power = pygame.mixer.Sound("Assets/audio/power.wav")
        self.sfx_ghost = pygame.mixer.Sound("Assets/audio/ghost_eaten.wav")
        self.sfx_die = pygame.mixer.Sound("Assets/audio/player_die.wav")
        self.sfx_win = pygame.mixer.Sound("Assets/audio/win.wav")
        self.sfx_game_over = pygame.mixer.Sound("Assets/audio/game_over.wav")
        self.sfx_start = pygame.mixer.Sound("Assets/audio/start.wav")

        pygame.mixer.music.set_volume(0.35)

    def play_music(self, kind):
        if self.current_music == kind:
            return
        self.current_music = kind
        pygame.mixer.music.stop()

        if kind == "menu":
            pygame.mixer.music.load(self.menu_music)
            pygame.mixer.music.play(-1)
        elif kind == "level":
            pygame.mixer.music.load(self.level_music)
            pygame.mixer.music.play(-1)

    # --- Sound effect wrappers ---
    def pellet(self):
        self.sfx_pellet.play()

    def power(self):
        self.sfx_power.play()

    def ghost_eaten(self):
        self.sfx_ghost.play()

    def player_die(self):
        self.sfx_die.play()

    def win(self):
        self.sfx_win.play()

    def game_over(self):
        self.sfx_game_over.play()

    def start(self):
        self.sfx_start.play()
