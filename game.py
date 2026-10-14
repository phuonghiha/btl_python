
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    GAME_TITLE,
    DARK_GREEN,
    WHITE,
)

from game_state import GameState
from world_map import WorldMap

from scenes.start_scene import StartScene
from scenes.intro_scene import IntroScene
from scenes.game_over_scene import GameOverScene
from scenes.placeholder_scene import PlaceholderScene


class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )

        pygame.display.set_caption(GAME_TITLE)

        self.clock = pygame.time.Clock()
        self.game_state = GameState()

        self.current_scene = None
        self.current_scene_id = None

        # Luu khu vuc truoc khi mo World Map
        self.previous_scene_id = "princess_room"

        # Nut World Map o goc tren ben phai
        self.map_button = pygame.Rect(
            SCREEN_WIDTH - 190,
            25,
            160,
            65,
        )

        # Dang ky cac scene
        self.scenes = {
            "start": StartScene(self),
            "intro": IntroScene(self),
            "world_map": WorldMap(self),
            "game_over": GameOverScene(self),

            "princess_room": PlaceholderScene(
                self, "Phong cong chua"
            ),
            "spirit_forest": PlaceholderScene(
                self, "Rung tinh linh"
            ),
            "poison_swamp": PlaceholderScene(
                self, "Dam lay doc"
            ),
            "dragon_cave": PlaceholderScene(
                self, "Hang dong rong"
            ),
        }

        self.change_scene("start")

    def change_scene(self, scene_id):
        if scene_id not in self.scenes:
            print(f"Khong tim thay scene: {scene_id}")
            return

        # Ghi nho man dang choi truoc khi mo ban do
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

    def draw_map_button(self):
        # Khong hien nut ban do o man bat dau,
        # man loi thoai va man ban do.
        if self.current_scene_id in (
            "start",
            "intro",
            "world_map",
            "game_over",
        ):
            return

        pygame.draw.rect(
            self.screen,
            DARK_GREEN,
            self.map_button,
            border_radius=12,
        )

        font = pygame.font.Font(None, 32)

        text = font.render(
            "Ban do",
            True,
            WHITE,
        )

        self.screen.blit(
            text,
            text.get_rect(center=self.map_button.center),
        )

    def run(self):
        running = True

        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                # Bam nut World Map
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and self.current_scene_id not in (
                        "start",
                        "intro",
                        "world_map",
                        "game_over",
                    )
                    and self.map_button.collidepoint(event.pos)
                ):
                    self.change_scene("world_map")
                    continue

                # ESC de quay lai man truoc tu World Map
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                    and self.current_scene_id == "world_map"
                ):
                    self.change_scene(self.previous_scene_id)
                    continue

                self.current_scene.handle_event(event)

            if not running:
                break

            # Cap nhat logic man hien tai
            self.current_scene.update(dt)

            # Het mau thi chuyen sang Game Over
            if (
                self.game_state.health <= 0
                and self.current_scene_id != "game_over"
            ):
                self.change_scene("game_over")

            # Ve man hinh
            self.current_scene.draw(self.screen)
            self.draw_map_button()

            pygame.display.flip()

        pygame.quit()
