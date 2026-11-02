"""Princess character sprite used in the dragon cave rescue scene."""

from pathlib import Path

import pygame


SPRITE_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "sprites"
    / "princess"
    / "princess_3.png"
)


class Princess:
    def __init__(self):
        self.image = pygame.image.load(str(SPRITE_PATH)).convert_alpha()

    def draw(self, screen, center, size):
        image = pygame.transform.smoothscale(self.image, size)
        screen.blit(image, image.get_rect(center=center))
