"""Simple in-scene princess figure used while the project lacks a sprite."""

import pygame


class Princess:
    def draw(self, screen, center, scale=1.0):
        x, y = center
        skin = (245, 202, 163)
        hair = (111, 48, 83)
        dress = (155, 90, 155)
        gold = (244, 195, 85)

        pygame.draw.ellipse(
            screen,
            (35, 20, 24),
            (x - 42 * scale, y + 54 * scale, 84 * scale, 15 * scale),
        )
        pygame.draw.polygon(
            screen,
            dress,
            [
                (x, y - 8 * scale),
                (x - 45 * scale, y + 63 * scale),
                (x + 45 * scale, y + 63 * scale),
            ],
        )
        pygame.draw.ellipse(
            screen,
            hair,
            (x - 25 * scale, y - 49 * scale, 50 * scale, 62 * scale),
        )
        pygame.draw.circle(screen, skin, (int(x), int(y - 29 * scale)), int(17 * scale))
        pygame.draw.polygon(
            screen,
            gold,
            [
                (x - 16 * scale, y - 47 * scale),
                (x - 10 * scale, y - 61 * scale),
                (x, y - 49 * scale),
                (x + 9 * scale, y - 62 * scale),
                (x + 16 * scale, y - 46 * scale),
            ],
        )
