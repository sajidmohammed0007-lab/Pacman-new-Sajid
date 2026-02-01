# fruit_system.py
import random
import pygame

# configuration 

# fruit type labels (stored in csv / used in logic)
fruit_cherry = "cherry"
fruit_strawberry = "strawberry"

# fruit display size (pixels)
fruit_size = 32

# spawn tuning (in frames)
# 2 * 60 = 120 frames which is ~2 seconds at 60 fps
spawn_cooldown_frames = 2 * 60

# at most this many fruits bouncing around at one time
max_active_fruits = 2

# color key for transparency (magenta)
magenta = (255, 0, 255)

fruit_images = None


def load_fruit_images():
    """
    Load cherry.png and strawberry.png, apply magenta transparency,
    and scale them to fruit_size so they match your game sprites.
    """
    cherry_img = pygame.image.load("Assets/cherry.png").convert()
    strawberry_img = pygame.image.load("Assets/strawberry.png").convert()

    # remove magenta background
    cherry_img.set_colorkey(magenta)
    strawberry_img.set_colorkey(magenta)

    # scale to consistent size
    return {
        fruit_cherry: pygame.transform.scale(cherry_img, (fruit_size, fruit_size)),
        fruit_strawberry: pygame.transform.scale(strawberry_img, (fruit_size, fruit_size)),
    }


# fruit entity
class Fruit:
    """
    A fruit that roams around the maze like an npc:
    - moves every frame
    - only chooses a new direction when it reaches a tile centre
    - avoids instantly reversing direction unless forced
    """

    def __init__(self, kind: str, x: int, y: int, speed: int = 2):
        # load images  
        global fruit_images
        if fruit_images is None:
            fruit_images = load_fruit_images()

        # identity + sprite
        self.kind = kind
        self.image = fruit_images[kind]

        # store position as floats for smoother movement
        self.x = float(x)
        self.y = float(y)

        # speed in pixels per frame
        self.speed = int(speed)

        # direction codes: 0 right, 1 left, 2 up, 3 down
        self.direction = random.choice([0, 1, 2, 3])

        # alive controls whether it is still active on the map
        self.alive = True

        # sprite size used for collision rectangles
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # prevents “shaking” by ensuring we only decide once per tile
        self._last_decision_tile = None

    def get_centre(self):
        """Return the fruit centre position as ints (for tile calculations)."""
        return (int(self.x), int(self.y))

    def rect(self):
        """
        Return a pygame.Rect for collision checks.
        The rect is centred on the fruit sprite.
        """
        return pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height,
        )

    # grid helper methods
    def _tile_rc_from_centre(self, tile_w, tile_h):
        """Convert the fruit centre position into tile row/col."""
        cx, cy = self.get_centre()
        r = int(cy // tile_h)
        c = int(cx // tile_w)
        return r, c

    def _near_tile_centre(self, tile_w, tile_h, tolerance=2):
        """
        Check if the fruit is close enough to the exact tile centre to make a decision.
        tolerance stops it being too strict (useful because speed may skip exact pixels).
        """
        cx, cy = self.get_centre()
        r = int(cy // tile_h)
        c = int(cx // tile_w)

        tile_cx = int(c * tile_w + tile_w * 0.5)
        tile_cy = int(r * tile_h + tile_h * 0.5)

        return abs(cx - tile_cx) <= tolerance and abs(cy - tile_cy) <= tolerance

    def _is_walkable_tile(self, level, r, c):
        """
        Define which tiles the fruit is allowed to travel through.
          0 = empty path, 1 = pellet path, 2 = power pellet path
        """
        if r < 0 or c < 0 or r >= len(level) or c >= len(level[0]):
            return False
        return level[r][c] in (0, 1, 2)

    def _available_dirs_from_tile(self, level, r, c):
        """
        Look at the four neighbouring tiles and return which directions are valid.
        """
        dirs = []
        if self._is_walkable_tile(level, r, c + 1):  # right
            dirs.append(0)
        if self._is_walkable_tile(level, r, c - 1):  # left
            dirs.append(1)
        if self._is_walkable_tile(level, r - 1, c):  # up
            dirs.append(2)
        if self._is_walkable_tile(level, r + 1, c):  # down
            dirs.append(3)
        return dirs

    def _snap_to_tile_centre(self, tile_w, tile_h, r, c):
        """
        Snap the fruit exactly to the tile centre.
        This prevents drift and reduces jitter at junctions.
        """
        tile_cx = int(c * tile_w + tile_w * 0.5)
        tile_cy = int(r * tile_h + tile_h * 0.5)
        self.x = float(tile_cx)
        self.y = float(tile_cy)

    # ---------------------------
    # movement logic
    # ---------------------------
    def update(self, level, tile_w: int, tile_h: int):
        """
        Move the fruit:
        - decide direction only at tile centres
        - avoid reversing direction unless forced
        - move every frame
        """
        if not self.alive:
            return

        r, c = self._tile_rc_from_centre(tile_w, tile_h)

        # only decide direction at the centre of the tile (and only once per tile)
        if self._near_tile_centre(tile_w, tile_h, tolerance=2) and self._last_decision_tile != (r, c):
            avail = self._available_dirs_from_tile(level, r, c)

            if avail:
                opposite = {0: 1, 1: 0, 2: 3, 3: 2}[self.direction]

                # if our current direction is blocked, we must pick a new one
                if self.direction not in avail:
                    choices = [d for d in avail if d != opposite] or avail
                    self.direction = random.choice(choices)
                else:
                    # at a junction (3+ options), sometimes turn
                    if len(avail) >= 3 and random.random() < 0.20:
                        choices = [d for d in avail if d != opposite] or avail
                        self.direction = random.choice(choices)

                # snap once to reduce drift/jitter at decision points
                self._snap_to_tile_centre(tile_w, tile_h, r, c)

            # mark that we already chose a direction for this tile
            self._last_decision_tile = (r, c)

        # continuous movement each frame
        if self.direction == 0:
            self.x += self.speed
        elif self.direction == 1:
            self.x -= self.speed
        elif self.direction == 2:
            self.y -= self.speed
        elif self.direction == 3:
            self.y += self.speed

    def draw(self, screen):
        """Draw the fruit sprite centred at (x, y)."""
        if not self.alive:
            return
        screen.blit(
            self.image,
            (int(self.x - self.width // 2), int(self.y - self.height // 2)),
        )



# fruit manager
class FruitManager:
    """
    Manages:
    - spawning fruits
    - updating fruit movement
    - drawing fruits
    - detecting collection by the player
    """

    def __init__(self):
        # currently active fruit objects on the map
        self.active = []        # list of Fruit objects

        # record of collected fruit types (useful for later UI display)
        self.collected = []     # list of strings

        # spawn timer counts frames between spawn attempts
        self._spawn_timer = 0

    def reset(self):
        """Reset fruit system for a new game."""
        self.active.clear()
        self.collected.clear()
        self._spawn_timer = 0

    def _random_pellet_spawn(self, level, tile_w, tile_h):
        """
        Spawn ONLY on small pellet tiles (value == 1).
        This avoids ghost box and unreachable areas because pellets only exist on valid paths.
        Returns (x, y) pixel centre or None if it fails.
        """
        rows = len(level)
        cols = len(level[0])

        # try several times before giving up
        for _ in range(600):
            r = random.randrange(rows)
            c = random.randrange(cols)

            if level[r][c] == 1:
                x = int(c * tile_w + tile_w * 0.5)
                y = int(r * tile_h + tile_h * 0.5)
                return x, y

        return None

    def try_spawn(self, level, tile_w, tile_h):
        """Spawn a fruit if we are below the active limit and we find a valid pellet tile."""
        if len(self.active) >= max_active_fruits:
            return

        pos = self._random_pellet_spawn(level, tile_w, tile_h)
        if not pos:
            return

        # weighted choice: cherry twice as likely as strawberry (2:1)
        kind = random.choice([fruit_cherry, fruit_cherry, fruit_strawberry])

        fx, fy = pos
        self.active.append(Fruit(kind, fx, fy, speed=2))

    def update(self, level, tile_w, tile_h):
        """Update all fruit movement and handle periodic spawning."""
        # move each fruit
        for f in self.active:
            f.update(level, tile_w, tile_h)

        # remove any fruits that were collected / killed
        self.active = [f for f in self.active if f.alive]

        # update spawn timer
        self._spawn_timer += 1
        if self._spawn_timer >= spawn_cooldown_frames:
            self._spawn_timer = 0

            # spawn chance each cooldown tick (tweak as needed)
            if random.random() < 0.7:
                self.try_spawn(level, tile_w, tile_h)

    def draw(self, screen):
        """Draw all active fruits."""
        for f in self.active:
            f.draw(screen)

    def check_collect(self, player_rect):
        """
        Check if the player touches a fruit.
        Marks fruit as collected and returns a list of collected fruit kinds this frame.
        """
        picked = []
        for f in self.active:
            if f.alive and player_rect.colliderect(f.rect()):
                f.alive = False
                self.collected.append(f.kind)
                picked.append(f.kind)
        return picked
