import glob
import math
import os
import pygame

from scene import Scene
from settings import GOLD, WHITE
from puzzes.forest.for_puz import TangramGame


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

IMG = os.path.join(
    ROOT,
    "assets",
    "images",
    "sence_2"
)

SPR = os.path.join(
    ROOT,
    "assets",
    "sprites"
)

HOUSE = os.path.join(
    IMG,
    "793802490_29353841374216909_1805474976622337015_n.png"
)

FOREST = os.path.join(
    IMG,
    "forest_no_house.png"
)

KNIGHT_DIR = os.path.join(
    SPR,
    "knight"
)

SPIRIT_DIR = os.path.join(
    SPR,
    "spirit"
)

SPIRIT_SHEET = os.path.join(
    SPIRIT_DIR,
    "new spirit.png"
)


EXPRESSIONS = {
    "curious": (0, 0),
    "stern": (1, 0),
    "surprised": (2, 0),
    "happy": (0, 1),
    "angry": (1, 1),
    "thinking": (2, 1)
}


PAPER = (244, 235, 210)
PAPER_BORDER = (111, 78, 43)
PAPER_BORDER_LIGHT = (157, 119, 72)

INK = (45, 35, 25)
INK_LIGHT = (75, 55, 38)


def cover(image, size):
    iw, ih = image.get_size()

    scale = max(
        size[0] / iw,
        size[1] / ih
    )

    image = pygame.transform.smoothscale(
        image,
        (
            int(iw * scale),
            int(ih * scale)
        )
    )

    x = (
        image.get_width()
        - size[0]
    ) // 2

    y = (
        image.get_height()
        - size[1]
    ) // 2

    return image.subsurface(
        (
            x,
            y,
            size[0],
            size[1]
        )
    ).copy()


def scale_keep_ratio(image, size):
    iw, ih = image.get_size()

    if iw <= 0 or ih <= 0:
        return image

    scale = min(
        size[0] / iw,
        size[1] / ih
    )

    new_size = (
        max(
            1,
            int(iw * scale)
        ),
        max(
            1,
            int(ih * scale)
        )
    )

    return pygame.transform.smoothscale(
        image,
        new_size
    )


def crop_transparent(image):
    rect = image.get_bounding_rect()

    if rect.width > 0 and rect.height > 0:
        return image.subsurface(
            rect
        ).copy()

    return image


def get_image_paths(folder):
    paths = []

    for ext in (
        "*.png",
        "*.webp",
        "*.jpg",
        "*.jpeg"
    ):
        paths.extend(
            glob.glob(
                os.path.join(
                    folder,
                    "**",
                    ext
                ),
                recursive=True
            )
        )

    paths.sort()

    return paths


def get_animation_name(path):
    name = os.path.basename(
        path
    ).lower()

    parent = os.path.basename(
        os.path.dirname(path)
    ).lower()

    text = parent + " " + name

    if (
        "walk" in text
        or "walking" in text
        or "move" in text
    ):
        return "walk"

    if (
        "run" in text
        or "running" in text
    ):
        return "walk"

    if (
        "talk" in text
        or "dialog" in text
        or "speak" in text
    ):
        return "talk"

    if (
        "idle" in text
        or "stand" in text
        or "front" in text
    ):
        return "idle"

    return "idle"


def load_knight_animations(size):
    animations = {
        "idle": [],
        "walk": [],
        "talk": []
    }

    paths = get_image_paths(
        KNIGHT_DIR
    )

    for path in paths:
        try:
            image = pygame.image.load(
                path
            ).convert_alpha()

            image = crop_transparent(
                image
            )

            image = scale_keep_ratio(
                image,
                size
            )

            animation_name = (
                get_animation_name(
                    path
                )
            )

            animations[
                animation_name
            ].append(
                image
            )

        except pygame.error:
            pass

    if not animations["idle"]:
        if animations["walk"]:
            animations["idle"] = [
                animations["walk"][0]
            ]

        elif animations["talk"]:
            animations["idle"] = [
                animations["talk"][0]
            ]

    if not animations["walk"]:
        animations["walk"] = list(
            animations["idle"]
        )

    if not animations["talk"]:
        animations["talk"] = list(
            animations["idle"]
        )

    return animations


def load_spirit_frames():
    result = {}

    if not os.path.isfile(
        SPIRIT_SHEET
    ):
        return result

    try:
        sheet = pygame.image.load(
            SPIRIT_SHEET
        ).convert_alpha()

    except pygame.error:
        return result

    cw = sheet.get_width() // 3
    ch = sheet.get_height() // 2

    for name, (
        col,
        row
    ) in EXPRESSIONS.items():

        frame = sheet.subsurface(
            (
                col * cw,
                row * ch,
                cw,
                ch
            )
        ).copy()

        frame = crop_transparent(
            frame
        )

        result[name] = frame

    return result


class ForestScene(Scene):

    def __init__(self, game):
        super().__init__(game)

        self.screen_size = (
            game.screen.get_size()
        )

        self.w, self.h = (
            self.screen_size
        )

        self.font = pygame.font.SysFont(
            "arial",
            20
        )

        self.small = pygame.font.SysFont(
            "arial",
            14
        )

        self.heading = pygame.font.SysFont(
            "arial",
            30,
            bold=True
        )

        self.name_font = pygame.font.SysFont(
            "arial",
            19,
            bold=True
        )

        self.echo_font = pygame.font.SysFont(
            "georgia",
            31,
            bold=True
        )

        self.forest = self._background(
            FOREST
        )

        self.house_bg = self._background(
            HOUSE
        )

        # -------------------------
        # KNIGHT ANIMATION
        # -------------------------

        self.knight_animations = (
            load_knight_animations(
                (150, 205)
            )
        )

        self.knight_animation = "walk"
        self.knight_frame = 0
        self.knight_animation_timer = 0.0
        self.knight_animation_speed = 0.14

        # -------------------------
        # SPIRIT
        # -------------------------

        self.spirits = (
            load_spirit_frames()
        )

        self.game_state = (
            game.game_state
        )

        # -------------------------
        # SCENE
        # -------------------------

        self.scene = "approach"

        self.timer = 0.0
        self.echo_time = 0.0

        self.knight_x = -170

        self.dialog_index = 0
        self.char_progress = 0.0

        self.puzzle = None
        self.puzzle_done_time = 0.0

        self.finished = False

        # -------------------------
        # HỘI THOẠI TRƯỚC PUZZLE
        # -------------------------

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

        # -------------------------
        # HỘI THOẠI SAU PUZZLE
        # -------------------------

        self.dialogs = [
            (
                "Tinh linh",
                "Ngươi đã khôi phục được bức tranh "
                "mà khu rừng che giấu. "
                "Ta công nhận trí tuệ của ngươi.",
                "happy"
            ),
            (
                "Hiệp sĩ",
                "Ta đang tìm đường đến hang rồng. "
                "Ngươi có biết con đường nào dẫn đến đó không?",
                "thinking"
            ),
            (
                "Tinh linh",
                "Có. Nhưng muốn đến hang rồng, "
                "ngươi phải vượt qua Đầm Lầy Độc ở phía trước.",
                "stern"
            ),
            (
                "Hiệp sĩ",
                "Đầm Lầy Độc? Vậy khí độc trong đó "
                "chính là thứ đang bao phủ khu rừng này sao?",
                "curious"
            ),
            (
                "Tinh linh",
                "Đúng vậy. Khí độc đang dần lan ra "
                "và ăn mòn mọi sinh vật trên đường đi của nó.",
                "stern"
            ),
            (
                "Tinh linh",
                "Ngươi đã chứng minh được trí tuệ của mình. "
                "Ta sẽ ban cho ngươi một lời chúc phúc.",
                "happy"
            ),
            (
                "Tinh linh",
                "Lời chúc này sẽ bảo vệ ngươi khỏi khí độc "
                "khi vượt qua khu rừng và tiến vào đầm lầy.",
                "happy"
            ),
            (
                "Hiệp sĩ",
                "Ta hiểu rồi. Cảm ơn ngươi. "
                "Ta sẽ tiếp tục đến Đầm Lầy Độc "
                "để tìm đường tới hang rồng.",
                "happy"
            ),
            (
                "Tinh linh",
                "Khoan đã... trước khi đi, "
                "hãy nhớ lấy một điều.",
                "thinking"
            ),
            (
                "Tinh linh",
                "Trên hành trình phía trước, "
                "có những thứ mắt thấy chưa chắc đã là thật.",
                "stern"
            ),
            (
                "Hiệp sĩ",
                "Ta sẽ ghi nhớ lời cảnh báo đó. "
                "Tạm biệt, tinh linh của khu rừng.",
                "thinking"
            ),
            (
                "Tinh linh",
                "Tạm biệt, hiệp sĩ. "
                "Chúc ngươi bình an trên con đường phía trước.",
                "happy"
            )
        ]

    def _background(
        self,
        path
    ):
        if os.path.isfile(path):
            return cover(
                pygame.image.load(
                    path
                ).convert(),
                self.screen_size
            )

        surface = pygame.Surface(
            self.screen_size
        )

        surface.fill(
            (35, 75, 45)
        )

        return surface

    def _text(
        self,
        screen,
        text,
        font,
        color,
        center
    ):
        image = font.render(
            text,
            True,
            color
        )

        screen.blit(
            image,
            image.get_rect(
                center=center
            )
        )

    def _wrap(
        self,
        text,
        font,
        width
    ):
        lines = []
        current = ""

        for word in text.split():

            if current:
                test = (
                    current
                    + " "
                    + word
                )
            else:
                test = word

            if (
                font.size(test)[0]
                <= width
            ):
                current = test

            else:
                if current:
                    lines.append(
                        current
                    )

                current = word

        if current:
            lines.append(
                current
            )

        return lines

    # -------------------------
    # HỘI THOẠI GIẤY CỔ
    # -------------------------

    def _dialog(
        self,
        screen,
        name,
        text
    ):
        pw = self.w - 100
        ph = 155

        x = 50
        y = self.h - ph - 25

        panel = pygame.Surface(
            (
                pw,
                ph
            ),
            pygame.SRCALPHA
        )

        panel.fill(
            (
                PAPER[0],
                PAPER[1],
                PAPER[2],
                248
            )
        )

        pygame.draw.rect(
            panel,
            PAPER_BORDER,
            panel.get_rect(),
            3,
            border_radius=5
        )

        pygame.draw.rect(
            panel,
            PAPER_BORDER_LIGHT,
            (
                8,
                8,
                pw - 16,
                ph - 16
            ),
            1,
            border_radius=3
        )

        pygame.draw.rect(
            panel,
            (
                225,
                210,
                181
            ),
            (
                16,
                13,
                pw - 32,
                34
            ),
            border_radius=4
        )

        pygame.draw.line(
            panel,
            PAPER_BORDER_LIGHT,
            (
                18,
                48
            ),
            (
                pw - 18,
                48
            ),
            1
        )

        name_image = (
            self.name_font.render(
                name,
                True,
                INK
            )
        )

        panel.blit(
            name_image,
            (
                28,
                19
            )
        )

        lines = self._wrap(
            text,
            self.font,
            pw - 55
        )

        for i, line in enumerate(
            lines[:3]
        ):
            image = self.font.render(
                line,
                True,
                INK
            )

            panel.blit(
                image,
                (
                    28,
                    58 + i * 27
                )
            )

        screen.blit(
            panel,
            (
                x,
                y
            )
        )

        self._text(
            screen,
            "ENTER / SPACE / click để tiếp tục",
            self.small,
            INK_LIGHT,
            (
                self.w - 180,
                self.h - 12
            )
        )

    # -------------------------
    # KNIGHT ANIMATION
    # -------------------------

    def _set_knight_animation(
        self,
        name
    ):
        if (
            name
            not in self.knight_animations
        ):
            name = "idle"

        if not self.knight_animations[
            name
        ]:
            name = "idle"

        if (
            self.knight_animation
            != name
        ):
            self.knight_animation = name
            self.knight_frame = 0
            self.knight_animation_timer = 0

    def _update_knight_animation(
        self,
        dt
    ):
        frames = (
            self.knight_animations.get(
                self.knight_animation,
                []
            )
        )

        if not frames:
            return

        if len(frames) == 1:
            self.knight_frame = 0
            return

        self.knight_animation_timer += dt

        if (
            self.knight_animation_timer
            >= self.knight_animation_speed
        ):
            self.knight_animation_timer = 0

            self.knight_frame = (
                self.knight_frame + 1
            ) % len(frames)

    def _get_knight_frame(self):
        frames = (
            self.knight_animations.get(
                self.knight_animation,
                []
            )
        )

        if not frames:
            frames = (
                self.knight_animations.get(
                    "idle",
                    []
                )
            )

        if not frames:
            return None

        index = (
            self.knight_frame
            % len(frames)
        )

        return frames[index]

    def _draw_knight(
        self,
        screen,
        x,
        y,
        size=None,
        flip=False
    ):
        image = (
            self._get_knight_frame()
        )

        if image is None:
            pygame.draw.circle(
                screen,
                (90, 105, 112),
                (
                    int(x + 50),
                    int(y + 30)
                ),
                24
            )

            pygame.draw.rect(
                screen,
                (65, 75, 85),
                (
                    int(x + 25),
                    int(y + 55),
                    50,
                    80
                ),
                border_radius=8
            )

            return

        if size is not None:
            image = scale_keep_ratio(
                image,
                size
            )

        if flip:
            image = pygame.transform.flip(
                image,
                True,
                False
            )

        screen.blit(
            image,
            (
                int(x),
                int(y)
            )
        )

    def _draw_dialog_knight(
        self,
        screen,
        side="left"
    ):
        self._set_knight_animation(
            "talk"
        )

        image = (
            self._get_knight_frame()
        )

        if image is None:
            return

        image = scale_keep_ratio(
            image,
            (
                175,
                235
            )
        )

        if side == "left":
            rect = image.get_rect(
                midbottom=(
                    170,
                    self.h - 175
                )
            )

        else:
            # Quay mặt về phía tinh linh
            image = pygame.transform.flip(
                image,
                True,
                False
            )

            rect = image.get_rect(
                midbottom=(
                    self.w - 155,
                    self.h - 175
                )
            )

        screen.blit(
            image,
            rect
        )

    # -------------------------
    # SPIRIT
    # -------------------------

    def _spirit(
        self,
        screen,
        expression,
        center,
        size=(235, 270)
    ):
        image = (
            self.spirits.get(
                expression
            )
            or self.spirits.get(
                "curious"
            )
        )

        if image is None:
            pygame.draw.circle(
                screen,
                (
                    174,
                    220,
                    116
                ),
                center,
                55
            )

            return

        image = scale_keep_ratio(
            image,
            size
        )

        screen.blit(
            image,
            image.get_rect(
                center=center
            )
        )

    # -------------------------
    # SƯƠNG
    # -------------------------

    def _mist(
        self,
        screen
    ):
        layer = pygame.Surface(
            self.screen_size,
            pygame.SRCALPHA
        )

        for i in range(8):
            x = int(
                (
                    self.timer
                    * (20 + i * 4)
                    + i * 160
                )
                % (
                    self.w + 280
                )
            ) - 140

            pygame.draw.ellipse(
                layer,
                (
                    235,
                    246,
                    224,
                    22
                ),
                (
                    x,
                    80 + i * 60,
                    250,
                    48
                )
            )

        screen.blit(
            layer,
            (0, 0)
        )

    # -------------------------
    # TIẾNG VỌNG
    # -------------------------

    def _draw_echo(
        self,
        screen
    ):
        shade = pygame.Surface(
            self.screen_size,
            pygame.SRCALPHA
        )

        shade.fill(
            (
                5,
                16,
                12,
                150
            )
        )

        screen.blit(
            shade,
            (0, 0)
        )

        center = (
            self.w // 2,
            self.h // 2 - 50
        )

        wave_layer = pygame.Surface(
            self.screen_size,
            pygame.SRCALPHA
        )

        # Sóng lan ra và tan dần
        for i in range(7):
            phase = (
                self.echo_time * 190
                - i * 85
            ) % 600

            progress = (
                phase / 600
            )

            rx = int(
                35
                + progress * 500
            )

            ry = int(
                12
                + progress * 150
            )

            alpha = int(
                150
                * (
                    1 - progress
                )
            )

            width = max(
                1,
                int(
                    4
                    * (
                        1 - progress
                    )
                )
            )

            pygame.draw.ellipse(
                wave_layer,
                (
                    205,
                    238,
                    210,
                    alpha
                ),
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

        message = (
            "KẺ XÂM NHẬP TỪ ĐÂU ĐẾN?"
        )

        # Các lớp chữ vọng
        for i in range(
            4,
            0,
            -1
        ):
            delay = i * 0.16

            progress = (
                self.echo_time
                - delay
            ) % 2.0

            progress /= 2.0

            scale = (
                1.0
                + progress * 0.18
            )

            alpha = max(
                0,
                int(
                    100
                    * (
                        1 - progress
                    )
                )
            )

            base = (
                self.echo_font.render(
                    message,
                    True,
                    (
                        205,
                        235,
                        210
                    )
                )
            )

            echo = (
                pygame.transform.smoothscale(
                    base,
                    (
                        int(
                            base.get_width()
                            * scale
                        ),
                        int(
                            base.get_height()
                            * scale
                        )
                    )
                )
            )

            echo.set_alpha(
                alpha
            )

            screen.blit(
                echo,
                echo.get_rect(
                    center=(
                        center[0],
                        center[1]
                        + i * 5
                    )
                )
            )

        main_text = (
            self.echo_font.render(
                message,
                True,
                (
                    240,
                    248,
                    232
                )
            )
        )

        pulse = (
            math.sin(
                self.echo_time * 3
            ) + 1
        ) / 2

        main_text.set_alpha(
            int(
                190
                + pulse * 65
            )
        )

        screen.blit(
            main_text,
            main_text.get_rect(
                center=center
            )
        )

        if self.echo_time > 0.8:
            self._text(
                screen,
                "Một giọng nói vang lên từ khắp khu rừng...",
                self.font,
                WHITE,
                (
                    self.w // 2,
                    self.h - 110
                )
            )

        self._text(
            screen,
            "ENTER / SPACE / click để tiếp tục",
            self.small,
            GOLD,
            (
                self.w // 2,
                self.h - 35
            )
        )

    # -------------------------
    # CHUYỂN CẢNH
    # -------------------------

    def _next(self):
        if self.scene == "approach":
            self.scene = (
                "intro_dialog"
            )

            self.dialog_index = 0
            self.char_progress = 0

            self._set_knight_animation(
                "talk"
            )

        elif (
            self.scene
            == "intro_dialog"
        ):
            line = (
                self.intro_dialogs[
                    self.dialog_index
                ][1]
            )

            if (
                self.char_progress
                < len(line)
            ):
                self.char_progress = (
                    len(line)
                )

                return

            self.dialog_index += 1
            self.char_progress = 0

            if self.dialog_index == 2:
                self.scene = "echo"
                self.echo_time = 0.0

                self._set_knight_animation(
                    "idle"
                )

            elif (
                self.dialog_index
                >= len(
                    self.intro_dialogs
                )
            ):
                self.scene = (
                    "puzzle_intro"
                )

                self._set_knight_animation(
                    "idle"
                )

        elif self.scene == "echo":
            self.scene = (
                "intro_dialog"
            )

            self.dialog_index = 2
            self.char_progress = 0

            self._set_knight_animation(
                "talk"
            )

        elif (
            self.scene
            == "puzzle_intro"
        ):
            self.puzzle = TangramGame(
                self.game.screen,
                HOUSE,
                self.w,
                self.h
            )

            self.puzzle_done_time = 0.0

            self.scene = "puzzle"

        elif (
            self.scene
            == "spirit_reveal"
        ):
            self.scene = "dialog"

            self.dialog_index = 0
            self.char_progress = 0

            self._set_knight_animation(
                "talk"
            )

        elif self.scene == "dialog":
            line = (
                self.dialogs[
                    self.dialog_index
                ][1]
            )

            if (
                self.char_progress
                < len(line)
            ):
                self.char_progress = (
                    len(line)
                )

                return

            self.dialog_index += 1
            self.char_progress = 0

            if (
                self.dialog_index
                >= len(
                    self.dialogs
                )
            ):
                # Vẫn lưu chúc phúc để map sau sử dụng
                if hasattr(
                    self,
                    "game_state"
                ):
                    self.game_state.forest_blessing = True

                self.scene = "ending"

                self._set_knight_animation(
                    "idle"
                )

        elif self.scene == "ending":
            self.finished = True

    # -------------------------
    # EVENT
    # -------------------------

    def handle_event(
        self,
        event
    ):
        if self.scene == "puzzle":
            if self.puzzle:
                self.puzzle.handle_event(
                    event
                )

            return

        if (
            (
                event.type
                == pygame.KEYDOWN
                and event.key
                in (
                    pygame.K_RETURN,
                    pygame.K_SPACE
                )
            )
            or
            (
                event.type
                == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            )
        ):
            self._next()

    # -------------------------
    # UPDATE
    # -------------------------

    def update(
        self,
        dt
    ):
        self.timer += dt

        self._update_knight_animation(
            dt
        )

        if self.scene == "approach":
            self._set_knight_animation(
                "walk"
            )

            self.knight_x = min(
                120,
                self.knight_x
                + 90 * dt
            )

            if self.knight_x >= 120:
                self._set_knight_animation(
                    "idle"
                )

        elif self.scene == "echo":
            self.echo_time += dt

        elif (
            self.scene
            == "intro_dialog"
        ):
            self._set_knight_animation(
                "talk"
            )

            line = (
                self.intro_dialogs[
                    self.dialog_index
                ][1]
            )

            self.char_progress = min(
                len(line),
                self.char_progress
                + dt * 35
            )

        elif (
            self.scene == "puzzle"
            and self.puzzle
        ):
            self.puzzle.update()

            if self.puzzle.completed:
                self.puzzle_done_time += dt

                if (
                    self.puzzle_done_time
                    > 1.6
                ):
                    self.scene = (
                        "spirit_reveal"
                    )

                    self.timer = 0.0

        elif self.scene == "dialog":
            self._set_knight_animation(
                "talk"
            )

            line = (
                self.dialogs[
                    self.dialog_index
                ][1]
            )

            self.char_progress = min(
                len(line),
                self.char_progress
                + dt * 35
            )

        elif self.scene == "ending":
            self._set_knight_animation(
                "idle"
            )

    # -------------------------
    # DRAW
    # -------------------------

    def draw(
        self,
        screen
    ):
        # -------------------------
        # PUZZLE
        # -------------------------

        if (
            self.scene == "puzzle"
            and self.puzzle
        ):
            self.puzzle.draw()

            return

        screen.blit(
            self.forest,
            (0, 0)
        )

        # -------------------------
        # ĐI VÀO RỪNG
        # -------------------------

        if self.scene == "approach":
            ghost = (
                self.house_bg.copy()
            )

            ghost.set_alpha(
                int(
                    25
                    + 150
                    * (
                        0.5
                        + 0.5
                        * math.sin(
                            self.timer * 2
                        )
                    )
                )
            )

            screen.blit(
                ghost,
                (0, 0)
            )

            self._mist(
                screen
            )

            self._draw_knight(
                screen,
                self.knight_x,
                self.h - 245,
                (
                    145,
                    200
                )
            )

            self._text(
                screen,
                "RỪNG TINH LINH",
                self.heading,
                GOLD,
                (
                    self.w // 2,
                    42
                )
            )

            self._dialog(
                screen,
                "Hiệp sĩ",
                "Một ngôi nhà giữa khu rừng...? "
                "Ta phải tiến lại gần xem sao."
            )

        # -------------------------
        # HỘI THOẠI MỞ ĐẦU
        # -------------------------

        elif (
            self.scene
            == "intro_dialog"
        ):
            self._mist(
                screen
            )

            speaker, text = (
                self.intro_dialogs[
                    self.dialog_index
                ]
            )

            self._draw_dialog_knight(
                screen,
                "left"
            )

            self._dialog(
                screen,
                speaker,
                text[
                    :int(
                        self.char_progress
                    )
                ]
            )

        # -------------------------
        # TIẾNG VỌNG
        # -------------------------

        elif self.scene == "echo":
            self._draw_echo(
                screen
            )

        # -------------------------
        # GIỚI THIỆU PUZZLE
        # -------------------------

        elif (
            self.scene
            == "puzzle_intro"
        ):
            shade = pygame.Surface(
                self.screen_size,
                pygame.SRCALPHA
            )

            shade.fill(
                (
                    10,
                    23,
                    15,
                    145
                )
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
                (
                    self.w // 2,
                    90
                )
            )

            self._text(
                screen,
                "Một bức tranh khu rừng "
                "có ngôi nhà nằm trên nền đất.",
                self.font,
                WHITE,
                (
                    self.w // 2,
                    235
                )
            )

            self._text(
                screen,
                "Những miếng gỗ vương vãi "
                "cạnh một khung gỗ trống.",
                self.font,
                WHITE,
                (
                    self.w // 2,
                    275
                )
            )

            self._text(
                screen,
                "Hãy ghép các mảnh lại "
                "để khôi phục bức tranh.",
                self.font,
                WHITE,
                (
                    self.w // 2,
                    315
                )
            )

            self._text(
                screen,
                "ENTER / SPACE / click để bắt đầu",
                self.small,
                GOLD,
                (
                    self.w // 2,
                    self.h - 45
                )
            )

        # -------------------------
        # TINH LINH XUẤT HIỆN
        # -------------------------

        elif (
            self.scene
            == "spirit_reveal"
        ):
            glow = pygame.Surface(
                self.screen_size,
                pygame.SRCALPHA
            )

            glow.fill(
                (
                    28,
                    54,
                    30,
                    80
                )
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

                radius = int(
                    40 + phase
                )

                alpha = max(
                    0,
                    int(
                        100
                        * (
                            1
                            - phase / 190
                        )
                    )
                )

                pygame.draw.circle(
                    ring_layer,
                    (
                        218,
                        245,
                        137,
                        alpha
                    ),
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
                (
                    230,
                    265
                )
            )

            self._text(
                screen,
                "Một tinh linh hiện ra giữa ánh sáng!",
                self.heading,
                GOLD,
                (
                    self.w // 2,
                    55
                )
            )

            self._text(
                screen,
                "ENTER / SPACE / click để đối thoại",
                self.small,
                WHITE,
                (
                    self.w // 2,
                    self.h - 35
                )
            )

        # -------------------------
        # HỘI THOẠI TINH LINH
        # -------------------------

        elif self.scene == "dialog":
            shade = pygame.Surface(
                self.screen_size,
                pygame.SRCALPHA
            )

            shade.fill(
                (
                    0,
                    0,
                    0,
                    45
                )
            )

            screen.blit(
                shade,
                (0, 0)
            )

            (
                speaker,
                text,
                expression
            ) = self.dialogs[
                self.dialog_index
            ]

            # Tinh linh bên trái
            self._spirit(
                screen,
                expression,
                (
                    self.w // 2 - 250,
                    self.h // 2 - 80
                ),
                (
                    205,
                    235
                )
            )

            # Hiệp sĩ bên phải
            self._draw_dialog_knight(
                screen,
                "right"
            )

            self._dialog(
                screen,
                speaker,
                text[
                    :int(
                        self.char_progress
                    )
                ]
            )

        # -------------------------
        # KẾT THÚC
        # -------------------------

        elif self.scene == "ending":
            shade = pygame.Surface(
                self.screen_size,
                pygame.SRCALPHA
            )

            shade.fill(
                (
                    5,
                    15,
                    10,
                    130
                )
            )

            screen.blit(
                shade,
                (0, 0)
            )

            image = (
                self._get_knight_frame()
            )

            if image is not None:
                image = scale_keep_ratio(
                    image,
                    (
                        160,
                        220
                    )
                )

                rect = image.get_rect(
                    midbottom=(
                        self.w // 2,
                        self.h - 170
                    )
                )

                screen.blit(
                    image,
                    rect
                )

            self._text(
                screen,
                "CHÚC PHÚC CỦA TINH LINH",
                self.heading,
                GOLD,
                (
                    self.w // 2,
                    80
                )
            )

            self._text(
                screen,
                "Bạn đã nhận được sự bảo vệ khỏi khí độc.",
                self.font,
                WHITE,
                (
                    self.w // 2,
                    self.h - 130
                )
            )

            self._text(
                screen,
                "Điểm đến tiếp theo: ĐẦM LẦY ĐỘC",
                self.font,
                GOLD,
                (
                    self.w // 2,
                    self.h - 90
                )
            )

            self._text(
                screen,
                "ENTER / SPACE / click để tiếp tục",
                self.small,
                WHITE,
                (
                    self.w // 2,
                    self.h - 40
                )
            )

    def is_finished(
        self
    ):
        return self.finished

    def get_next_scene(
        self
    ):
        if self.finished:
            return "swamp"

        return None


def create_forest_scene(
    game
):
    return ForestScene(
        game
    )