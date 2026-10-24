
import pygame
from game_fonts import content1, title

from scene import Scene
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PARCHMENT,
    DARK_BROWN,
    DARK_GREEN,
    GOLD,
    WHITE,
    RED,
)

from scenes.start_scene import (
    load_font,
    load_background,
    TITLE_FONT_PATH,
    DIALOGUE_FONT_PATH,
)


class GameOverScene(Scene):
    def __init__(self, game):
        super().__init__(game)

        self.background = load_background()

        self.title_font = title(55)
        self.message_font = content1(29)
        self.button_font = content1(28)

        self.restart_button = pygame.Rect(
            SCREEN_WIDTH // 2 - 175,
            SCREEN_HEIGHT // 2 + 90,
            350,
            75,
        )

    def handle_event(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.restart_button.collidepoint(event.pos)
        ):
            self.game.restart_game()

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.blit(self.background, (0, 0))

        title = self.title_font.render(
            "Game over",
            True,
            RED,
        )
        screen.blit(
            title,
            title.get_rect(
                center=(SCREEN_WIDTH // 2, 245)
            ),
        )

        message = self.message_font.render(
            "Bạn đã kiệt sức trong hành trình.",
            True,
            DARK_BROWN,
        )
        screen.blit(
            message,
            message.get_rect(
                center=(SCREEN_WIDTH // 2, 325)
            ),
        )

        pygame.draw.rect(
            screen,
            DARK_GREEN,
            self.restart_button,
            border_radius=12,
        )
        pygame.draw.rect(
            screen,
            GOLD,
            self.restart_button,
            width=3,
            border_radius=12,
        )

        text = self.button_font.render(
            "CHƠI LẠI",
            True,
            WHITE,
        )
        screen.blit(
            text,
            text.get_rect(
                center=self.restart_button.center
            ),
        )
