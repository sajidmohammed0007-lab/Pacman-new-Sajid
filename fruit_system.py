# fruit_system.py
import random
import pygame

# =========================
# Configuration / constants
# =========================
FRUIT_CHERRY = "cherry"
FRUIT_STRAWBERRY = "strawberry"

# Adjust if your PNGs are a different intended size
FRUIT_SIZE = 32

# Spawn tuning (in frames)
SPAWN_COOLDOWN_FRAMES = 10 * 60   # attempt spawn every ~10s at 60fps
MAX_ACTIVE_FRUITS = 2            # at most 2 bouncing fruits at once

# Magenta used for transparency in your assets
MAGENTA = (255, 0, 255)

# Image cache (loaded lazily)
FRUIT_IMAGES = None


def load_fruit_images():
    """
    Loads cherry.png and strawberry.png, applies magenta transparency,
    and scales them to FRUIT_SIZE.
    """
    # Change path if your assets folder differs
    cherry = pygame.image.load("Assets/cherry.png").convert()
    strawberry = pygame.image.load("Assets/strawberry.png").convert()

    cherry.set_colorkey(MAGENTA)
    strawberry.set_colorkey(MAGENTA)

    return {
        FRUIT_CHERRY: pygame.transform.scale(cherry, (FRUIT_SIZE, FRUIT_SIZE)),
        FRUIT_STRAWBERRY: pygame.transform.scale(strawberry, (FRUIT_SIZE, FRUIT_SIZE)),
    }


# =========================
# Fruit entity
# =========================
class Fruit:
    def __init__(self, kind: str, x: int, y: int, speed: int = 2):
        global FRUIT_IMAGES
        if FRUIT_IMAGES is None:
            FRUIT_IMAGES = load_fruit_images()

        self.kind = kind
        self.image = FRUIT_IMAGES[kind]

        # store as floats for smoother movement
        self.x = float(x)
        self.y = float(y)
        self.speed = speed

        # direction: 0 right, 1 left, 2 up, 3 down
        self.direction = random.choice([0, 1, 2, 3])

        self.alive = True

        self.width = self.image.get_width()
        self.height = self.image.get_height()

    @property
    def center(self):
        return (int(self.x), int(self.y))

    def rect(self):
        # collision rect centered on fruit
        return pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height,
        )

    def _can_move_dir(self, level, tile_w, tile_h, d: int) -> bool:
        """
        Checks if the fruit can move in direction d based on the tile map.
        Walkable = values < 3 (matches your Pac-Man collision logic).
        """
        cx, cy = self.center
        probe = self.width // 2 + 2  # small forward probe beyond sprite edge

        nx, ny = cx, cy
        if d == 0:      # right
            nx += probe
        elif d == 1:    # left
            nx -= probe
        elif d == 2:    # up
            ny -= probe
        elif d == 3:    # down
            ny += probe

        r = int(ny // tile_h)
        c = int(nx // tile_w)

        if r < 0 or c < 0 or r >= len(level) or c >= len(level[0]):
            return False

        return level[r][c] < 3  # walkable

    def _available_dirs(self, level, tile_w, tile_h):
        return [d for d in (0, 1, 2, 3) if self._can_move_dir(level, tile_w, tile_h, d)]

    def update(self, level, tile_w: int, tile_h: int):
        """
        Bounce/roam movement:
        - If current direction becomes blocked, pick a new valid direction.
        - Occasionally change direction at junctions (3+ available turns).
        """
        if not self.alive:
            return

        avail = self._available_dirs(level, tile_w, tile_h)
        if not avail:
            return

        # if blocked, pick new direction
        if self.direction not in avail:
            self.direction = random.choice(avail)
        else:
            # at junctions, sometimes turn
            if len(avail) >= 3 and random.random() < 0.12:
                opposite = {0: 1, 1: 0, 2: 3, 3: 2}[self.direction]
                choices = [d for d in avail if d != opposite] or avail
                self.direction = random.choice(choices)

        # move in chosen direction
        if self.direction == 0:
            self.x += self.speed
        elif self.direction == 1:
            self.x -= self.speed
        elif self.direction == 2:
            self.y -= self.speed
        elif self.direction == 3:
            self.y += self.speed

    def draw(self, screen):
        if not self.alive:
            return
        screen.blit(
            self.image,
            (int(self.x - self.width // 2), int(self.y - self.height // 2)),
        )


# =========================
# Fruit manager
# =========================
class FruitManager:
    """
    Manages spawning, updating, drawing, and collecting fruits.
    Keeps a record of collected fruit types for UI display later.
    """

    def __init__(self):
        self.active = []        # list[Fruit]
        self.collected = []     # list[str] (fruit kind)
        self._spawn_timer = 0

    def reset(self):
        self.active.clear()
        self.collected.clear()
        self._spawn_timer = 0

    def _random_walkable_spawn(self, level, tile_w, tile_h):
        """
        Picks a random walkable tile (<3) and returns pixel center.
        Tries a limited number of attempts for safety.
        """
        rows = len(level)
        cols = len(level[0])

        for _ in range(300):
            r = random.randrange(rows)
            c = random.randrange(cols)
            if level[r][c] < 3:
                x = int(c * tile_w + tile_w * 0.5)
                y = int(r * tile_h + tile_h * 0.5)
                return x, y

        return None

    def try_spawn(self, level, tile_w, tile_h):
        """
        Spawns a fruit if we have room. Randomly chooses cherry/strawberry.
        """
        if len(self.active) >= MAX_ACTIVE_FRUITS:
            return

        pos = self._random_walkable_spawn(level, tile_w, tile_h)
        if not pos:
            return

        kind = random.choice([FRUIT_CHERRY, FRUIT_STRAWBERRY])
        fx, fy = pos
        self.active.append(Fruit(kind, fx, fy, speed=2))

    def update(self, level, tile_w, tile_h):
        """
        Call every frame.
        - Move fruits
        - Spawn a fruit periodically
        """
        # update existing fruits
        for f in self.active:
            f.update(level, tile_w, tile_h)

        # remove dead fruits
        self.active = [f for f in self.active if f.alive]

        # spawn timer
        self._spawn_timer += 1
        if self._spawn_timer >= SPAWN_COOLDOWN_FRAMES:
            self._spawn_timer = 0
            # 70% chance to spawn on each cooldown tick (tweak if needed)
            if random.random() < 0.7:
                self.try_spawn(level, tile_w, tile_h)

    def draw(self, screen):
        for f in self.active:
            f.draw(screen)

    def check_collect(self, player_rect):
        """
        If the player's rect overlaps a fruit rect, mark collected.
        Returns list of collected fruit kinds this frame.
        """
        picked = []
        for f in self.active:
            if f.alive and player_rect.colliderect(f.rect()):
                f.alive = False
                self.collected.append(f.kind)
                picked.append(f.kind)
        return picked
