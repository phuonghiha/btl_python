"""Run PRINCESS_ROOM by itself without changing the main game's scene table."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from game_state import GameState
from scenes.princess_room import PrincessRoomScene
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


class PrincessRoomTestHarness:
    """Small game stub providing only the API PrincessRoomScene needs."""

    def __init__(self):
        self.game_state = GameState()
        self.next_scene_id = None

    def change_scene(self, scene_id):
        # Record the transition so it can be inspected while debugging.
        self.next_scene_id = scene_id


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Test - Phòng công chúa | F12 để thoát")
    clock = pygame.time.Clock()

    harness = PrincessRoomTestHarness()
    scene = PrincessRoomScene(harness)
    running = True

    try:
        while running:
            dt = min(clock.tick(60) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F12:
                    running = False
                else:
                    scene.handle_event(event)

            if not running:
                break

            scene.update(dt)
            scene.draw(screen)

            if harness.next_scene_id:
                # The room requested its next scene; end this standalone run.
                running = False

            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
