
import os
import pygame

from scene import Scene
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_IMAGE_PATH = os.path.join(
    BASE_DIR, "assets", "images", "Main_map.png"
)


class WorldMap(Scene):
    def __init__(self, game):
        super().__init__(game)

        self.map_image = pygame.image.load(
            MAP_IMAGE_PATH
        ).convert()

        # Kích thước gốc của ảnh bản đồ
        self.original_width, self.original_height = (
            self.map_image.get_size()
        )

        # Co ảnh vừa màn hình, giữ nguyên tỉ lệ
        scale = min(
            SCREEN_WIDTH / self.original_width,
            SCREEN_HEIGHT / self.original_height
        )

        new_width = int(self.original_width * scale)
        new_height = int(self.original_height * scale)

        self.map_image = pygame.transform.smoothscale(
            self.map_image,
            (new_width, new_height)
        )

        self.map_rect = self.map_image.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        )

        # Vùng bấm tính theo tọa độ tương đối của ảnh gốc:
        # (x, y, width, height)
        self.locations = {
            "princess_room": (150, 460, 270, 95),
            "spirit_forest": (600, 510, 235, 90),
            "poison_swamp": (970, 560,245, 85),
            "dragon_cave": (1380, 580, 235, 90),
        }

        self.hovered_location = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_scene(
                    self.game.previous_scene_id
                )
                return

        if event.type == pygame.MOUSEMOTION:
            self.hovered_location = self.get_location_at(
                event.pos
            )

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                location = self.get_location_at(event.pos)

                if location:
                    self.game.change_scene(location)

    def get_location_at(self, mouse_pos):
        # Đổi tọa độ màn hình thành tọa độ ảnh gốc
        if not self.map_rect.collidepoint(mouse_pos):
            return None

        scale_x = self.original_width / self.map_rect.width
        scale_y = self.original_height / self.map_rect.height

        image_x = int(
            (mouse_pos[0] - self.map_rect.left) * scale_x
        )
        image_y = int(
            (mouse_pos[1] - self.map_rect.top) * scale_y
        )

        for scene_id, (x, y, width, height) in (
            self.locations.items()
        ):
            area = pygame.Rect(x, y, width, height)

            if area.collidepoint(image_x, image_y):
                return scene_id

        return None

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((30, 40, 50))

        screen.blit(self.map_image, self.map_rect)

