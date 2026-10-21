"""Launch the swamp scene without poison protection."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from game import Game
from scenes.swamp import SwampScene


def main():
    game = Game()
    game.game_state.has_poison_protection = False
    game.scenes["poison_swamp"] = SwampScene(game)
    game.change_scene("poison_swamp")
    game.run()


if __name__ == "__main__":
    main()
