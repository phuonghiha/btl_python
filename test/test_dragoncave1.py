"""Launch Dragon Cave puzzle 1 without changing the main game's scenes."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from game_state import GameState
from puzzes.dragoncave1 import DragonCave1Scene
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


class PuzzleTestHarness:
    def __init__(self):
        self.game_state = GameState()
        self.next_scene = None

    def change_scene(self, scene_id):
        self.next_scene = scene_id


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Test - Hang Rong: Bi mat nhung vien ngoc")
    clock = pygame.time.Clock()

    harness = PuzzleTestHarness()
    scene = DragonCave1Scene(harness)
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

            scene.update(dt)
            scene.draw(screen)
            pygame.display.flip()

            if harness.next_scene == "dragon_cave":
                running = False
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
