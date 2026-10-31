"""Dragon idle and one-shot fire-breath animations."""

from pathlib import Path

import pygame

from animation.animation_manager import AnimationManager


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "sprites" / "dragon"


class Dragon:
    def __init__(self):
        self.animation = AnimationManager()
        self.animation.load_folder(
            "idle", str(ASSET_DIR / "idle"), fps=1, loop=True
        )
        self.animation.load_folder(
            "fire", str(ASSET_DIR / "fire"), fps=7, loop=False
        )
        self.play_idle()

    def play_idle(self):
        self.animation.play("idle")

    def play_fire_attack(self):
        self.animation.play("fire")

    def update(self, dt):
        self.animation.update(dt)

    def is_animation_finished(self):
        return self.animation.is_finished()

    def draw(self, screen, position, size):
        frame = self.animation.get_current_frame()
        if frame is None:
            return
        image = pygame.transform.smoothscale(frame, size)
        screen.blit(image, position)
