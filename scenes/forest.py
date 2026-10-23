import math
import os
import pygame

from scene import Scene
from settings import GOLD, WHITE
from puzzes.forest.for_puz import TangramGame


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "images", "sence_2")
SPR = os.path.join(ROOT, "assets", "sprites")

HOUSE = os.path.join(
    IMG,
    "793802490_29353841374216909_1805474976622337015_n.png"
)

FOREST = os.path.join(
    IMG,
    "forest_no_house.png"
)

KNIGHT_DIR = os.path.join(SPR, "knight")
SPIRIT_DIR = os.path.join(SPR, "spirit")

KNIGHT_IDLE = os.path.join(KNIGHT_DIR, "IDLE", "Đứng_1.png")
KNIGHT_DIALOG = os.path.join(KNIGHT_DIR, "front", "1.png")
KNIGHT_WALK_DIR = os.path.join(KNIGHT_DIR, "Walk_right")

SPIRIT_FILES = {
    "curious": "new spirit-curious.png",
    "stern": "new spirit - stern.png",
    "surprised": "new spirit - susprised.png",
    "happy": "new spirit - happy.png",
    "angry": "new spirit - warning.png",
    "thinking": "new spirit - normal.png"
}

PAPER = (244, 235, 210)
PAPER_BORDER = (111, 78, 43)
PAPER_BORDER_LIGHT = (157, 119, 72)
INK = (45, 35, 25)
INK_LIGHT = (75, 55, 38)


def cover(image, size):
    iw, ih = image.get_size()
    scale = max(size[0] / iw, size[1] / ih)

    image = pygame.transform.smoothscale(
        image,
        (int(iw * scale), int(ih * scale))
    )

    x = (image.get_width() - size[0]) // 2
    y = (image.get_height() - size[1]) // 2

    return image.subsurface(
        (x, y, size[0], size[1])
    ).copy()


def scale_keep_ratio(image, size):
    iw, ih = image.get_size()

    if iw <= 0 or ih <= 0:
        return image

    scale = min(size[0] / iw, size[1] / ih)

    return pygame.transform.smoothscale(
        image,
        (
            max(1, int(iw * scale)),
            max(1, int(ih * scale))
        )
    )


def crop_transparent(image):
    rect = image.get_bounding_rect()

    if rect.width > 0 and rect.height > 0:
        return image.subsurface(rect).copy()

    return image


def load_image(path):
    if not os.path.isfile(path):
        return None

    try:
        return crop_transparent(
            pygame.image.load(path).convert_alpha()
        )
    except pygame.error:
        return None


def load_walk_frames():
    frames = []

    if not os.path.isdir(KNIGHT_WALK_DIR):
        return frames

    files = []

    for name in os.listdir(KNIGHT_WALK_DIR):
        path = os.path.join(KNIGHT_WALK_DIR, name)

        if os.path.isfile(path) and name.lower().endswith(
            (".png", ".jpg", ".jpeg", ".webp")
        ):
            files.append(path)

    files.sort()

    for path in files:
        image = load_image(path)

        if image is not None:
            frames.append(
                scale_keep_ratio(image, (175, 235))
            )

    return frames


def crop_upper_body(image, ratio=0.72):
    image = crop_transparent(image)

    width, height = image.get_size()
    new_height = max(1, int(height * ratio))

    return image.subsurface(
        (0, 0, width, new_height)
    ).copy()


def load_spirit_frames():
    result = {}

    for expression, filename in SPIRIT_FILES.items():
        path = os.path.join(SPIRIT_DIR, filename)
        image = load_image(path)

        if image is not None:
            result[expression] = image

    return result


class ForestScene(Scene):

    def __init__(self, game):
        super().__init__(game)

        self.screen_size = game.screen.get_size()
        self.w, self.h = self.screen_size

        self.font = pygame.font.SysFont("arial", 20)
        self.small = pygame.font.SysFont("arial", 14)
        self.heading = pygame.font.SysFont("arial", 30, bold=True)
        self.name_font = pygame.font.SysFont("arial", 19, bold=True)
        self.echo_font = pygame.font.SysFont("georgia", 31, bold=True)

        self.forest = self._background(FOREST)
        self.house_bg = self._background(HOUSE)

        self.knight_idle = load_image(KNIGHT_IDLE)
        self.knight_dialog = load_image(KNIGHT_DIALOG)

        if self.knight_dialog is not None:
            self.knight_dialog = crop_upper_body(
                self.knight_dialog,
                0.72
            )

        self.knight_walk_frames = load_walk_frames()

        if not self.knight_walk_frames and self.knight_idle is not None:
            self.knight_walk_frames = [
                scale_keep_ratio(
                    self.knight_idle,
                    (175, 235)
                )
            ]

        self.knight_frame = 0
        self.knight_animation_timer = 0.0
        self.knight_animation_speed = 0.14

        self.spirits = load_spirit_frames()

        self.game_state = game.game_state

        self.scene = "approach"
        self.timer = 0.0
        self.echo_time = 0.0

        self.knight_x = -170

        self.dialog_index = 0
        self.char_progress = 0.0

        self.puzzle = None
        self.puzzle_done_time = 0.0

        self.finished = False

        self.intro_dialogs = [
            (
                "Hiệp sĩ",
                "Một ngôi nhà giữa khu rừng...? "
                "Ta phải tiến lại gần xem sao."
            ),
            (
                "Hiệp sĩ",
                "Kỳ lạ... vừa rồi nó còn ở đây. "
                "Tại sao lại biến mất?"
            ),
            (
                "???",
                "Kẻ xâm nhập... "
                "ngươi đến nơi này để tìm kiếm điều gì?"
            ),
            (
                "Hiệp sĩ",
                "Ai đó? Hãy hiện thân! "
                "Ta không đến đây để gây chiến."
            ),
            (
                "???",
                "Muốn được khu rừng công nhận, "
                "đôi mắt của ngươi là chưa đủ."
            ),
            (
                "???",
                "Nếu thật sự có trí tuệ, "
                "hãy khôi phục lại thứ mà khu rừng đã che giấu."
            )
        ]

        self.dialogs = [
            (
                "Tinh linh",
                "Ngươi đã khôi phục được bức tranh mà khu rừng che giấu. Ta công nhận trí tuệ của ngươi.",
                "happy"
            ),
            (
                "Tinh linh",
                "Nhưng... khoan đã. Ta cảm nhận được một luồng khí rất quen thuộc trên người ngươi.",
                "thinking"
            ),
            (
                "Hiệp sĩ",
                "Ngươi đang nói đến thứ này sao?",
                "curious"
            ),
            (
                "Hiệp sĩ",
                "Ta tìm thấy nó trên đường đi. Một chiếc vảy rồng.",
                "curious"
            ),
            (
                "Tinh linh",
                "Vảy rồng... Ta hiểu rồi. Ngươi đang trên đường tìm kiếm con rồng.",
                "surprised"
            ),
            (
                "Hiệp sĩ",
                "Đúng vậy. Ta đang tìm đường đến hang rồng.",
                "curious"
            ),
            (
                "Tinh linh",
                "Vậy hãy nhận lấy viên đá quý này. Nó mang theo lời chúc phúc của tinh linh.",
                "happy"
            ),
            (
                "Tinh linh",
                "Nó sẽ giúp ngươi vượt qua khí độc trong Đầm Lầy Độc phía trước.",
                "happy"
            ),
            (
                "Hiệp sĩ",
                "Ta hiểu rồi. Cảm ơn ngươi. Ta sẽ tiếp tục lên đường.",
                "happy"
            ),
            (
                "Tinh linh",
                "Hãy cẩn thận, hiệp sĩ. Trên hành trình phía trước, có những thứ mắt thấy chưa chắc đã là thật.",
                "stern"
            ),
            (
                "Hiệp sĩ",
                "Ta sẽ ghi nhớ lời cảnh báo đó. Tạm biệt, tinh linh của khu rừng.",
                "happy"
            ),
            (
                "Tinh linh",
                "Tạm biệt, hiệp sĩ. Chúc ngươi bình an trên con đường phía trước.",
                "happy"
            )
        ]

    def _background(self, path):
        if os.path.isfile(path):
            return cover(
                pygame.image.load(path).convert(),
                self.screen_size
            )

        surface = pygame.Surface(self.screen_size)
        surface.fill((35, 75, 45))
        return surface

    def _text(self, screen, text, font, color, center):
        image = font.render(text, True, color)
        screen.blit(image, image.get_rect(center=center))

    def _wrap(self, text, font, width):
        lines = []
        current = ""

        for word in text.split():
            test = current + " " + word if current else word

            if font.size(test)[0] <= width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines

    def _dialog(self, screen, name, text):
        pw = self.w - 100
        ph = 155
        x = 50
        y = self.h - ph - 25

        panel = pygame.Surface(
            (pw, ph),
            pygame.SRCALPHA
        )

        panel.fill((*PAPER, 250))

        pygame.draw.rect(
            panel,
            PAPER_BORDER,
            panel.get_rect(),
            3,
            border_radius=6
        )

        pygame.draw.rect(
            panel,
            PAPER_BORDER_LIGHT,
            (8, 8, pw - 16, ph - 16),
            1,
            border_radius=4
        )

        pygame.draw.rect(
            panel,
            (225, 210, 181),
            (16, 13, pw - 32, 34),
            border_radius=4
        )

        pygame.draw.line(
            panel,
            PAPER_BORDER_LIGHT,
            (18, 48),
            (pw - 18, 48),
            1
        )

        name_image = self.name_font.render(
            name,
            True,
            INK
        )

        panel.blit(name_image, (28, 19))

        lines = self._wrap(
            text,
            self.font,
            pw - 55
        )

        for i, line in enumerate(lines[:3]):
            image = self.font.render(
                line,
                True,
                INK
            )

            panel.blit(
                image,
                (28, 58 + i * 27)
            )

        screen.blit(panel, (x, y))

        self._text(
            screen,
            "ENTER / SPACE / click để tiếp tục",
            self.small,
            INK_LIGHT,
            (self.w - 180, self.h - 12)
        )

    def _update_walk(self, dt):
        if len(self.knight_walk_frames) <= 1:
            self.knight_frame = 0
            return

        self.knight_animation_timer += dt

        if self.knight_animation_timer >= self.knight_animation_speed:
            self.knight_animation_timer = 0.0
            self.knight_frame = (
                self.knight_frame + 1
            ) % len(self.knight_walk_frames)

    def _draw_knight(self, screen, x, y):
        if not self.knight_walk_frames:
            return

        image = self.knight_walk_frames[
            self.knight_frame % len(self.knight_walk_frames)
        ]

        screen.blit(
            image,
            (int(x), int(y))
        )

    def _draw_dialog_knight(self, screen, side="left"):
        image = self.knight_dialog

        if image is None:
            image = self.knight_idle

        if image is None:
            return

        image = scale_keep_ratio(
            image,
            (235, 300)
        )

        if side == "left":
            rect = image.get_rect(
                midbottom=(170, self.h - 175)
            )
        else:
            image = pygame.transform.flip(
                image,
                True,
                False
            )

            rect = image.get_rect(
                midbottom=(self.w - 155, self.h - 175)
            )

        screen.blit(image, rect)

    def _draw_idle_knight(self, screen, center):
        if self.knight_idle is None:
            return

        image = scale_keep_ratio(
            self.knight_idle,
            (200, 270)
        )

        rect = image.get_rect(
            midbottom=center
        )

        screen.blit(image, rect)

    def _spirit(self, screen, expression, center, size=(235, 270)):
        image = self.spirits.get(expression)

        if image is None:
            image = self.spirits.get("curious")

        if image is None:
            return

        image = scale_keep_ratio(
            image,
            size
        )

        screen.blit(
            image,
            image.get_rect(center=center)
        )

    def _mist(self, screen):
        layer = pygame.Surface(
            self.screen_size,
            pygame.SRCALPHA
        )

        for i in range(8):
            x = int(
                (
                    self.timer * (20 + i * 4)
                    + i * 160
                ) % (self.w + 280)
            ) - 140

            pygame.draw.ellipse(
                layer,
                (235, 246, 224, 22),
                (x, 80 + i * 60, 250, 48)
            )

        screen.blit(layer, (0, 0))

    def _draw_echo(self, screen):
        shade = pygame.Surface(
            self.screen_size,
            pygame.SRCALPHA
        )

        shade.fill((5, 16, 12, 150))
        screen.blit(shade, (0, 0))

        center = (
            self.w // 2,
            145
        )

        wave_layer = pygame.Surface(
            self.screen_size,
            pygame.SRCALPHA
        )

        for i in range(7):
            phase = (
                self.echo_time * 190
                - i * 85
            ) % 600

            progress = phase / 600

            rx = int(35 + progress * 500)
            ry = int(12 + progress * 150)

            alpha = int(
                150 * (1 - progress)
            )

            width = max(
                1,
                int(4 * (1 - progress))
            )

            pygame.draw.ellipse(
                wave_layer,
                (205, 238, 210, alpha),
                (
                    center[0] - rx,
                    center[1] - ry,
                    rx * 2,
                    ry * 2
                ),
                width
            )

        screen.blit(
            wave_layer,
            (0, 0)
        )

        message = "KẺ XÂM NHẬP TỪ ĐÂU ĐẾN?"

        for i in range(4, 0, -1):
            delay = i * 0.16

            progress = (
                self.echo_time - delay
            ) % 2.0

            progress /= 2.0

            scale = 1.0 + progress * 0.18

            alpha = max(
                0,
                int(100 * (1 - progress))
            )

            base = self.echo_font.render(
                message,
                True,
                (205, 235, 210)
            )

            echo = pygame.transform.smoothscale(
                base,
                (
                    int(base.get_width() * scale),
                    int(base.get_height() * scale)
                )
            )

            echo.set_alpha(alpha)

            screen.blit(
                echo,
                echo.get_rect(
                    center=(
                        center[0],
                        center[1] + i * 5
                    )
                )
            )

        main_text = self.echo_font.render(
            message,
            True,
            (240, 248, 232)
        )

        pulse = (
            math.sin(self.echo_time * 3) + 1
        ) / 2

        main_text.set_alpha(
            int(190 + pulse * 65)
        )

        screen.blit(
            main_text,
            main_text.get_rect(center=center)
        )

        if self.echo_time > 0.8:
            self._text(
                screen,
                "Một giọng nói vang lên từ khắp khu rừng...",
                self.font,
                WHITE,
                (self.w // 2, 235)
            )

        self._text(
            screen,
            "ENTER / SPACE / click để tiếp tục",
            self.small,
            GOLD,
            (self.w // 2, self.h - 35)
        )

    def _next(self):
        if self.scene == "approach":
            self.scene = "intro_dialog"
            self.dialog_index = 0
            self.char_progress = 0

        elif self.scene == "intro_dialog":
            line = self.intro_dialogs[
                self.dialog_index
            ][1]

            if self.char_progress < len(line):
                self.char_progress = len(line)
                return

            self.dialog_index += 1
            self.char_progress = 0

            if self.dialog_index == 2:
                self.scene = "echo"
                self.echo_time = 0.0

            elif self.dialog_index >= len(
                self.intro_dialogs
            ):
                self.scene = "puzzle_intro"

        elif self.scene == "echo":
            self.scene = "intro_dialog"
            self.dialog_index = 2
            self.char_progress = 0

        elif self.scene == "puzzle_intro":
            self.puzzle = TangramGame(
                self.game.screen,
                HOUSE,
                self.w,
                self.h
            )

            self.puzzle_done_time = 0.0
            self.scene = "puzzle"

        elif self.scene == "spirit_reveal":
            self.scene = "dialog"
            self.dialog_index = 0
            self.char_progress = 0

        elif self.scene == "dialog":
            line = self.dialogs[
                self.dialog_index
            ][1]

            if self.char_progress < len(line):
                self.char_progress = len(line)
                return

            self.dialog_index += 1
            self.char_progress = 0

            if self.dialog_index >= len(
                self.dialogs
            ):
                self.game_state.forest_gemstone = True
                self.scene = "ending"

        elif self.scene == "ending":
            self.finished = True

    def handle_event(self, event):
        if self.scene == "puzzle":
            if self.puzzle:
                self.puzzle.handle_event(event)
            return

        if (
            event.type == pygame.KEYDOWN
            and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE
            )
        ) or (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            self._next()

    def update(self, dt):
        self.timer += dt

        if self.scene == "approach":
            self._update_walk(dt)

            self.knight_x = min(
                120,
                self.knight_x + 90 * dt
            )

        elif self.scene == "echo":
            self.echo_time += dt

        elif self.scene == "intro_dialog":
            line = self.intro_dialogs[
                self.dialog_index
            ][1]

            self.char_progress = min(
                len(line),
                self.char_progress + dt * 35
            )

        elif self.scene == "puzzle" and self.puzzle:
            self.puzzle.update()

            if self.puzzle.completed:
                self.puzzle_done_time += dt

                if self.puzzle_done_time > 1.6:
                    self.scene = "spirit_reveal"
                    self.timer = 0.0

        elif self.scene == "dialog":
            line = self.dialogs[
                self.dialog_index
            ][1]

            self.char_progress = min(
                len(line),
                self.char_progress + dt * 35
            )

    def draw(self, screen):
        if self.scene == "puzzle" and self.puzzle:
            self.puzzle.draw()
            return

        screen.blit(
            self.forest,
            (0, 0)
        )

        if self.scene == "approach":
            ghost = self.house_bg.copy()

            ghost.set_alpha(
                int(
                    25
                    + 150 * (
                        0.5
                        + 0.5 * math.sin(
                            self.timer * 2
                        )
                    )
                )
            )

            screen.blit(
                ghost,
                (0, 0)
            )

            self._mist(screen)

            self._draw_knight(
                screen,
                self.knight_x,
                self.h - 245
            )

            self._text(
                screen,
                "RỪNG TINH LINH",
                self.heading,
                GOLD,
                (self.w // 2, 42)
            )

            self._dialog(
                screen,
                "Hiệp sĩ",
                "Một ngôi nhà giữa khu rừng...? "
                "Ta phải tiến lại gần xem sao."
            )

        elif self.scene == "intro_dialog":
            self._mist(screen)

            speaker, text = self.intro_dialogs[
                self.dialog_index
            ]

            self._draw_dialog_knight(
                screen,
                "left"
            )

            self._dialog(
                screen,
                speaker,
                text[:int(self.char_progress)]
            )

        elif self.scene == "echo":
            self._draw_echo(screen)

        elif self.scene == "puzzle_intro":
            shade = pygame.Surface(
                self.screen_size,
                pygame.SRCALPHA
            )

            shade.fill(
                (10, 23, 15, 145)
            )

            screen.blit(
                shade,
                (0, 0)
            )

            self._text(
                screen,
                "KÝ ỨC BỊ ĐÁNH RƠI",
                self.heading,
                GOLD,
                (self.w // 2, 90)
            )

            self._text(
                screen,
                "Một bức tranh khu rừng "
                "có ngôi nhà nằm trên nền đất.",
                self.font,
                WHITE,
                (self.w // 2, 235)
            )

            self._text(
                screen,
                "Những miếng gỗ vương vãi "
                "cạnh một khung gỗ trống.",
                self.font,
                WHITE,
                (self.w // 2, 275)
            )

            self._text(
                screen,
                "Hãy ghép các mảnh lại "
                "để khôi phục bức tranh.",
                self.font,
                WHITE,
                (self.w // 2, 315)
            )

            self._text(
                screen,
                "ENTER / SPACE / click để bắt đầu",
                self.small,
                GOLD,
                (self.w // 2, self.h - 45)
            )

        elif self.scene == "spirit_reveal":
            glow = pygame.Surface(
                self.screen_size,
                pygame.SRCALPHA
            )

            glow.fill(
                (28, 54, 30, 80)
            )

            screen.blit(
                glow,
                (0, 0)
            )

            center = (
                self.w // 2,
                self.h // 2 - 55
            )

            ring_layer = pygame.Surface(
                self.screen_size,
                pygame.SRCALPHA
            )

            for i in range(5):
                phase = (
                    self.timer * 110
                    + i * 65
                ) % 190

                radius = int(40 + phase)

                alpha = max(
                    0,
                    int(
                        100 * (
                            1 - phase / 190
                        )
                    )
                )

                pygame.draw.circle(
                    ring_layer,
                    (218, 245, 137, alpha),
                    center,
                    radius,
                    2
                )

            screen.blit(
                ring_layer,
                (0, 0)
            )

            self._spirit(
                screen,
                "surprised",
                center,
                (255, 295)
            )

            self._text(
                screen,
                "Một tinh linh hiện ra giữa ánh sáng!",
                self.heading,
                GOLD,
                (self.w // 2, 55)
            )

            self._text(
                screen,
                "ENTER / SPACE / click để đối thoại",
                self.small,
                WHITE,
                (self.w // 2, self.h - 35)
            )

        elif self.scene == "dialog":
            shade = pygame.Surface(
                self.screen_size,
                pygame.SRCALPHA
            )

            shade.fill(
                (0, 0, 0, 45)
            )

            screen.blit(
                shade,
                (0, 0)
            )

            speaker, text, spirit_expression = self.dialogs[
                self.dialog_index
            ]

            self._spirit(
                screen,
                spirit_expression,
                (
                    self.w // 2 - 300,
                    self.h // 2 - 80
                ),
                (255, 295)
            )

            self._draw_dialog_knight(
                screen,
                "right"
            )

            self._dialog(
                screen,
                speaker,
                text[:int(self.char_progress)]
            )

        elif self.scene == "ending":
            shade = pygame.Surface(
                self.screen_size,
                pygame.SRCALPHA
            )

            shade.fill(
                (5, 15, 10, 130)
            )

            screen.blit(
                shade,
                (0, 0)
            )

            self._draw_idle_knight(
                screen,
                (
                    self.w // 2,
                    self.h - 170
                )
            )

            self._text(
                screen,
                "ĐÁ QUÝ TINH LINH",
                self.heading,
                GOLD,
                (self.w // 2, 80)
            )

            self._text(
                screen,
                "Bạn đã nhận được đá quý tinh linh.",
                self.font,
                WHITE,
                (self.w // 2, self.h - 130)
            )

            self._text(
                screen,
                "Điểm đến tiếp theo: ĐẦM LẦY ĐỘC",
                self.font,
                GOLD,
                (self.w // 2, self.h - 90)
            )

            self._text(
                screen,
                "ENTER / SPACE / click để tiếp tục",
                self.small,
                WHITE,
                (self.w // 2, self.h - 40)
            )

    def is_finished(self):
        return self.finished

    def get_next_scene(self):
        if self.finished:
            return "swamp"

        return None


def create_forest_scene(game):
    return ForestScene(game)
