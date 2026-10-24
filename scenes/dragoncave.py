"""Dragon cave scene with the shared gameplay HUD and inventory."""

import pygame
from game_fonts import content1, title

from base_scene import BaseScene
from settings import PARCHMENT, SCREEN_WIDTH, DARK_BROWN


class DragonCaveScene(BaseScene):
    """Placeholder cave view that uses the shared scene controls."""

    def __init__(self, game):
        super().__init__(game)
        self.title_font = title(34)
        self.message_font = content1(23)

    def draw(self, screen):
        screen.fill(PARCHMENT)
        title = self.title_font.render("Hang động của rồng", True, DARK_BROWN)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 250)))
        message = self.message_font.render(
            "Khu vực đang được xây dựng.", True, DARK_BROWN
        )
        screen.blit(message, message.get_rect(center=(SCREEN_WIDTH // 2, 320)))
        super().draw(screen)
