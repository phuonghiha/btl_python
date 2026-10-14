
import pygame

from scene import Scene
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GREEN,
    DARK_GREEN,
    GOLD,
    WHITE,
)


class WorldMap(Scene):
    def __init__(self, game):
        super().__init__(game)

        self.title_font = pygame.font.Font(None, 76)
        self.font = pygame.font.Font(None, 44)

        self.back_button = pygame.Rect(30, 25, 180, 70)

        width = 500
        height = 110
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        locations = [
            ("princess_room", "Phong cong chua"),
            ("spirit_forest", "Rung tinh linh"),
            ("poison_swamp", "Dam lay doc"),
            ("dragon_cave", "Hang dong rong"),
        ]

        self.buttons = []

        for index, (scene_id, label) in enumerate(locations):
            rect = pygame.Rect(
                center_x - width // 2,
                center_y - 245 + index * 135,
                width,
                height,
            )

            self.buttons.append((scene_id, label, rect))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.back_button.collidepoint(event.pos):
                    self.game.change_scene(
                        self.game.previous_scene_id
                    )
                    return

                for scene_id, label, rect in self.buttons:
                    if rect.collidepoint(event.pos):
                        self.game.change_scene(scene_id)
                        return

    def draw(self, screen):
        screen.fill(GREEN)

        title = self.title_font.render(
            "WORLD MAP",
            True,
            WHITE,
        )

        screen.blit(
            title,
            title.get_rect(
                center=(SCREEN_WIDTH // 2, 150)
            ),
        )

        pygame.draw.rect(
            screen,
            DARK_GREEN,
            self.back_button,
            border_radius=12,
        )

        back_text = self.font.render(
            "Quay lai",
            True,
            WHITE,
        )

        screen.blit(
            back_text,
            back_text.get_rect(center=self.back_button.center),
        )

        for scene_id, label, rect in self.buttons:
            pygame.draw.rect(
                screen,
                DARK_GREEN,
                rect,
                border_radius=16,
            )

            pygame.draw.rect(
                screen,
                GOLD,
                rect,
                width=3,
                border_radius=16,
            )

            text = self.font.render(
                label,
                True,
                WHITE,
            )

            screen.blit(
                text,
                text.get_rect(center=rect.center),
            )
