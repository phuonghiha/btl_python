
import os
import pygame
from game_fonts import content1, title

from scene import Scene
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DARK_BROWN,
    DARK_GREEN,
    GOLD,
    WHITE,
)

# Đường dẫn gốc của dự án
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Ảnh giấy da
BACKGROUND_PATH = os.path.join(
    BASE_DIR,
    "assets",
    "images",
    "parchment.jpg",
)

# Font tiêu đề
TITLE_FONT_PATH = os.path.join(
    BASE_DIR,
    "assets",
    "fonts",
    "cinzel",
    "CinzelDecorative-Black.otf",
)

# Font lời thoại và nút
DIALOGUE_FONT_PATH = os.path.join(
    BASE_DIR,
    "assets",
    "fonts",
    "eb-garamond",
    "EBGaramond-Regular.ttf",
)


def load_font(path, size, bold=False):
    """Tải font từ đường dẫn; dùng font hệ thống nếu thiếu."""
    if os.path.isfile(path):
        return pygame.font.Font(path, size)

    print(f"Không tìm thấy font: {path}")
    return pygame.font.SysFont("arial", size, bold=bold)


def load_background():
    """Tải ảnh giấy da và điều chỉnh theo kích thước màn hình."""
    if os.path.isfile(BACKGROUND_PATH):
        image = pygame.image.load(
            BACKGROUND_PATH
        ).convert()

        return pygame.transform.smoothscale(
            image,
            (SCREEN_WIDTH, SCREEN_HEIGHT),
        )

    print(f"Không tìm thấy ảnh nền: {BACKGROUND_PATH}")

    background = pygame.Surface(
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )
    background.fill((239, 222, 180))
    return background


class StartScene(Scene):
    def __init__(self, game):
        super().__init__(game)

        self.background = load_background()

        self.title_font = title(60)
        self.button_font = content1(30)

        self.start_button = pygame.Rect(
            SCREEN_WIDTH // 2 - 175,
            SCREEN_HEIGHT - 180,
            350,
            75,
        )

    def handle_event(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if self.start_button.collidepoint(event.pos):
                self.game.change_scene("intro")

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.blit(self.background, (0, 0))

        title1 = self.title_font.render(
            "Hành trình giải cứu",
            True,
            DARK_BROWN,
        )
        title2 = self.title_font.render(
            "Công chúa",
            True,
            DARK_BROWN,
        )

        screen.blit(
            title1,
            title1.get_rect(
                center=(SCREEN_WIDTH // 2, 235)
            ),
        )
        screen.blit(
            title2,
            title2.get_rect(
                center=(SCREEN_WIDTH // 2, 305)
            ),
        )

        # Vẽ nút bắt đầu
        pygame.draw.rect(
            screen,
            DARK_GREEN,
            self.start_button,
            border_radius=12,
        )

        text = self.button_font.render(
            "BẮT ĐẦU CHƠI",
            True,
            WHITE,
        )

        screen.blit(
            text,
            text.get_rect(
                center=self.start_button.center
            ),
        )
