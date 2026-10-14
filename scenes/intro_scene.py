
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


class IntroScene(Scene):
    def __init__(self, game):
        super().__init__(game)

        self.title_font = pygame.font.Font(None, 76)
        self.dialogue_font = pygame.font.Font(None, 44)
        self.button_font = pygame.font.Font(None, 44)

        self.continue_button = pygame.Rect(
            SCREEN_WIDTH // 2 - 200,
            SCREEN_HEIGHT - 220,
            400,
            90,
        )

        self.dialogue_lines = [
            "Hiep si, ta co mot nhiem vu quan trong giao cho nguoi.",
            "Cong chua cua vuong quoc da dot nhien mat tich.",
            "Ta khong biet ai dung sau viec nay.",
            "Hay den phong cong chua, tim manh moi",
            "va dua cong chua tro ve an toan.",
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.continue_button.collidepoint(event.pos):
                    self.game.change_scene("princess_room")

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.change_scene("princess_room")

    def draw(self, screen):
        screen.fill(DARK_BLUE)

        title = self.title_font.render(
            "LOI NHAN CUA DUC VUA",
            True,
            GOLD,
        )

        screen.blit(
            title,
            title.get_rect(
                center=(SCREEN_WIDTH // 2, 220)
            ),
        )

        y = 420

        for line in self.dialogue_lines:
            text = self.dialogue_font.render(
                line,
                True,
                WHITE,
            )

            screen.blit(
                text,
                text.get_rect(
                    center=(SCREEN_WIDTH // 2, y)
                ),
            )

            y += 65

        pygame.draw.rect(
            screen,
            DARK_GREEN,
            self.continue_button,
            border_radius=16,
        )

        button_text = self.button_font.render(
            "Tiep tuc",
            True,
            WHITE,
        )

        screen.blit(
            button_text,
            button_text.get_rect(
                center=self.continue_button.center
            ),
        )
