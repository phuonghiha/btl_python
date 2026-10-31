"""Câu đố Hang Rồng đầu tiên: đếm năm loại ngọc và nhập mật mã."""

from pathlib import Path
import random

import pygame

from scene import Scene
from game_fonts import content1
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENE_ASSET_DIR = PROJECT_ROOT / "assets" / "images" / "sence_4"
GEM_FILES = {
    "black": "black.png",
    "blue": "blue.png",
    "pink": "pink.png",
    "red": "red.png",
    "yellow": "yellow.png",
}
GEM_NAMES = tuple(GEM_FILES)

GOLD = (255, 190, 82)
CREAM = (255, 244, 220)
RED = (229, 105, 84)
GREEN = (139, 199, 132)


class DragonCave1Scene(Scene):
    """Puzzle scene that can be hosted by Game or launched from its test."""

    def __init__(self, game, on_solved=None):
        super().__init__(game)
        self.on_solved = on_solved
        self.background_closed = self._load_scaled("gate.png")
        self.background_open = self._load_scaled("dragon_cave.png")
        self.gem_images = {
            name: self._load_gem(name, 62)
            for name in GEM_NAMES
        }

        self.body_font = content1(20)
        self.button_font = content1(21)

        self.gem_row_top_rects = self._make_row_rects(5, 62, 34, 218)
        self.gem_row_bottom_rects = self._make_row_rects(10, 62, 34, 348)
        self.slot_rects = [
            pygame.Rect(407 + index * 98, 478, 74, 74)
            for index in range(5)
        ]
        self.confirm_rect = pygame.Rect(522, 584, 236, 44)
        self.continue_rect = pygame.Rect(522, 584, 236, 44)
        self.message_rect = pygame.Rect(120, 654, 1040, 40)

        self.overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self.overlay.fill((10, 8, 10, 105))
        self.gate_overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self.gate_open_alpha = 0
        self.message = ""
        self.message_color = CREAM
        self.solved = False
        self.message_time = 0.0
        self.reset()

    def _load_scaled(self, filename):
        image = pygame.image.load(str(SCENE_ASSET_DIR / filename)).convert()
        return pygame.transform.smoothscale(
            image, (SCREEN_WIDTH, SCREEN_HEIGHT)
        )

    def _load_gem(self, name, size):
        image = pygame.image.load(
            str(SCENE_ASSET_DIR / GEM_FILES[name])
        ).convert_alpha()
        return pygame.transform.smoothscale(image, (size, size))

    @staticmethod
    def _make_row_rects(count, width, gap, center_y):
        total_width = count * width + (count - 1) * gap
        start_x = (SCREEN_WIDTH - total_width) // 2
        return [
            pygame.Rect(
                start_x + index * (width + gap),
                center_y - width // 2,
                width,
                width,
            )
            for index in range(count)
        ]

    def reset(self):
        """Create one randomized but always solvable set of 15 gems."""
        gem_order = list(GEM_NAMES)
        random.shuffle(gem_order)
        self.counts = {
            gem_name: count
            for count, gem_name in enumerate(gem_order, start=1)
        }
        self.answer = [
            next(
                gem_name
                for gem_name, count in self.counts.items()
                if count == wanted_count
            )
            for wanted_count in range(1, 6)
        ]

        gems = [
            gem_name
            for gem_name, count in self.counts.items()
            for _ in range(count)
        ]
        random.shuffle(gems)
        self.gem_rows = [gems[:5], gems[5:]]
        self.selections = [None] * 5
        self.solved = False
        self.gate_open_alpha = 0
        self.message = ""
        self.message_color = CREAM
        self.message_time = 0.0

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.solved:
            if self.continue_rect.collidepoint(event.pos):
                self._continue_to_cave()
            return

        for index, rect in enumerate(self.slot_rects):
            if rect.collidepoint(event.pos):
                current = self.selections[index]
                self.selections[index] = (
                    0 if current is None else (current + 1) % len(GEM_NAMES)
                )
                self.message = ""
                return

        if self.confirm_rect.collidepoint(event.pos):
            self._check_answer()

    def _check_answer(self):
        if any(selection is None for selection in self.selections):
            self.message = "Hãy chọn đủ 5 loại ngọc trước khi xác nhận."
            self.message_color = GOLD
            return

        selected_gems = [GEM_NAMES[index] for index in self.selections]
        if selected_gems != self.answer:
            self.message = (
                "Mật mã chưa chính xác. Hãy quan sát những viên ngọc "
                "một lần nữa!"
            )
            self.message_color = RED
            return

        self.solved = True
        self.message = (
            "Ánh sáng từ những viên ngọc hòa làm một. "
            "Cánh cổng đá từ từ mở ra..."
        )
        self.message_color = GREEN
        state = getattr(self.game, "game_state", None)
        if state is not None:
            state.dragon_cave_puzzle_solved = True

    def _continue_to_cave(self):
        if callable(self.on_solved):
            self.on_solved()
            return
        change_scene = getattr(self.game, "change_scene", None)
        if callable(change_scene):
            change_scene("dragon_cave")

    def update(self, dt):
        if self.solved:
            self.gate_open_alpha = min(
                255, self.gate_open_alpha + int(210 * dt)
            )
        if self.message_time > 0:
            self.message_time = max(0.0, self.message_time - dt)

    def _draw_text(self, screen, font, value, color, center):
        text = font.render(value, True, color)
        screen.blit(text, text.get_rect(center=center))

    def draw(self, screen):
        screen.blit(self.background_closed, (0, 0))
        screen.blit(self.overlay, (0, 0))

        if self.gate_open_alpha:
            self.gate_overlay.set_alpha(self.gate_open_alpha)
            self.gate_overlay.blit(self.background_open, (0, 0))
            screen.blit(self.gate_overlay, (0, 0))
            self.gate_overlay.fill((0, 0, 0, 0))

        self._draw_gem_row(
            screen, self.gem_rows[0], self.gem_row_top_rects, self.gem_images
        )
        self._draw_gem_row(
            screen,
            self.gem_rows[1],
            self.gem_row_bottom_rects,
            self.gem_images,
        )

        self._draw_text(
            screen,
            self.body_font,
            "M\u1eacT M\u00c3",
            GOLD,
            (SCREEN_WIDTH // 2, 458),
        )

        for rect, selection in zip(self.slot_rects, self.selections):
            pygame.draw.rect(screen, CREAM, rect, 2, border_radius=8)
            if selection is not None:
                image = self.gem_images[GEM_NAMES[selection]]
                screen.blit(image, image.get_rect(center=rect.center))

        button_rect = self.continue_rect if self.solved else self.confirm_rect
        self._draw_text(
            screen,
            self.button_font,
            "TI\u1ebeP T\u1ee4C" if self.solved else "X\u00c1C NH\u1eacN",
            GOLD,
            button_rect.center,
        )

        if self.message:
            self._draw_text(
                screen,
                self.body_font,
                self.message,
                self.message_color,
                self.message_rect.center,
            )

    def _draw_gem_row(self, screen, gems, rects, image_map):
        for gem_name, rect in zip(gems, rects):
            image = image_map[gem_name]
            screen.blit(image, image.get_rect(center=rect.center))
