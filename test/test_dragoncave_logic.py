"""Logic checks for the Dragon Cave battle module."""

from pathlib import Path
import sys
from types import SimpleNamespace
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from game_state import GameState
from puzzes.dragoncave import DragonBlockGame
from scenes.dragoncave import DragonCaveScene


class DragonCaveLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def make_game(self, sword=True):
        return DragonBlockGame(self.screen, sword=sword)

    def test_piece_color_is_fixed_by_length(self):
        game = self.make_game()
        self.assertIs(game.screen, self.screen)
        self.assertFalse(hasattr(game, "run"))
        for length, expected_color in game.COLORS.items():
            piece = game.new_piece(length, 0, 0, color=(1, 2, 3))
            self.assertEqual(piece["length"], length)
            self.assertEqual(piece["color"], expected_color)

    def test_sword_combo_damage_uses_rows_cleared(self):
        game = self.make_game(sword=True)
        game.rows_cleared_this_attack = 2
        game.player_attack()
        self.assertEqual(game.dragon_hp, 73)
        self.assertFalse(game.game_over)

    def test_no_sword_damage_is_low_and_cannot_defeat_dragon(self):
        game = self.make_game(sword=False)
        game.rows_cleared_this_attack = 4
        game.player_attack()
        self.assertEqual(game.dragon_hp, 92)

        game.dragon_hp = 81
        game.rows_cleared_this_attack = 4
        game.player_attack()
        self.assertEqual(game.dragon_hp, 80)

        game.rows_cleared_this_attack = 4
        game.player_attack()
        self.assertEqual(game.dragon_hp, 80)
        self.assertFalse(game.win)

    def test_dragon_attack_result_applies_damage_once(self):
        game = self.make_game(sword=False)
        game.dragon_attack_result()
        game.dragon_attack_result()
        self.assertEqual(game.knight_hp, 75)

    def test_sword_counterattack_does_not_damage_knight(self):
        game = self.make_game(sword=True)
        game.dragon_attack_result()
        self.assertEqual(game.knight_hp, 100)

    def test_scene_injects_the_shared_screen_and_inventory_weapon(self):
        game_state = GameState()
        game_state.has_holy_sword = True
        harness = SimpleNamespace(
            screen=self.screen,
            game_state=game_state,
            current_scene_id="dragon_cave",
        )
        scene = DragonCaveScene(harness)

        self.assertIs(scene.puzzle.screen, self.screen)
        self.assertTrue(scene.puzzle.sword)
        scene.draw(self.screen)

    def test_drag_cannot_pass_through_another_piece(self):
        game = self.make_game()
        game.clear_board()
        moving = game.new_piece(1, 4, 0)
        blocker = game.new_piece(1, 4, 2)
        game.place_piece(moving)
        game.place_piece(blocker)
        game.rebuild_piece_cells()

        self.assertFalse(game.can_slide_piece(4, 0, 3, 1, moving["id"]))
        self.assertTrue(game.can_slide_piece(4, 0, 1, 1, moving["id"]))

    def test_dragon_attack_threshold_depends_on_sword(self):
        for sword, misses in ((True, 2), (False, 2)):
            game = self.make_game(sword=sword)
            called = []
            game.dragon_attack = lambda: called.append(True)
            game.failed_turns = misses

            game.resolve_after_push()

            self.assertEqual(called, [True])
            self.assertEqual(game.failed_turns, 0)


if __name__ == "__main__":
    unittest.main()
