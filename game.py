
import pygame
import os

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    GAME_TITLE,
)

from game_state import GameState
from world_map import WorldMap

from scenes.start_scene import StartScene
from scenes.intro_scene import IntroScene
from scenes.game_over_scene import GameOverScene
from scenes.princess_room import PrincessRoomScene
from scenes.forest import ForestScene
from scenes.swamp import SwampScene
from scenes.dragoncave import DragonCaveScene


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        pygame.display.set_caption(GAME_TITLE)
        
        self.clock = pygame.time.Clock()
        self.game_state = GameState()
        
        base_dir = os.path.dirname(os.path.abspath(__file__))

        map_icon_path = os.path.join(
            base_dir, "assets", "images", "treasure-map.png"
        )

        self.map_icon = pygame.image.load(
            map_icon_path
        ).convert_alpha()

        self.map_icon = pygame.transform.smoothscale(
            self.map_icon, (64, 64)
        )

        self.map_button_rect = self.map_icon.get_rect(
            topright=(SCREEN_WIDTH - 25, 20)
        )
        

        self.current_scene = None
        self.current_scene_id = None

        # Khu vực trước khi mở bản đồ
        self.previous_scene_id = "princess_room"

        # Khởi tạo các scene
        self.scenes = {
            "start": StartScene(self),
            "intro": IntroScene(self),
            "world_map": WorldMap(self),
            "game_over": GameOverScene(self),

            "princess_room": PrincessRoomScene(self),
            "spirit_forest": ForestScene(self),
            "poison_swamp": SwampScene(self),
            "dragon_cave": DragonCaveScene(self),
        }

        self.change_scene("start")

    def change_scene(self, scene_id):
        if scene_id not in self.scenes:
            print(f"Không tìm thấy scene: {scene_id}")
            return

        # Ghi nhớ khu vực trước khi mở bản đồ
        if (
            scene_id == "world_map"
            and self.current_scene_id not in (
                None,
                "start",
                "intro",
                "world_map",
                "game_over",
            )
        ):
            self.previous_scene_id = self.current_scene_id

        self.current_scene_id = scene_id
        self.current_scene = self.scenes[scene_id]
        self.game_state.current_scene = scene_id

    def restart_game(self):
        # Đưa toàn bộ trạng thái về ban đầu
        self.game_state.reset()

        for scene in self.scenes.values():
            reset = getattr(scene, "reset", None)
            if callable(reset):
                reset()

        self.previous_scene_id = "princess_room"

        self.change_scene("start")

    def run(self):
        running = True

        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                # ESC để quay lại khu vực trước đó
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                    and self.current_scene_id == "world_map"
                ):
                    self.change_scene(
                        self.previous_scene_id
                    )
                    continue

                self.current_scene.handle_event(event)

            if not running:
                break

            self.current_scene.update(dt)

            # Kiểm tra máu sau khi cập nhật scene
            if (
                self.game_state.health <= 0
                and self.current_scene_id != "game_over"
            ):
                self.change_scene("game_over")

            self.current_scene.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
