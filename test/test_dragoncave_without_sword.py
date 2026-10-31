"""Launch the dragon cave puzzle without the Holy Sword."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from game import Game


def main():
    game = Game()
    game.game_state.has_holy_sword = False
    game.scenes["dragon_cave"].reset()
    game.change_scene("dragon_cave")
    game.run()


if __name__ == "__main__":
    main()
