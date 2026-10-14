
import pygame

from scene import Scene
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DARK_BLUE,
    RED,
    WHITE,
    DARK_GREEN,
)


class GameOverScene(Scene):
    def __init__(self, game):
        super().__init__(game)

        self.title_font = pygame.font.Font(None, 100)
        self.message_font = pygame.font.Font(None, 42)
        self.button_font = pygame.font.Font(None, 42)

        self.restart_button = pygame.Rect(
            SCREEN_WIDTH // 2 - 260,
            SCREEN_HEIGHT // 2 + 100,
            520,
            100,
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.restart_button.collidepoint(event.pos):
                    self.game.game_state.reset()
                    self.game.change_scene("start")

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.game_state.reset()
                self.game.change_scene("start")

    def draw(self, screen):
        screen.fill(DARK_BLUE)

        title = self.title_font.render(
            "BAN DA THUA CUOC!",
            True,
            RED,
        )

        screen.blit(
            title,
            title.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120)
            ),
        )

        message = self.message_font.render(
            "Ban da het mau. Hay thu lai!",
            True,
            WHITE,
        )

        screen.blit(
            message,
            message.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            ),
        )

        pygame.draw.rect(
            screen,
            DARK_GREEN,
            self.restart_button,
            border_radius=16,
        )

        button_text = self.button_font.render(
            "Ve man hinh bat dau",
            True,
            WHITE,
        )

        screen.blit(
            button_text,
            button_text.get_rect(
                center=self.restart_button.center
            ),
        )
