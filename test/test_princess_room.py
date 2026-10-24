"""Run PRINCESS_ROOM by itself without changing the main game's scene table."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from game_state import GameState
from scenes.princess_room import PrincessRoomScene
from settings import SCREEN_HEIGHT, SCREEN_WIDTH
from world_map import WorldMap


class PrincessRoomTestHarness:
    """Small game stub providing only the API PrincessRoomScene needs."""

    def __init__(self):
        self.game_state = GameState()
        self.next_scene_id = None
        self.current_scene_id = "princess_room"
        self.previous_scene_id = "princess_room"

    def change_scene(self, scene_id):
        if scene_id == "world_map":
            if self.current_scene_id != "world_map":
                self.previous_scene_id = self.current_scene_id
            self.current_scene_id = "world_map"
        elif scene_id == "princess_room":
            self.current_scene_id = scene_id
        else:
            # Stop the room-only test when it requests an unimplemented scene.
            self.next_scene_id = scene_id


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Test - Phòng công chúa | F12 để thoát")
    clock = pygame.time.Clock()

    harness = PrincessRoomTestHarness()
    scene = PrincessRoomScene(harness)
    world_map = WorldMap(harness)
    running = True

    try:
        while running:
            dt = min(clock.tick(60) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F12:
                    running = False
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                    and harness.current_scene_id == "world_map"
                ):
                    harness.change_scene(harness.previous_scene_id)
                else:
                    active_scene = (
                        world_map
                        if harness.current_scene_id == "world_map"
                        else scene
                    )
                    active_scene.handle_event(event)

            if not running:
                break

            active_scene = (
                world_map
                if harness.current_scene_id == "world_map"
                else scene
            )
            active_scene.update(dt)
            active_scene.draw(screen)

            if harness.next_scene_id:
                # The room requested a scene this test harness does not run.
                running = False

            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
