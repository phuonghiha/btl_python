
import pygame

from scene import Scene
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DARK_BROWN,
    DARK_GREEN,
    GOLD,
    WHITE,
    RED,
)

# Dùng chung ảnh nền và font đã khai báo trong start_scene.py
from scenes.start_scene import (
    load_font,
    load_background,
    TITLE_FONT_PATH,
    DIALOGUE_FONT_PATH,
)


class IntroScene(Scene):
    def __init__(self, game):
        super().__init__(game)

        self.background = load_background()

        self.title_font = load_font(
            TITLE_FONT_PATH, 38
        )
        self.dialogue_font = load_font(
            DIALOGUE_FONT_PATH, 27
        )
        self.button_font = load_font(
            DIALOGUE_FONT_PATH, 23
        )

        # Nút nhận chiếu chỉ
        self.accept_button = pygame.Rect(
            SCREEN_WIDTH // 2 - 275,
            SCREEN_HEIGHT - 115,
            255,
            65,
        )

        # Nút từ chối
        self.refuse_button = pygame.Rect(
            SCREEN_WIDTH // 2 + 20,
            SCREEN_HEIGHT - 115,
            255,
            65,
        )

        self.dialogue_lines = [
            "Hỡi hiệp sĩ của vương quốc!",
            "Công chúa đã mất tích một cách bí ẩn.",
            "Ta giao cho ngươi nhiệm vụ điều tra",
            "và tìm nàng trở về an toàn.",
            "Hãy lên đường và khám phá sự thật!",
        ]

    def handle_event(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if self.accept_button.collidepoint(event.pos):
                # Nhận chiếu chỉ -> phòng công chúa
                self.game.change_scene("princess_room")

            elif self.refuse_button.collidepoint(event.pos):
                # Từ chối -> màn hình bắt đầu
                self.game.change_scene("start")

    def update(self, dt):
        pass

    def draw(self, screen):
        # Vẽ nền giấy da
        screen.blit(self.background, (0, 0))

        # Khung chiếu chỉ
        panel = pygame.Rect(
            90,
            45,
            SCREEN_WIDTH - 180,
            SCREEN_HEIGHT - 190,
        )

        pygame.draw.rect(
            screen,
            (247, 235, 204),
            panel,
            border_radius=18,
        )
        pygame.draw.rect(
            screen,
            DARK_BROWN,
            panel,
            width=4,
            border_radius=18,
        )

        # Tiêu đề
        title = self.title_font.render(
            "CHIẾU CHỈ HOÀNG GIA",
            True,
            DARK_BROWN,
        )

        screen.blit(
            title,
            title.get_rect(
                center=(SCREEN_WIDTH // 2, 115)
            ),
        )

        # Nội dung lời thoại
        y = 205

        for line in self.dialogue_lines:
            text = self.dialogue_font.render(
                line,
                True,
                DARK_BROWN,
            )

            screen.blit(
                text,
                text.get_rect(
                    center=(SCREEN_WIDTH // 2, y)
                ),
            )

            y += 45

        # Vẽ nút nhận chiếu chỉ
        pygame.draw.rect(
            screen,
            DARK_GREEN,
            self.accept_button,
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            GOLD,
            self.accept_button,
            width=3,
            border_radius=10,
        )

        accept_text = self.button_font.render(
            "NHẬN CHIẾU CHỈ",
            True,
            WHITE,
        )

        screen.blit(
            accept_text,
            accept_text.get_rect(
                center=self.accept_button.center
            ),
        )

        # Vẽ nút từ chối
        pygame.draw.rect(
            screen,
            RED,
            self.refuse_button,
            border_radius=10,
        )
        pygame.draw.rect(
            screen,
            GOLD,
            self.refuse_button,
            width=3,
            border_radius=10,
        )

        refuse_text = self.button_font.render(
            "TỪ CHỐI",
            True,
            WHITE,
        )

        screen.blit(
            refuse_text,
            refuse_text.get_rect(
                center=self.refuse_button.center
            ),
        )
