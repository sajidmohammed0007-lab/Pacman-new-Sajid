import pygame

class SpriteSheet:
    def __init__(self, image):
        self.sheet = image

    def get_image(self, framex, framey, width, height, scale=1, colour1=None):
        # Extract frame from spritesheet
        image = pygame.Surface((width, height)).convert()
        image.blit(self.sheet, (0, 0), (framex * width, framey * height, width, height))

        # Apply transparency if requested
        if colour1:
            image.set_colorkey(pygame.Color(colour1))

        # Scale up or down
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))

        # Preserve transparency
        image = image.convert_alpha()

        return image