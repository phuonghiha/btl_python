import os
import pygame

from .animation import Animation


class AnimationManager:

    def __init__(self):
        self.animations = {}
        self.current_animation = None

    def load_folder(self, name, folder_path, fps=8, loop=True):
        files = [
            file
            for file in os.listdir(folder_path)
            if file.lower().endswith(".png")
        ]

        files.sort(
            key=lambda file: int(
                ''.join(
                    c for c in os.path.splitext(file)[0]
                    if c.isdigit()
                )
            )
        )

        frames = []

        for file in files:
            image_path = os.path.join(folder_path, file)
            image = pygame.image.load(image_path).convert_alpha()
            frames.append(image)

        self.animations[name] = Animation(
            frames,
            fps=fps,
            loop=loop
        )

    def load_image(self, name, image_path, loop=True):
        image = pygame.image.load(image_path).convert_alpha()

        self.animations[name] = Animation(
            [image],
            fps=1,
            loop=loop
        )

    def play(self, name):
        if name not in self.animations:
            return

        if self.current_animation == name:
            return

        self.current_animation = name
        self.animations[name].reset()

    def update(self, dt):
        if self.current_animation is None:
            return

        self.animations[self.current_animation].update(dt)

    def get_current_frame(self):
        if self.current_animation is None:
            return None

        return self.animations[
            self.current_animation
        ].get_current_frame()

    def is_finished(self):
        if self.current_animation is None:
            return False

        return self.animations[
            self.current_animation
        ].finished