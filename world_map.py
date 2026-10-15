
import pygame

from scene import Scene
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PARCHMENT,
    DARK_BROWN,
    DARK_GREEN,
    GOLD,
    WHITE,
)


class WorldMap(Scene):
    def __init__(self, game):
        super().__init__(game)

        self.title_font = pygame.font.SysFont(
            "arial", 38, bold=True
        )
        self.button_font = pygame.font.SysFont(
            "arial", 25, bold=True
        )
        self.help_font = pygame.font.SysFont(
            "arial", 20
        )

        button_width = 330
        button_height = 75
        center_x = SCREEN_WIDTH // 2

        self.locations = [
            (
                "Phòng công chúa",
                "princess_room",
                pygame.Rect(
                    center_x - button_width // 2,
                    160,
                    button_width,
                    button_height,
                ),
            ),
            (
                "Rừng tinh linh",
                "spirit_forest",
                pygame.Rect(
                    center_x - button_width // 2,
                    255,
                    button_width,
                    button_height,
                ),
            ),
            (
                "Đầm lầy độc",
                "poison_swamp",
                pygame.Rect(
                    center_x - button_width // 2,
                    350,
                    button_width,
                    button_height,
                ),
            ),
            (
                "Hang động của rồng",
                "dragon_cave",
                pygame.Rect(
                    center_x - button_width // 2,
                    445,
                    button_width,
                    button_height,
                ),
            ),
        ]

    def handle_event(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            for name, scene_id, rect in self.locations:
                if rect.collidepoint(event.pos):
                    self.game.change_scene(scene_id)
                    return

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(PARCHMENT)

        title = self.title_font.render(
            "BẢN ĐỒ VƯƠNG QUỐC",
            True,
            DARK_BROWN,
        )
        screen.blit(
            title,
            title.get_rect(
                center=(SCREEN_WIDTH // 2, 85)
            ),
        )

        for name, scene_id, rect in self.locations:
            pygame.draw.rect(
                screen,
                DARK_GREEN,
                rect,
                border_radius=10,
            )
            pygame.draw.rect(
                screen,
                GOLD,
                rect,
                width=3,
                border_radius=10,
            )

            text = self.button_font.render(
                name,
                True,
                WHITE,
            )
            screen.blit(
                text,
                text.get_rect(center=rect.center),
            )

        help_text = self.help_font.render(
            "Nhấn ESC để quay lại khu vực trước đó",
            True,
            DARK_BROWN,
        )
        screen.blit(
            help_text,
            help_text.get_rect(
                center=(SCREEN_WIDTH // 2, 570)
            ),
        )
