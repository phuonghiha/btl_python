
import pygame

from scene import Scene
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BLUE,
    WHITE,
    DARK_GREEN,
)


class PlaceholderScene(Scene):
    def __init__(self, game, title):
        super().__init__(game)

        self.title = title
        self.title_font = pygame.font.Font(None, 72)
        self.message_font = pygame.font.Font(None, 38)

        self.back_button = pygame.Rect(
            30, 25, 180, 70
        )

        self.test_damage_button = pygame.Rect(
            30, 115, 300, 70
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.back_button.collidepoint(event.pos):
                    self.game.change_scene("world_map")
                    return

                # Nut thu nghiem de kiem tra Game Over.
                if self.test_damage_button.collidepoint(event.pos):
                    self.game.game_state.take_damage(25)

    def draw(self, screen):
        screen.fill(BLUE)

        title = self.title_font.render(
            self.title,
            True,
            WHITE,
        )

        screen.blit(
            title,
            title.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)
            ),
        )

        message = self.message_font.render(
            "Day la man choi tam de kiem tra Core",
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
            self.back_button,
            border_radius=12,
        )

        back_text = self.message_font.render(
            "Quay lai",
            True,
            WHITE,
        )

        screen.blit(
            back_text,
            back_text.get_rect(center=self.back_button.center),
        )

        pygame.draw.rect(
            screen,
            (120, 60, 60),
            self.test_damage_button,
            border_radius=12,
        )

        damage_text = self.message_font.render(
            "Thu tru HP",
            True,
            WHITE,
        )

        screen.blit(
            damage_text,
            damage_text.get_rect(
                center=self.test_damage_button.center
            ),
        )
