
import pygame
from game_fonts import content1, title

from scene import Scene
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PARCHMENT,
    DARK_BROWN,
    DARK_GREEN,
    RED,
    WHITE,
)


class PlaceholderScene(Scene):
    def __init__(self, game, scene_name):
        super().__init__(game)
        self.scene_name = scene_name

        self.font = title(34)
        self.small_font = content1(23)

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(PARCHMENT)

        title = self.font.render(
            self.scene_name,
            True,
            DARK_BROWN,
        )
        screen.blit(
            title,
            title.get_rect(
                center=(SCREEN_WIDTH // 2, 250)
            ),
        )

        message = self.small_font.render(
            "Khu vực đang được xây dựng.",
            True,
            DARK_BROWN,
        )
        screen.blit(
            message,
            message.get_rect(
                center=(SCREEN_WIDTH // 2, 320)
            ),
        )

        # Thanh máu
        bar_x = 40
        bar_y = 35
        bar_width = 250
        bar_height = 28

        pygame.draw.rect(
            screen,
            DARK_BROWN,
            (bar_x, bar_y, bar_width, bar_height),
            border_radius=5,
        )

        health_ratio = (
            self.game_state.health
            / self.game_state.max_health
        )

        current_width = int(
            (bar_width - 4) * health_ratio
        )

        if current_width > 0:
            pygame.draw.rect(
                screen,
                RED,
                (
                    bar_x + 2,
                    bar_y + 2,
                    current_width,
                    bar_height - 4,
                ),
                border_radius=4,
            )

        health_text = self.small_font.render(
            f"Máu: {self.game_state.health}/"
            f"{self.game_state.max_health}",
            True,
            DARK_BROWN,
        )
        screen.blit(
            health_text,
            (bar_x, bar_y + 38),
        )
