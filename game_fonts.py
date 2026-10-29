

import os
import pygame


_FONT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
    "fonts",
)

_TITLE_PATH = os.path.join(_FONT_DIR, "title3.ttf")
_CONTENT_PATH = os.path.join(_FONT_DIR, "content3.otf")

_CACHE = {}


def title(size):
    return _load(_TITLE_PATH, size)


def content1(size):
    return _load(_CONTENT_PATH, size)


def _load(path, size):
    key = (path, size)

    if key not in _CACHE:
        _CACHE[key] = pygame.font.Font(path, size)

    return _CACHE[key]
