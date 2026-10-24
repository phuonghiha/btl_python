"""Reusable game HUD, inventory, and navigation helpers for scenes.

Scenes can inherit from :class:`BaseScene` and call ``super().draw(screen)``
after drawing their own world. Their event handler should call
``super().handle_event(event)`` first and return when it reports ``True``.
Collected item IDs and health are stored in the existing ``GameState``.
"""

from dataclasses import dataclass
import os

import pygame

from scene import Scene
from settings import DARK_BROWN, GOLD, RED, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(PROJECT_DIR, "assets", "images")
INVENTORY_COLUMNS = 3
INVENTORY_CARD_WIDTH = 176
INVENTORY_CARD_HEIGHT = 122
INVENTORY_GAP_X = 12
INVENTORY_GAP_Y = 8
DIALOGUE_PAPER = (240, 222, 181)
DIALOGUE_BORDER = (104, 69, 43)
DIALOGUE_INNER_BORDER = (157, 119, 72)


def draw_dialogue_frame(screen, rect):
    """Draw the shared parchment frame used by hints and dialogue boxes."""
    pygame.draw.rect(
        screen, (31, 22, 16), rect.move(0, 5), border_radius=12
    )
    pygame.draw.rect(screen, DIALOGUE_PAPER, rect, border_radius=12)
    pygame.draw.rect(
        screen, DIALOGUE_BORDER, rect, 3, border_radius=12
    )
    inner = rect.inflate(-12, -12)
    if inner.width > 0 and inner.height > 0:
        pygame.draw.rect(
            screen, DIALOGUE_INNER_BORDER, inner, 1, border_radius=8
        )


@dataclass(frozen=True)
class InventoryItem:
    """Display metadata for an item stored in the shared GameState."""

    item_id: str
    name: str
    image_path: str | None


class BaseScene(Scene):
    """Shared HUD and inventory helpers for gameplay scenes.

    ``GameState.inventory`` remains the source of truth for ownership. Item
    display metadata and loaded surfaces are cached here so scenes can add
    items with one call and reuse the same images after changing locations.
    """

    _item_definitions = {}
    _image_cache = {}

    def __init__(self, game):
        super().__init__(game)
        self.inventory_open = False
        self.inventory_scroll_row = 0
        self.selected_item = None

        self.map_button_rect = getattr(
            game,
            "map_button_rect",
            pygame.Rect(SCREEN_WIDTH - 82, 16, 64, 64),
        )
        self.inventory_button_rect = pygame.Rect(
            self.map_button_rect.left - 70,
            self.map_button_rect.top,
            self.map_button_rect.width,
            self.map_button_rect.height,
        )
        self.inventory_panel_rect = pygame.Rect(
            160, 66, SCREEN_WIDTH - 320, SCREEN_HEIGHT - 132
        )
        self.take_item_rect = pygame.Rect(0, 0, 0, 0)

        self._font = pygame.font.SysFont("arial", 20)
        self._small_font = pygame.font.SysFont("arial", 16)
        self._title_font = pygame.font.SysFont("arial", 30, bold=True)
        self._button_font = pygame.font.SysFont("arial", 18, bold=True)

        self._pouch_image = self._fit_image(
            self._load_image(os.path.join(IMAGE_DIR, "pouch.png")),
            self.inventory_button_rect.size,
        )
        self._map_image = getattr(game, "map_icon", None)
        if self._map_image is None:
            self._map_image = self._load_ui_image("treasure-map.png", (58, 58))
        self._wood_image = self._load_ui_image(
            "Wood.png", self.inventory_panel_rect.size
        )

    @classmethod
    def _asset_path(cls, path):
        if os.path.isabs(path):
            return path
        return os.path.join(PROJECT_DIR, path)

    @classmethod
    def _load_image(cls, path):
        absolute_path = cls._asset_path(path)
        cached = cls._image_cache.get(absolute_path)
        if cached is not None:
            return cached
        if not os.path.isfile(absolute_path):
            raise FileNotFoundError(
                f"BaseScene asset does not exist: {absolute_path}"
            )
        try:
            image = pygame.image.load(absolute_path).convert_alpha()
        except (pygame.error, OSError) as error:
            raise ValueError(
                f"Could not load BaseScene image '{absolute_path}': {error}"
            ) from error
        cls._image_cache[absolute_path] = image
        return image

    @classmethod
    def _load_ui_image(cls, filename, size):
        image = cls._load_image(os.path.join(IMAGE_DIR, filename))
        return pygame.transform.smoothscale(image, size)

    def add_item(self, item_id, name, image_path):
        """Register and add a collected item to the shared inventory.

        Returns ``True`` only when this call adds a previously unowned item.
        Call this from the scene event that actually collects the item.
        ``image_path`` may be absolute or relative to the project directory.
        """
        if not item_id:
            raise ValueError("item_id must be a non-empty string")
        if not name:
            raise ValueError("name must be a non-empty string")
        if not image_path:
            raise ValueError("image_path must identify an existing item image")

        absolute_path = self._asset_path(image_path)
        if not os.path.isfile(absolute_path):
            raise FileNotFoundError(
                f"Inventory item image does not exist: {absolute_path}"
            )
        self._item_definitions[item_id] = InventoryItem(
            item_id=item_id,
            name=name,
            image_path=absolute_path,
        )

        if self.game_state.has_item(item_id):
            return False
        self.game_state.add_item(item_id)
        return True

    def handle_event(self, event):
        """Handle shared HUD controls; return True when consumed."""
        if self.inventory_open:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_i):
                    self.inventory_open = False
                    return True
            elif event.type == pygame.MOUSEWHEEL:
                self._scroll_inventory(event.y)
                return True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_inventory_click(event.pos)
                return True
            return True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            self.inventory_open = True
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.inventory_button_rect.collidepoint(event.pos):
                self.inventory_open = True
                return True
            if self.map_button_rect.collidepoint(event.pos):
                self.game.change_scene("world_map")
                return True

        return False

    def update(self, dt):
        """The shared HUD has no per-frame state to update."""

    def draw(self, screen):
        """Draw the common health bar, navigation buttons, and open bag."""
        self.draw_health_bar(screen)
        screen.blit(
            self._pouch_image,
            self._pouch_image.get_rect(center=self.inventory_button_rect.center),
        )
        screen.blit(self._map_image, self.map_button_rect)
        if self.inventory_open:
            self.draw_inventory(screen)

    def draw_health_bar(self, screen):
        """Render current and maximum health directly from GameState."""
        scene_names = {
            "princess_room": "PHÒNG CÔNG CHÚA",
            "spirit_forest": "RỪNG TINH LINH",
            "poison_swamp": "ĐẦM LẦY ĐỘC",
            "dragon_cave": "HANG RỒNG",
        }
        title = scene_names.get(
            getattr(self.game, "current_scene_id", None),
            getattr(self, "scene_name", ""),
        )
        if title:
            title_image = self._button_font.render(title, True, WHITE)
            screen.blit(title_image, (20, 10))

        bar = pygame.Rect(20, 38, 222, 24)
        pygame.draw.rect(screen, DARK_BROWN, bar, border_radius=6)
        max_health = max(1, self.game_state.max_health)
        ratio = max(0.0, min(1.0, self.game_state.health / max_health))
        fill = bar.inflate(-6, -6)
        fill.width = round(fill.width * ratio)
        if fill.width > 0:
            pygame.draw.rect(screen, RED, fill, border_radius=4)

        label = self._small_font.render(
            f"HP {int(self.game_state.health)}/{self.game_state.max_health}",
            True,
            WHITE,
        )
        screen.blit(label, (bar.x + 8, bar.bottom + 4))

    def draw_inventory(self, screen):
        """Draw a scrollable grid using the shared GameState inventory."""
        panel = self.inventory_panel_rect
        screen.blit(self._wood_image, panel)

        title = self._title_font.render("TÚI ĐỒ", True, GOLD)
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 80)))
        items = self._get_inventory_items()
        grid_rect = self._inventory_grid_rect()
        self.take_item_rect = pygame.Rect(
            panel.centerx - 95, panel.y + 415, 190, 40
        )
        self._draw_button(
            screen,
            self.take_item_rect,
            "LẤY ĐỒ",
            emphasized=True,
            border_color=None,
            text_color=(240, 222, 181),
        )
        if not items:
            text = self._font.render("Túi đồ đang trống", True, DARK_BROWN)
            screen.blit(text, text.get_rect(center=grid_rect.center))
            return

        columns = INVENTORY_COLUMNS
        gap_x, gap_y = INVENTORY_GAP_X, INVENTORY_GAP_Y
        cell_width = (grid_rect.width - gap_x * (columns - 1)) // columns
        card_width = min(INVENTORY_CARD_WIDTH, cell_width)
        card_height = INVENTORY_CARD_HEIGHT
        visible_rows = max(1, (grid_rect.height + gap_y) // (card_height + gap_y))
        total_rows = (len(items) + columns - 1) // columns
        self.inventory_scroll_row = min(
            max(0, self.inventory_scroll_row), max(0, total_rows - visible_rows)
        )

        old_clip = screen.get_clip()
        screen.set_clip(grid_rect)
        first = self.inventory_scroll_row * columns
        last = min(len(items), (self.inventory_scroll_row + visible_rows) * columns)
        for index in range(first, last):
            item = items[index]
            visible_index = index - first
            row, column = divmod(visible_index, columns)
            y_offset = 5 if item.item_id == "holy_sword" else 0
            card = pygame.Rect(
                grid_rect.x + column * (cell_width + gap_x)
                + (cell_width - card_width) // 2,
                grid_rect.y + row * (card_height + gap_y) + y_offset,
                card_width,
                card_height,
            )
            selected = item.item_id == self.selected_item
            pygame.draw.rect(
                screen,
                (231, 211, 166) if selected else (247, 234, 202),
                card,
                border_radius=10,
            )
            pygame.draw.rect(screen, DARK_BROWN, card, 2, border_radius=10)

            image = self._get_item_image(item)
            image_box = pygame.Rect(card.x + 12, card.y + 5, card.width - 24, 58)
            if image is not None:
                fitted = self._fit_image(image, image_box.size)
                screen.blit(fitted, fitted.get_rect(center=image_box.center))

            name_lines = self._wrap_text(item.name, self._small_font, card.width - 16)
            text_y = card.y + 68
            for line in name_lines[:3]:
                label = self._small_font.render(line, True, DARK_BROWN)
                screen.blit(label, label.get_rect(centerx=card.centerx, top=text_y))
                text_y += 19

        screen.set_clip(old_clip)

    def _get_inventory_items(self):
        result = []
        for item_id in self.game_state.inventory:
            item = self._item_definitions.get(item_id)
            if item is None:
                item = InventoryItem(
                    item_id=str(item_id),
                    name=str(item_id).replace("_", " ").title(),
                    image_path=None,
                )
            result.append(item)
        return result

    def _get_item_image(self, item):
        if not item.image_path:
            return None
        return self._load_image(item.image_path)

    @staticmethod
    def _fit_image(image, bounds):
        width, height = bounds
        scale = min(
            1.0,
            width / image.get_width(),
            height / image.get_height(),
        )
        size = (
            max(1, round(image.get_width() * scale)),
            max(1, round(image.get_height() * scale)),
        )
        if image.get_size() == size:
            return image
        return pygame.transform.smoothscale(image, size)

    def _handle_inventory_click(self, position):
        if not self.inventory_panel_rect.collidepoint(position):
            self.inventory_open = False
            return

        if self.take_item_rect.collidepoint(position):
            if self.selected_item is not None:
                self.inventory_open = False
            return

        grid_rect = self._inventory_grid_rect()
        if not grid_rect.collidepoint(position):
            return

        items = self._get_inventory_items()
        columns = INVENTORY_COLUMNS
        gap_x = INVENTORY_GAP_X
        gap_y = INVENTORY_GAP_Y
        cell_width = (grid_rect.width - gap_x * (columns - 1)) // columns
        card_width = min(INVENTORY_CARD_WIDTH, cell_width)
        card_height = INVENTORY_CARD_HEIGHT
        visible_rows = max(
            1, (grid_rect.height + gap_y) // (card_height + gap_y)
        )
        row = (position[1] - grid_rect.y) // (card_height + gap_y)
        column = (position[0] - grid_rect.x) // (cell_width + gap_x)
        if column >= columns or row < 0 or row >= visible_rows:
            return
        index = (self.inventory_scroll_row + row) * columns + column
        if index >= len(items):
            return
        item = items[index]
        y_offset = 5 if item.item_id == "holy_sword" else 0
        card_rect = pygame.Rect(
            grid_rect.x + column * (cell_width + gap_x)
            + (cell_width - card_width) // 2,
            grid_rect.y + row * (card_height + gap_y) + y_offset,
            card_width,
            card_height,
        )
        if not card_rect.collidepoint(position):
            return
        self.selected_item = item.item_id

    def _scroll_inventory(self, direction):
        items = self._get_inventory_items()
        columns = INVENTORY_COLUMNS
        rows = (len(items) + columns - 1) // columns
        visible_height = self._inventory_grid_rect().height
        visible_rows = max(
            1,
            (visible_height + INVENTORY_GAP_Y)
            // (INVENTORY_CARD_HEIGHT + INVENTORY_GAP_Y),
        )
        self.inventory_scroll_row = min(
            max(0, self.inventory_scroll_row - direction),
            max(0, rows - visible_rows),
        )

    def _inventory_grid_rect(self):
        panel = self.inventory_panel_rect
        return pygame.Rect(
            panel.x + 144,
            panel.y + 112,
            panel.width - 288,
            panel.height - 293,
        )

    @staticmethod
    def _wrap_text(text, font, max_width):
        lines = []
        current = ""
        for word in text.split():
            candidate = word if not current else f"{current} {word}"
            if current and font.size(candidate)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines or [""]

    def _draw_button(
        self, screen, rect, label, emphasized, border_color=GOLD, text_color=None
    ):
        fill = (119, 77, 44) if emphasized else (226, 207, 170)
        if text_color is None:
            text_color = WHITE if emphasized else DARK_BROWN
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        if border_color is not None:
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=8)
        text = self._button_font.render(label, True, text_color)
        screen.blit(text, text.get_rect(center=rect.center))
