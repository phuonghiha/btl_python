
import pygame

from scene import Scene
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DARK_BLUE,
    GOLD,
    WHITE,
    DARK_GREEN,
)


class StartScene(Scene):
    def __init__(self, game):
        super().__init__(game)

        self.title_font = pygame.font.Font(None, 86)
        self.button_font = pygame.font.Font(None, 48)

        self.start_button = pygame.Rect(
            SCREEN_WIDTH // 2 - 200,
            SCREEN_HEIGHT // 2 + 100,
            400,
            100,
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.start_button.collidepoint(event.pos):
                    self.game.change_scene("intro")

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.change_scene("intro")

    def draw(self, screen):
        screen.fill(DARK_BLUE)

        title = self.title_font.render(
            "HANH TRINH GIAI CUU CONG CHUA",
            True,
            GOLD,
        )

        screen.blit(
            title,
            title.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
            ),
        )

        pygame.draw.rect(
            screen,
            DARK_GREEN,
            self.start_button,
            border_radius=16,
        )

        text = self.button_font.render(
            "Bat dau choi",
            True,
            WHITE,
        )

        screen.blit(
            text,
            text.get_rect(center=self.start_button.center),
        )
