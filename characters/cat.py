import pygame

from animation.animation_manager import AnimationManager


class Cat:

    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.speed = 180

        # sit -> stand_up -> ready -> walk
        self.state = "sit"

        self.animation = AnimationManager()

        # Ảnh mèo ngồi ban đầu
        self.animation.load_image(
            "sit",
            "assets/sprites/cat/stand_up/n_1.png"
        )

        # Animation đứng dậy: n_1 -> n_6
        self.animation.load_folder(
            "stand_up",
            "assets/sprites/cat/stand_up",
            fps=3,
            loop=False
        )

        # Animation đi: w_1 -> w_5
        self.animation.load_folder(
            "walk",
            "assets/sprites/cat/walk",
            fps=6,
            loop=True
        )

        self.animation.play("sit")


    def stand_up(self):
        if self.state != "sit":
            return

        self.state = "stand_up"
        self.animation.play("stand_up")


    def walk(self):
        # Chỉ đi sau khi đứng dậy xong
        if self.state != "ready":
            return

        self.state = "walk"
        self.animation.play("walk")


    def update(self, dt):

        if self.state == "stand_up":

            self.animation.update(dt)

            # n_1 -> ... -> n_6 chạy xong
            if self.animation.is_finished():
                self.state = "ready"


        elif self.state == "walk":

            self.animation.update(dt)

            # Mèo di chuyển sang phải
            self.x += self.speed * dt


    def draw(self, screen, size):

        frame = self.animation.get_current_frame()

        if frame is None:
            return

        width, height = size

        frame = pygame.transform.smoothscale(
            frame,
            (width, height)
        )

        rect = frame.get_rect(
            midbottom=(self.x, self.y)
        )

        screen.blit(frame, rect)