import pygame

from animation.animation_manager import AnimationManager


class Frog:

    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.speed = 3
        self.direction = "right"

        self.animation = AnimationManager()

        self.animation.load_image(
            "idle",
            "assets/sprites/frog/dung.png"
        )

        self.animation.load_folder(
            "turn_left",
            "assets/sprites/frog/xoaytrai",
            fps=8,
            loop=False
        )

        self.animation.load_folder(
            "turn_right",
            "assets/sprites/frog/xoayphai",
            fps=8,
            loop=False
        )

        self.animation.load_folder(
            "jump",
            "assets/sprites/frog/nhay",
            fps=10,
            loop=False
        )

        self.animation.load_folder(
            "attack",
            "assets/sprites/frog/phundoc",
            fps=8,
            loop=False
        )

        self.animation.play("idle")

    def idle(self):
        self.animation.play("idle")

    def turn_left(self):
        self.direction = "left"
        self.animation.play("turn_left")

    def turn_right(self):
        self.direction = "right"
        self.animation.play("turn_right")

    def jump(self):
        self.animation.play("jump")

    def attack(self):
        self.animation.play("attack")

    def update(self, dt):
        self.animation.update(dt)

        if self.animation.is_finished():
            if self.animation.current_animation == "jump":
                self.animation.play("idle")

            elif self.animation.current_animation == "attack":
                self.animation.play("idle")
    def draw(self, screen, size=None):
        frame = self.animation.get_current_frame()

        if frame is None:
            return

        if size is not None:
            frame = pygame.transform.scale(
                frame,
                size
            )

        screen.blit(
            frame,
            (self.x, self.y)
        )