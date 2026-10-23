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

SPIRIT_SHEET = os.path.join(
    SPR,
    "spirit",
    "new spirit.png"
)

KNIGHT_DIR = os.path.join(
    SPR,
    "knight"
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
PAPER_LIGHT = (250, 244, 226)
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


def load_knight(size):
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
                    KNIGHT_DIR,
                    ext
                )
            )
        )

    paths.sort(
        key=lambda p: (
            0
            if any(
                key in os.path.basename(p).lower()
                for key in (
                    "idle",
                    "front",
                    "dialog",
                    "talk",
                    "stand",
                    "knight"
                )
            )
            else 1,
            p
        )
    )

    for path in paths:
        try:
            image = pygame.image.load(
                path
            ).convert_alpha()

            # Cắt phần trong suốt xung quanh nhân vật
            rect = image.get_bounding_rect()

            if rect.width > 0 and rect.height > 0:
                image = image.subsurface(
                    rect
                ).copy()

            iw, ih = image.get_size()

            if iw <= 0 or ih <= 0:
                continue

            # Giữ nguyên tỉ lệ
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

        except pygame.error:
            continue

    return None


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

    for name, (col, row) in EXPRESSIONS.items():
        frame = sheet.subsurface(
            (
                col * cw,
                row * ch,
                cw,
                ch
            )
        ).copy()

        rect = frame.get_bounding_rect()

        if rect.width > 0 and rect.height > 0:
            frame = frame.subsurface(
                rect
            ).copy()

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

        # Font
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

        # Font riêng cho tiếng vọng
        self.echo_font = pygame.font.SysFont(
            "georgia",
            31,
            bold=True
        )

        # Background
        self.forest = self._background(
            FOREST
        )

        self.house_bg = self._background(
            HOUSE
        )

        # Nhân vật
        self.knight = load_knight(
            (135, 190)
        )

        self.knight_dialog = load_knight(
            (175, 245)
        )

        self.spirits = load_spirit_frames()

        # Game state
        self.game_state = game.game_state

        # Scene state
        self.scene = "approach"

        self.timer = 0.0
        self.echo_time = 0.0

        self.knight_x = -170

        self.dialog_index = 0
        self.char_progress = 0.0

        self.puzzle = None
        self.puzzle_done_time = 0.0

        self.finished = False

        # Hội thoại trước câu đố
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

        # Hội thoại sau khi giải câu đố
        self.dialogs = [
            (
                "Tinh linh",
                "Ngươi đã khôi phục được bức tranh "
                "mà khu rừng che giấu. Ta công nhận trí tuệ của ngươi.",
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

    def _background(self, path):
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
            test = (
                word
                if not current
                else current + " " + word
            )

            if font.size(test)[0] <= width:
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

        # Giấy cổ
        panel = pygame.Surface(
            (pw, ph),
            pygame.SRCALPHA
        )

        panel.fill(
            (*PAPER, 248)
        )

        # Viền ngoài
        pygame.draw.rect(
            panel,
            PAPER_BORDER,
            panel.get_rect(),
            3,
            border_radius=5
        )

        # Viền trong
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

        # Thanh tên
        pygame.draw.rect(
            panel,
            (225, 210, 181),
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
            (18, 48),
            (pw - 18, 48),
            1
        )

        name_image = self.name_font.render(
            name,
            True,
            INK
        )

        panel.blit(
            name_image,
            (28, 19)
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
            (x, y)
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

    def _knight(
        self,
        screen,
        x,
        y,
        size=None
    ):
        image = self.knight

        if size is not None and image is not None:
            iw, ih = image.get_size()

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

            image = pygame.transform.smoothscale(
                image,
                new_size
            )

        if image is not None:
            screen.blit(
                image,
                (
                    int(x),
                    int(y)
                )
            )

        else:
            pygame.draw.circle(
                screen,
                (90, 105, 112),
                (
                    int(x + 60),
                    int(y + 35)
                ),
                27
            )

            pygame.draw.rect(
                screen,
                (65, 75, 85),
                (
                    int(x + 30),
                    int(y + 60),
                    60,
                    95
                ),
                border_radius=10
            )

    def _draw_dialog_knight(
        self,
        screen,
        side="left"
    ):
        if self.knight_dialog is None:
            return

        image = self.knight_dialog

        if side == "left":
            rect = image.get_rect(
                midbottom=(
                    170,
                    self.h - 175
                )
            )

        else:
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
                (174, 220, 116),
                center,
                55
            )

            return

        image = pygame.transform.smoothscale(
            image,
            size
        )

        screen.blit(
            image,
            image.get_rect(
                center=center
            )
        )

    def _mist(self, screen):
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
                % (self.w + 280)
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

    def _draw_echo(self, screen):
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

        # Sóng nước lan ra
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

            rx = int(
                35 + progress * 500
            )

            ry = int(
                12 + progress * 150
            )

            alpha = int(
                150 * (
                    1 - progress
                )
            )

            width = max(
                1,
                int(
                    4 * (
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

        # Chữ vọng tan dần
        message = (
            "KẺ XÂM NHẬP TỪ ĐÂU ĐẾN?"
        )

        for i in range(4, 0, -1):
            delay = i * 0.16

            progress = (
                self.echo_time - delay
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

            base = self.echo_font.render(
                message,
                True,
                (
                    205,
                    235,
                    210
                )
            )

            echo = pygame.transform.smoothscale(
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

            echo.set_alpha(
                alpha
            )

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
            (
                240,
                248,
                232
            )
        )

        pulse = (
            math.sin(
                self.echo_time * 3
            ) + 1
        ) / 2

        main_text.set_alpha(
            int(
                190 + pulse * 65
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

    def draw_game_state(
        self,
        screen
    ):
        hp = getattr(
            self.game_state,
            "hp",
            100
        )

        max_hp = getattr(
            self.game_state,
            "max_hp",
            100
        )

        blessing = getattr(
            self.game_state,
            "forest_blessing",
            False
        )

        panel_w = 270
        panel_h = 82

        panel = pygame.Surface(
            (
                panel_w,
                panel_h
            ),
            pygame.SRCALPHA
        )

        panel.fill(
            (
                20,
                20,
                20,
                185
            )
        )

        pygame.draw.rect(
            panel,
            PAPER_BORDER_LIGHT,
            panel.get_rect(),
            2,
            border_radius=8
        )

        title_font = pygame.font.SysFont(
            "arial",
            17,
            bold=True
        )

        text_font = pygame.font.SysFont(
            "arial",
            15
        )

        title = title_font.render(
            "HIỆP SĨ",
            True,
            (
                245,
                225,
                180
            )
        )

        panel.blit(
            title,
            (12, 8)
        )

        hp_text = text_font.render(
            f"HP  {hp}/{max_hp}",
            True,
            WHITE
        )

        panel.blit(
            hp_text,
            (12, 31)
        )

        bar_x = 82
        bar_y = 34
        bar_w = 170
        bar_h = 12

        pygame.draw.rect(
            panel,
            (
                65,
                65,
                65
            ),
            (
                bar_x,
                bar_y,
                bar_w,
                bar_h
            ),
            border_radius=5
        )

        hp_ratio = 0

        if max_hp > 0:
            hp_ratio = max(
                0,
                min(
                    1,
                    hp / max_hp
                )
            )

        pygame.draw.rect(
            panel,
            (
                75,
                165,
                85
            ),
            (
                bar_x,
                bar_y,
                int(
                    bar_w * hp_ratio
                ),
                bar_h
            ),
            border_radius=5
        )

        if blessing:
            status = text_font.render(
                "Trạng thái: Kháng khí độc",
                True,
                GOLD
            )
        else:
            status = text_font.render(
                "Trạng thái: Bình thường",
                True,
                WHITE
            )

        panel.blit(
            status,
            (12, 57)
        )

        screen.blit(
            panel,
            (15, 15)
        )

    def _next(self):
        if self.scene == "approach":
            # Bắt đầu hội thoại,
            # chưa được vào câu đố
            self.scene = "intro_dialog"
            self.dialog_index = 0
            self.char_progress = 0

        elif self.scene == "intro_dialog":
            line = self.intro_dialogs[
                self.dialog_index
            ][1]

            # Nếu chữ đang chạy,
            # bấm lần đầu chỉ hiện hết câu
            if (
                self.char_progress
                < len(line)
            ):
                self.char_progress = len(line)
                return

            self.dialog_index += 1
            self.char_progress = 0

            # Sau 2 câu đầu mới có tiếng vọng
            if self.dialog_index == 2:
                self.scene = "echo"
                self.echo_time = 0.0

            elif (
                self.dialog_index
                >= len(
                    self.intro_dialogs
                )
            ):
                self.scene = "puzzle_intro"

        elif self.scene == "echo":
            # Quay lại hội thoại
            # sau khi hiệu ứng tiếng vọng kết thúc
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

            if (
                self.char_progress
                < len(line)
            ):
                self.char_progress = len(line)
                return

            self.dialog_index += 1
            self.char_progress = 0

            if (
                self.dialog_index
                >= len(self.dialogs)
            ):
                self.game_state.forest_blessing = True
                self.scene = "ending"

        elif self.scene == "ending":
            self.finished = True

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
                event.type == pygame.KEYDOWN
                and event.key in (
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

    def update(
        self,
        dt
    ):
        self.timer += dt

        if self.scene == "approach":
            self.knight_x = min(
                120,
                self.knight_x
                + 90 * dt
            )

        elif self.scene == "echo":
            self.echo_time += dt

        elif self.scene == "intro_dialog":
            line = self.intro_dialogs[
                self.dialog_index
            ][1]

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
            line = self.dialogs[
                self.dialog_index
            ][1]

            self.char_progress = min(
                len(line),
                self.char_progress
                + dt * 35
            )

    def draw(
        self,
        screen
    ):
        # Puzzle tự vẽ toàn màn hình
        if (
            self.scene == "puzzle"
            and self.puzzle
        ):
            self.puzzle.draw()
            self.draw_game_state(
                screen
            )
            return

        screen.blit(
            self.forest,
            (0, 0)
        )

        # -------------------------
        # ĐI VÀO RỪNG
        # -------------------------
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

            self._mist(
                screen
            )

            self._knight(
                screen,
                self.knight_x,
                self.h - 245
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
        elif self.scene == "intro_dialog":
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
        # GIỚI THIỆU CÂU ĐỐ
        # -------------------------
        elif self.scene == "puzzle_intro":
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
        elif self.scene == "spirit_reveal":
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
                center
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
        # HỘI THOẠI VỚI TINH LINH
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

            speaker, text, expression = (
                self.dialogs[
                    self.dialog_index
                ]
            )

            # Tinh linh bên trái
            self._spirit(
                screen,
                expression,
                (
                    self.w // 2 - 250,
                    self.h // 2 - 80
                ),
                (205, 235)
            )

            # Hiệp sĩ bên phải
            if self.knight_dialog is not None:
                rect = self.knight_dialog.get_rect(
                    midbottom=(
                        self.w - 155,
                        self.h - 175
                    )
                )

                screen.blit(
                    self.knight_dialog,
                    rect
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

            if self.knight_dialog is not None:
                rect = self.knight_dialog.get_rect(
                    midbottom=(
                        self.w // 2,
                        self.h - 170
                    )
                )

                screen.blit(
                    self.knight_dialog,
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

        # Game stat luôn hiện
        self.draw_game_state(
            screen
        )

    def is_finished(self):
        return self.finished

    def get_next_scene(self):
        if self.finished:
            return "swamp"

        return None


def create_forest_scene(game):
    return ForestScene(game)
