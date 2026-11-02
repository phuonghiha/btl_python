import math
import os
import pygame

from base_scene import BaseScene, STANDARD_DIALOG_RECT
from game_fonts import content1, title
from settings import GOLD, WHITE
from puzzes.forest.for_puz import TangramGame


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IMG = os.path.join(ROOT, "assets", "images", "sence_2")
SPR = os.path.join(ROOT, "assets", "sprites")

HOUSE = os.path.join(
    IMG,
    "793802490_29353841374216909_1805474976622337015_n.png"
)

FOREST = os.path.join(IMG, "forest_no_house.png")

KNIGHT_DIR = os.path.join(SPR, "knight")
SPIRIT_DIR = os.path.join(SPR, "spirit")

KNIGHT_IDLE = os.path.join(KNIGHT_DIR, "IDLE", "Đứng_1.png")
KNIGHT_DIALOG = os.path.join(KNIGHT_DIR, "front", "1.png")
KNIGHT_WALK_DIR = os.path.join(KNIGHT_DIR, "Walk_right")

SPIRIT_GEM_IMAGE = os.path.join(
    ROOT, "assets", "images", "gem.png"
)

SPIRIT_FILES = {
    "curious": "new spirit-curious.png",
    "stern": "new spirit - stern.png",
    "surprised": "new spirit - susprised.png",
    "happy": "new spirit - happy.png",
    "angry": "new spirit - warning.png",
    "thinking": "new spirit - normal.png",
}

PAPER = (244, 235, 210)
PAPER_BORDER = (111, 78, 43)
PAPER_BORDER_LIGHT = (157, 119, 72)
INK = (45, 35, 25)
INK_LIGHT = (75, 55, 38)


def cover(image, size):
    iw, ih = image.get_size()

    if iw <= 0 or ih <= 0:
        return pygame.Surface(size)

    scale = max(size[0] / iw, size[1] / ih)

    image = pygame.transform.smoothscale(
        image,
        (
            max(1, int(iw * scale)),
            max(1, int(ih * scale)),
        ),
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
            max(1, int(ih * scale)),
        ),
    )


def crop_transparent(image):
    rect = image.get_bounding_rect()

    if rect.width > 0 and rect.height > 0:
        return image.subsurface(rect).copy()

    return image


def load_image(path):
    if not os.path.isfile(path):
        print(f"[ForestScene] Khong tim thay anh: {path}")
        return None

    try:
        return crop_transparent(
            pygame.image.load(path).convert_alpha()
        )
    except (pygame.error, OSError) as error:
        print(f"[ForestScene] Loi doc anh {path}: {error}")
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


class ForestScene(BaseScene):

    def __init__(self, game):
        super().__init__(game)

        self.game = game
        self.game_state = game.game_state

        # Nếu Forest được tạo lại sau khi rời đi,
        # instance mới sẽ tự bắt đầu với trạng thái ban đầu.
        self._clear_pending_reset()

        self.screen_size = game.screen.get_size()
        self.w, self.h = self.screen_size

        self.font = content1(23)
        self.small = content1(18)
        self.heading = title(30)
        self.name_font = title(22)
        self.echo_font = title(34)

        self.forest = self._background(FOREST)
        self.house_bg = self._background(HOUSE)

        self.knight_idle = load_image(KNIGHT_IDLE)
        self.knight_dialog = load_image(KNIGHT_DIALOG)

        if self.knight_dialog is not None:
            self.knight_dialog = crop_upper_body(
                self.knight_dialog, 0.72
            )

        self.knight_walk_frames = load_walk_frames()

        if not self.knight_walk_frames and self.knight_idle is not None:
            self.knight_walk_frames = [
                scale_keep_ratio(self.knight_idle, (175, 235))
            ]

        self.knight_frame = 0
        self.knight_animation_timer = 0.0
        self.knight_animation_speed = 0.14

        self.spirits = load_spirit_frames()

        self.gem_image = self._load_item_image(
            SPIRIT_GEM_IMAGE, (300, 300)
        )

        # self._init_story_state()

        self.dialogs_with_scale = [
            (
                "Tinh linh",
                "Ngươi đã khôi phục ký ức của khu rừng. Ta công nhận trí tuệ của ngươi.",
                "happy",
            ),
            (
                "Tinh linh",
                "Ta là Tinh Linh, người bảo vệ khu rừng cổ này. Ngươi là ai, đến đây để làm gì?",
                "thinking",
            ),
            (
                "Hiệp sĩ",
                "Ta là hiệp sĩ của nhà vua. Công chúa đã mất tích. Trong phòng nàng, ta tìm thấy một chiếc vảy rồng.",
                "curious",
            ),
            (
                "Hiệp sĩ",
                "Ta muốn tìm công chúa. Xin hãy chỉ cho ta đường đến hang rồng và cách đánh bại con rồng.",
                "curious",
            ),
            (
                "Tinh linh",
                "Vậy thứ ngươi tìm thấy đúng là vảy rồng. Hang rồng nằm phía bên kia Đầm Lầy Độc, nơi khí độc bao phủ lối đi.",
                "surprised",
            ),
            (
                "Tinh linh",
                "Hãy quan sát đòn tấn công của rồng và chờ thời cơ phản công. Nếu có Thánh Kiếm, ngươi sẽ gây sát thương mạnh hơn.",
                "stern",
            ),
            (
                "Tinh linh",
                "Hãy nhận viên đá chúc phúc này. Nó sẽ bảo vệ ngươi trước khí độc trong đầm lầy.",
                "happy",
            ),
            (
                "Hiệp sĩ",
                "Ta sẽ giữ viên đá cẩn thận. Cảm ơn ngươi đã giúp đỡ.",
                "happy",
            ),
            (
                "Tinh linh",
                "Hãy men theo những thân cây phủ rêu, rồi đi về phía dòng nước đen. Lối vào hang rồng nằm sau màn sương.",
                "thinking",
            ),
            (
                "Hiệp sĩ",
                "Ta hiểu rồi. Ta sẽ ghi nhớ lời chỉ dẫn này và tìm cách cứu công chúa.",
                "happy",
            ),
            (
                "Tinh linh",
                "Chúc ngươi bình an, hiệp sĩ. Đừng vội tin mọi thứ ngươi nhìn thấy.",
                "stern",
            ),
        ]

        self.dialogs_without_scale = [
            (
                "Tinh linh",
                "Ngươi đã khôi phục ký ức của khu rừng. Ta công nhận trí tuệ của ngươi.",
                "happy",
            ),
            (
                "Tinh linh",
                "Ta là Tinh Linh, người bảo vệ khu rừng cổ này. Ngươi là ai, đến đây để làm gì?",
                "thinking",
            ),
            (
                "Hiệp sĩ",
                "Ta là hiệp sĩ của nhà vua. Công chúa đã mất tích, và ta được giao nhiệm vụ tìm nàng.",
                "curious",
            ),
            (
                "Tinh linh",
                "Ngươi đã tìm được manh mối nào giúp tìm công chúa chưa?",
                "thinking",
            ),
            (
                "Hiệp sĩ",
                "Chưa. Ta vẫn chưa biết nàng đang ở đâu hay phải bắt đầu từ đâu.",
                "curious",
            ),
            (
                "Tinh linh",
                "Hãy quay lại nơi công chúa từng sống và quan sát thật kỹ. Đôi khi câu trả lời nằm ở nơi ta ít ngờ tới nhất.",
                "stern",
            ),
            (
                "Hiệp sĩ",
                "Ta hiểu rồi. Ta sẽ quay lại phòng công chúa để tìm manh mối.",
                "happy",
            ),
            (
                "Tinh linh",
                "Hãy kiên nhẫn và đừng bỏ qua bất kỳ dấu vết nào.",
                "happy",
            ),
        ]

        self.dialogs_without_scale_return = [
            ("Tinh linh", "Ngươi đã tìm thấy công chúa chưa?", "thinking"),
            ("Hiệp sĩ", "Chưa… Ta vẫn chẳng biết nàng đang ở đâu.", "curious"),
            ("Tinh linh", "Ngươi đã tìm kỹ nơi nàng từng sống chưa?", "stern"),
            ("Hiệp sĩ", "Ta đã tìm, nhưng vẫn chưa hiểu chuyện gì đã xảy ra.", "curious"),
            ("Tinh linh", "Đừng vội rời đi khi chưa xem xét mọi thứ. Hãy trở lại đó và quan sát cẩn thận hơn.", "stern"),
            ("Hiệp sĩ", "Được. Ta sẽ thử lại.", "happy"),
        ]

        self.dialogs_with_scale_return = [
            ("Tinh linh", "Ngươi đã tìm được điều mình cần chưa?", "thinking"),
            ("Hiệp sĩ", "Ta có vảy rồng rồi. Nhưng ta vẫn chưa biết công chúa đang ở đâu.", "curious"),
            ("Tinh linh", "Muốn đến nơi sinh sống của loài rồng, ngươi phải vượt qua Đầm Lầy Độc.", "stern"),
            ("Hiệp sĩ", "Nếu phải đối mặt với rồng, ta cần chuẩn bị những gì?", "curious"),
            ("Tinh linh", "Hãy quan sát chuyển động của đối thủ và chờ thời cơ. Nếu tìm được Thánh Kiếm, cơ hội chiến thắng của ngươi sẽ lớn hơn.", "stern"),
            ("Hiệp sĩ", "Ta sẽ ghi nhớ. Cảm ơn ngài.", "happy"),
            ("Tinh linh", "Hãy nhận viên đá chúc phúc này. Nó sẽ bảo vệ ngươi trước khí độc trong đầm lầy.", "happy"),
            ("Hiệp sĩ", "Ta sẽ giữ viên đá cẩn thận. Cảm ơn ngài.", "happy"),
            ("Tinh linh", "Con đường đến Đầm Lầy Độc nằm phía trước. Hãy cẩn thận với khí độc.", "thinking"),
            ("Tinh linh", "Mong ngươi tìm được công chúa và trở về bình an.", "happy"),
        ]

        self.dialogs = self.dialogs_without_scale

        self.intro_dialogs = [
            (
                "Hiệp sĩ",
                "Một ngôi nhà giữa khu rừng...? "
                "Ta phải tiến lại gần xem sao.",
            ),
            (
                "Hiệp sĩ",
                "Kỳ lạ... vừa rồi nó còn ở đây. "
                "Tại sao lại biến mất?",
            ),
            (
                "???",
                "Kẻ xâm nhập... ngươi đến nơi này "
                "để tìm kiếm điều gì?",
            ),
            (
                "Hiệp sĩ",
                "Ai đó? Hãy hiện thân! "
                "Ta không đến đây để gây chiến.",
            ),
            (
                "???",
                "Muốn được khu rừng công nhận, "
                "đôi mắt của ngươi là chưa đủ.",
            ),
            (
                "???",
                "Nếu thật sự có trí tuệ, "
                "hãy khôi phục lại thứ mà khu rừng đã che giấu.",
            ),
        ]

        self._init_story_state()

        # Chỉ khóa nội dung khi đã có đá chúc phúc VÀ đã hoàn thành câu đố rừng.
        # Chỉ có viên đá chưa đủ để đánh dấu toàn bộ nhiệm vụ đã xong.
        self.already_completed = (
            self._has_spirit_gemstone()
            and bool(self._get_state("forest_puzzle_completed", False))
        )
        if self.already_completed:
            self.scene = "completed_return"


    # =====================================================
    # KHỞI TẠO TRẠNG THÁI
    # =====================================================

    def _init_story_state(self):
        self.scene = "approach"
        self.timer = 0.0
        self.echo_time = 0.0

        self.knight_x = -170

        self.dialog_index = 0
        self.char_progress = 0.0

        self.puzzle = None
        self.puzzle_done_time = 0.0

        self.item_reveal_time = 0.0
        self.item_reveal_kind = None
        self.reveal_return_scene = "dialog"

        self.gem_revealed = False
        self.blessing_granted = False

        self.has_dragon_scale = False
        self.already_completed = False

        self.finished = False
        self.transitioned = False

        self.dialogs = self.dialogs_without_scale

    def _set_state(self, name, value):
        try:
            setattr(self.game_state, name, value)
        except (AttributeError, TypeError):
            print(f"[ForestScene] Khong the cap nhat game_state.{name}")

    def _get_state(self, name, default=False):
        return getattr(self.game_state, name, default)

    def _mark_reset_when_reentering(self):
        """
        Đánh dấu Forest cần khởi động lại khi người chơi
        rời Forest và quay lại sau này.

        Không reset instance hiện tại, vì màn hình ending
        vẫn cần được giữ nguyên khi người chơi mở bản đồ.
        """
        self._set_state("forest_reset_pending", True)

    def _clear_pending_reset(self):
        """
        Xóa cờ reset khi một ForestScene mới được tạo.
        Túi đồ và các dữ liệu khác trong game_state không bị xóa.
        """
        self._set_state("forest_reset_pending", False)

    def on_enter(self):
        """
        Nếu đã nhận đá chúc phúc và hoàn thành câu đố,
        quay lại Forest sẽ không kích hoạt lại nội dung.
        """
        if (
            self._has_spirit_gemstone()
            and bool(self._get_state("forest_puzzle_completed", False))
        ):
            self.already_completed = True
            self.scene = "completed_return"
            return

        if self._get_state("forest_reset_pending", False):
            self._clear_pending_reset()
            self.reset()

    # =====================================================
    # GAME STATE
    # =====================================================

    def _has_dragon_scale(self):
        item_id = "dragon_scale"

        checker = getattr(self.game_state, "has_item", None)

        if callable(checker):
            try:
                if checker(item_id):
                    return True
            except (AttributeError, TypeError, KeyError):
                pass

        inventory = getattr(self.game_state, "inventory", [])

        if isinstance(inventory, dict):
            return item_id in inventory

        try:
            return item_id in inventory
        except TypeError:
            return False

    def _has_spirit_gemstone(self):
        """Kiểm tra đá chúc phúc thật sự có trong túi đồ hoặc trạng thái game."""
        checker = getattr(self.game_state, "has_item", None)
        if callable(checker):
            try:
                if checker("forest_gemstone"):
                    return True
            except (AttributeError, TypeError, KeyError):
                pass

        inventory = getattr(self.game_state, "inventory", [])
        if isinstance(inventory, dict):
            if "forest_gemstone" in inventory:
                return True
        else:
            try:
                if "forest_gemstone" in inventory:
                    return True
            except TypeError:
                pass

        return bool(self._get_state("forest_gemstone", False))

    def _select_story_branch(self):
        self.has_dragon_scale = self._has_dragon_scale()
        previously_met = bool(self._get_state("forest_spirit_met", False))

        # Đã nhận đá chúc phúc và hoàn thành nhiệm vụ: trường hợp 5,
        # quay lại không phát lại hội thoại hoặc câu đố.
        if self._has_spirit_gemstone() and self._get_state("forest_puzzle_completed", False):
            self.already_completed = True
            self.scene = "completed_return"
            return

        if self.has_dragon_scale:
            self.dialogs = (
                self.dialogs_with_scale_return
                if previously_met
                else self.dialogs_with_scale
            )
            print("[ForestScene] Chon nhanh: CO vay rong" + (" - gap lai" if previously_met else " - lan dau"))
        else:
            self.dialogs = (
                self.dialogs_without_scale_return
                if previously_met
                else self.dialogs_without_scale
            )
            print("[ForestScene] Chon nhanh: KHONG CO vay rong" + (" - gap lai" if previously_met else " - lan dau"))

        self._set_state("forest_spirit_met", True)

    def _grant_blessing(self):
        if not self.has_dragon_scale:
            return

        if self.blessing_granted:
            return

        self.blessing_granted = True

        self._set_state("has_poison_protection", True)
        self._set_state("forest_gemstone", True)
        self._set_state("forest_puzzle_completed", True)

        clue = (
            "Qua Đầm Lầy Độc, men theo thân cây phủ rêu "
            "và dòng nước đen. Cửa hang rồng nằm sau màn sương."
        )

        self._set_state("dragon_cave_clue", clue)

        if hasattr(self.game_state, "add_clue"):
            self.game_state.add_clue(clue)

        if hasattr(self.game_state, "complete_puzzle"):
            self.game_state.complete_puzzle("forest_tangram")

        self.add_item(
            "forest_gemstone",
            "Đá chúc phúc tinh linh",
            SPIRIT_GEM_IMAGE
        )

    # =====================================================
    # LOAD ẢNH
    # =====================================================

    def _load_item_image(self, path, size):
        image = load_image(path)

        if image is None:
            return None

        return scale_keep_ratio(image, size)

    def _background(self, path):
        if os.path.isfile(path):
            try:
                return cover(
                    pygame.image.load(path).convert(),
                    self.screen_size,
                )
            except (pygame.error, OSError) as error:
                print(f"[ForestScene] Loi doc nen {path}: {error}")

        surface = pygame.Surface(self.screen_size)
        surface.fill((35, 75, 45))
        return surface

    # =====================================================
    # TEXT
    # =====================================================

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
        rect = STANDARD_DIALOG_RECT
        pw, ph = rect.size
        x, y = rect.topleft

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((*PAPER, 250))

        pygame.draw.rect(
            panel, PAPER_BORDER, panel.get_rect(),
            3, border_radius=6
        )

        pygame.draw.rect(
            panel, PAPER_BORDER_LIGHT,
            (8, 8, pw - 16, ph - 16),
            1, border_radius=4
        )

        pygame.draw.rect(
            panel, (225, 210, 181),
            (16, 13, pw - 32, 34),
            border_radius=4
        )

        pygame.draw.line(
            panel, PAPER_BORDER_LIGHT,
            (18, 48), (pw - 18, 48), 1
        )

        name_image = self.name_font.render(name, True, INK)
        panel.blit(name_image, (28, 19))

        lines = self._wrap(text, self.font, pw - 55)

        for i, line in enumerate(lines[:3]):
            image = self.font.render(line, True, INK)
            panel.blit(image, (28, 50 + i * 25))

        screen.blit(panel, (x, y))

        self._text(
            screen,
            "Click để tiếp tục",
            self.small,
            INK_LIGHT,
            (rect.right - 105, rect.y + 30),
        )

    # =====================================================
    # NHÂN VẬT
    # =====================================================

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

        screen.blit(image, (int(x), int(y)))

    def _draw_dialog_knight(self, screen, side="left"):
        image = self.knight_dialog

        if image is None:
            image = self.knight_idle

        if image is None:
            return

        image = scale_keep_ratio(image, (310, 390))

        if side == "left":
            rect = image.get_rect(
                midbottom=(175, STANDARD_DIALOG_RECT.top + 10)
            )
        else:
            image = pygame.transform.flip(image, True, False)
            rect = image.get_rect(
                midbottom=(self.w - 175, STANDARD_DIALOG_RECT.top + 10)
            )

        screen.blit(image, rect)

    def _draw_idle_knight(self, screen, center):
        if self.knight_idle is None:
            return

        image = scale_keep_ratio(self.knight_idle, (200, 270))
        rect = image.get_rect(midbottom=center)
        screen.blit(image, rect)

    def _spirit(self, screen, expression, center, size=(300, 340)):
        image = self.spirits.get(expression)

        if image is None:
            image = self.spirits.get("curious")

        if image is None:
            return

        image = scale_keep_ratio(image, size)

        glow = pygame.mask.from_surface(image).to_surface(
            setcolor=(235, 255, 235, 100),
            unsetcolor=(0, 0, 0, 0)
        )

        for _ in range(3):
            glow = pygame.transform.smoothscale(
                glow,
                (
                    glow.get_width() + 18,
                    glow.get_height() + 18,
                )
            )

        glow.set_alpha(90)

        rect = image.get_rect(center=center)
        glow_rect = glow.get_rect(center=center)

        screen.blit(glow, glow_rect)
        screen.blit(image, rect)

    # =====================================================
    # SƯƠNG
    # =====================================================

    def _mist(self, screen):
        layer = pygame.Surface(self.screen_size, pygame.SRCALPHA)

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
                (x, 80 + i * 60, 250, 48),
            )

        screen.blit(layer, (0, 0))

    def _draw_echo(self, screen):
        shade = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        shade.fill((5, 16, 12, 150))
        screen.blit(shade, (0, 0))

        center = (self.w // 2, 145)
        wave_layer = pygame.Surface(self.screen_size, pygame.SRCALPHA)

        for i in range(7):
            phase = (self.echo_time * 190 - i * 85) % 600
            progress = phase / 600

            rx = int(35 + progress * 500)
            ry = int(12 + progress * 150)
            alpha = int(150 * (1 - progress))
            width = max(1, int(4 * (1 - progress)))

            pygame.draw.ellipse(
                wave_layer,
                (205, 238, 210, alpha),
                (
                    center[0] - rx,
                    center[1] - ry,
                    rx * 2,
                    ry * 2,
                ),
                width,
            )

        screen.blit(wave_layer, (0, 0))

        message = "Kẻ xâm nhập từ đâu đến?"

        for i in range(4, 0, -1):
            delay = i * 0.16
            progress = (self.echo_time - delay) % 2.0
            progress /= 2.0

            scale = 1.0 + progress * 0.18
            alpha = max(0, int(100 * (1 - progress)))

            base = self.echo_font.render(
                message, True, (205, 235, 210)
            )

            echo = pygame.transform.smoothscale(
                base,
                (
                    max(1, int(base.get_width() * scale)),
                    max(1, int(base.get_height() * scale)),
                ),
            )

            echo.set_alpha(alpha)

            screen.blit(
                echo,
                echo.get_rect(
                    center=(center[0], center[1] + i * 5)
                ),
            )

        main_text = self.echo_font.render(
            message, True, (240, 248, 232)
        )

        pulse = (math.sin(self.echo_time * 3) + 1) / 2
        main_text.set_alpha(int(190 + pulse * 65))

        screen.blit(
            main_text,
            main_text.get_rect(center=center),
        )

        if self.echo_time > 0.8:
            self._text(
                screen,
                "Một giọng nói vang lên từ khắp khu rừng...",
                self.font,
                WHITE,
                (self.w // 2, 235),
            )

        self._text(
            screen,
            "Click để tiếp tục",
            self.small,
            GOLD,
            (self.w // 2, self.h - 35),
        )

    # =====================================================
    # VẬT PHẨM
    # =====================================================

    def _draw_item_reveal(self, screen, kind):
        shade = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 215))
        screen.blit(shade, (0, 0))

        cx = self.w // 2
        cy = self.h // 2 - 45

        pulse = 0.5 + 0.5 * math.sin(self.item_reveal_time * 3.5)
        radius = int(125 + pulse * 18)

        glow = pygame.Surface(self.screen_size, pygame.SRCALPHA)

        pygame.draw.circle(
            glow,
            (218, 183, 105, 35),
            (cx, cy),
            radius,
        )

        pygame.draw.circle(
            glow,
            (218, 220, 150, 150),
            (cx, cy),
            radius,
            2,
        )

        for i in range(8):
            angle = self.item_reveal_time * 0.7 + i * math.pi / 4

            x1 = cx + int(math.cos(angle) * (radius + 8))
            y1 = cy + int(math.sin(angle) * (radius + 8))
            x2 = cx + int(math.cos(angle) * (radius + 22))
            y2 = cy + int(math.sin(angle) * (radius + 22))

            pygame.draw.line(
                glow,
                (255, 226, 150, 180),
                (x1, y1),
                (x2, y2),
                2,
            )

        screen.blit(glow, (0, 0))

        image = self.gem_image
        item_title = "Đá chúc phúc tinh linh"
        subtitle = "Đã nhận bảo hộ kháng khí độc"

        if image is not None:
            display_size = int(300 + pulse * 12)
            display = scale_keep_ratio(
                image, (display_size, display_size)
            )

            rect = display.get_rect(center=(cx, cy))
            screen.blit(display, rect)
        else:
            points = [
                (cx, cy - 100),
                (cx + 65, cy - 40),
                (cx + 50, cy + 45),
                (cx, cy + 85),
                (cx - 50, cy + 45),
                (cx - 65, cy - 40),
            ]

            pygame.draw.polygon(
                screen, (75, 205, 170), points
            )
            pygame.draw.polygon(
                screen, (230, 245, 190), points, 3
            )

        self._text(
            screen, item_title, self.heading, GOLD,
            (cx, cy + 185),
        )

        self._text(
            screen, subtitle, self.font, WHITE,
            (cx, cy + 225),
        )

        self._text(
            screen,
            "Click để tiếp tục",
            self.small,
            WHITE,
            (self.w // 2, self.h - 35),
        )

    def _start_item_reveal(self, kind):
        if kind == "gem" and not self.has_dragon_scale:
            return

        self.item_reveal_kind = kind
        self.item_reveal_time = 0.0
        self.reveal_return_scene = "dialog"

        self.scene = "gem_reveal"

        if kind == "gem":
            self._grant_blessing()

    # =====================================================
    # CHUYỂN HỘI THOẠI
    # =====================================================

    def _next(self):
        if self.scene == "approach":
            self.scene = "intro_dialog"
            self.dialog_index = 0
            self.char_progress = 0.0

        elif self.scene == "intro_dialog":
            if not (0 <= self.dialog_index < len(self.intro_dialogs)):
                self.scene = "puzzle_intro"
                return

            line = self.intro_dialogs[self.dialog_index][1]

            if self.char_progress < len(line):
                self.char_progress = len(line)
                return

            self.dialog_index += 1
            self.char_progress = 0.0

            if self.dialog_index == 2:
                self.scene = "echo"
                self.echo_time = 0.0

            elif self.dialog_index >= len(self.intro_dialogs):
                self.scene = "puzzle_intro"

        elif self.scene == "echo":
            self.scene = "intro_dialog"
            self.dialog_index = 2
            self.char_progress = 0.0

        elif self.scene == "puzzle_intro":
            self.puzzle = TangramGame(
                self.game.screen,
                HOUSE,
                self.w,
                self.h,
            )

            self.puzzle_done_time = 0.0
            self.scene = "puzzle"

        elif self.scene == "spirit_reveal":
            self.scene = "dialog"
            self.dialog_index = 0
            self.char_progress = 0.0

        elif self.scene == "gem_reveal":
            self.gem_revealed = True
            self.scene = self.reveal_return_scene
            self.char_progress = 0.0

        elif self.scene == "dialog":
            if not (0 <= self.dialog_index < len(self.dialogs)):
                self.scene = "ending"
                return

            line = self.dialogs[self.dialog_index][1]

            if self.char_progress < len(line):
                self.char_progress = len(line)
                return

            self.dialog_index += 1
            self.char_progress = 0.0

            if (
                self.has_dragon_scale
                and self.dialog_index == 7
                and not self.gem_revealed
                and not self._has_spirit_gemstone()
            ):
                self._start_item_reveal("gem")
                return

            if self.dialog_index >= len(self.dialogs):
                self.scene = "ending"

        elif self.scene == "ending":
            self.finished = True

            # Chưa có vảy rồng:
            # Giữ nguyên màn hình Forest để người chơi mở bản đồ.
            if not self.has_dragon_scale:
                self._mark_reset_when_reentering()

    # =====================================================
    # INPUT
    # =====================================================

    def handle_event(self, event):
        if self.already_completed:
            return

        if super().handle_event(event):
            return

        if self.scene == "puzzle":
            if self.puzzle is not None:
                self.puzzle.handle_event(event)
            return

        # Khi đã hoàn thành nhánh không có vảy rồng,
        # không cho click làm thay đổi màn hình ending.
        if self.finished and not self.has_dragon_scale:
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._next()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._next()

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self, dt):
        # Trường hợp 5: đã hoàn thành rừng và có đá chúc phúc,
        # quay lại chỉ giữ nền rừng, không phát sinh sự kiện mới.
        if self.already_completed:
            return

        # Nhánh không có vảy rồng:
        # Giữ nguyên màn hình ending, chờ người chơi mở bản đồ.
        if self.finished and not self.has_dragon_scale:
            return

        # Nhánh có vảy rồng:
        # Kết thúc hội thoại thì chuyển sang Đầm Lầy Độc.
        if self.finished and self.has_dragon_scale:
            if not self.transitioned:
                self.transitioned = True
                self.game.change_scene("poison_swamp")

            return

        self.timer += dt

        if self.scene == "approach":
            self._update_walk(dt)
            self.knight_x = min(120, self.knight_x + 90 * dt)

        elif self.scene == "echo":
            self.echo_time += dt

        elif self.scene == "intro_dialog":
            if 0 <= self.dialog_index < len(self.intro_dialogs):
                line = self.intro_dialogs[self.dialog_index][1]

                self.char_progress = min(
                    len(line),
                    self.char_progress + dt * 35,
                )

        elif self.scene == "puzzle" and self.puzzle is not None:
            self.puzzle.update()

            if self.puzzle.completed:
                self.puzzle_done_time += dt

                if self.puzzle_done_time > 1.6:
                    # Kiểm tra túi đồ ngay sau khi hoàn thành puzzle.
                    self._select_story_branch()

                    self.scene = "spirit_reveal"
                    self.timer = 0.0

        elif self.scene == "dialog":
            if 0 <= self.dialog_index < len(self.dialogs):
                line = self.dialogs[self.dialog_index][1]

                self.char_progress = min(
                    len(line),
                    self.char_progress + dt * 35,
                )

        elif self.scene == "gem_reveal":
            self.item_reveal_time += dt

    # =====================================================
    # DRAW
    # =====================================================

    def draw(self, screen):
        if self.scene == "puzzle" and self.puzzle is not None:
            self.puzzle.draw()
            super().draw(screen)
            return

        screen.blit(self.forest, (0, 0))

        if self.already_completed or self.scene == "completed_return":
            super().draw(screen)
            return

        if self.scene == "approach":
            ghost = self.house_bg.copy()

            ghost.set_alpha(
                int(
                    25 + 150 * (
                        0.5 + 0.5 * math.sin(self.timer * 2)
                    )
                )
            )

            screen.blit(ghost, (0, 0))
            self._mist(screen)

            self._draw_knight(
                screen,
                self.knight_x,
                self.h - 245,
            )

            self._dialog(
                screen,
                "Hiệp sĩ",
                "Một ngôi nhà giữa khu rừng...? "
                "Ta phải tiến lại gần xem sao.",
            )

        elif self.scene == "intro_dialog":
            self._mist(screen)

            if 0 <= self.dialog_index < len(self.intro_dialogs):
                speaker, text = self.intro_dialogs[self.dialog_index]

                self._draw_dialog_knight(screen, "left")

                self._dialog(
                    screen,
                    speaker,
                    text[:int(self.char_progress)],
                )

        elif self.scene == "echo":
            self._draw_echo(screen)

        elif self.scene == "puzzle_intro":
            shade = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            shade.fill((10, 23, 15, 145))
            screen.blit(shade, (0, 0))

            self._text(
                screen,
                "Ký ức bị đánh rơi",
                self.heading,
                GOLD,
                (self.w // 2, 90),
            )

            self._text(
                screen,
                "Một bức tranh khu rừng có ngôi nhà nằm trên nền đất.",
                self.font,
                WHITE,
                (self.w // 2, 235),
            )

            self._text(
                screen,
                "Những miếng gỗ vương vãi cạnh một khung gỗ trống.",
                self.font,
                WHITE,
                (self.w // 2, 275),
            )

            self._text(
                screen,
                "Hãy ghép các mảnh lại để khôi phục bức tranh.",
                self.font,
                WHITE,
                (self.w // 2, 315),
            )

            self._text(
                screen,
                "Click để bắt đầu",
                self.small,
                GOLD,
                (self.w // 2, self.h - 45),
            )

        elif self.scene == "spirit_reveal":
            glow = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            glow.fill((28, 54, 30, 80))
            screen.blit(glow, (0, 0))

            center = (self.w // 2, self.h // 2 - 55)
            ring_layer = pygame.Surface(
                self.screen_size, pygame.SRCALPHA
            )

            for i in range(5):
                phase = (self.timer * 110 + i * 65) % 190
                radius = int(40 + phase)
                alpha = max(0, int(100 * (1 - phase / 190)))

                pygame.draw.circle(
                    ring_layer,
                    (218, 245, 137, alpha),
                    center,
                    radius,
                    2,
                )

            screen.blit(ring_layer, (0, 0))

            self._spirit(
                screen,
                "surprised",
                center,
                (300, 350),
            )

            self._text(
                screen,
                "Một tinh linh hiện ra giữa ánh sáng!",
                self.heading,
                GOLD,
                (self.w // 2, 55),
            )

            self._text(
                screen,
                "Click để đối thoại",
                self.small,
                WHITE,
                (self.w // 2, self.h - 35),
            )

        elif self.scene == "dialog":
            if not (0 <= self.dialog_index < len(self.dialogs)):
                self.scene = "ending"
                self.draw(screen)
                return

            shade = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            shade.fill((0, 0, 0, 45))
            screen.blit(shade, (0, 0))

            speaker, text, expression = self.dialogs[self.dialog_index]

            spirit_center = (
                self.w - 260,
                self.h // 2 - 125
            )

            self._spirit(
                screen,
                expression,
                spirit_center,
                (310, 360),
            )

            self._draw_dialog_knight(screen, "left")

            self._dialog(
                screen,
                speaker,
                text[:int(self.char_progress)],
            )

        elif self.scene == "gem_reveal":
            self._draw_item_reveal(screen, "gem")

        elif self.scene == "ending":
            shade = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            shade.fill((5, 15, 10, 150))
            screen.blit(shade, (0, 0))

            self._draw_idle_knight(
                screen,
                (self.w // 2, self.h - 170),
            )

            if self.has_dragon_scale:
                ending_title = "Đá chúc phúc tinh linh"
                ending_text = "Bạn đã nhận được đá chúc phúc tinh linh."
            else:
                ending_title = "Lối về thị trấn"
                ending_text = (
                    "Tinh linh đã chỉ cho bạn con đường "
                    "qua suối và xuyên qua cánh rừng."
                )

            self._text(
                screen,
                ending_title,
                self.heading,
                GOLD,
                (self.w // 2, 80),
            )

            self._text(
                screen,
                ending_text,
                self.font,
                WHITE,
                (self.w // 2, self.h - 130),
            )

            if self.has_dragon_scale:
                ending_destination = "Tiếp tục đến Đầm Lầy Độc"
            else:
                ending_destination = "Mở bản đồ để quay về Hoàng cung"

            self._text(
                screen,
                ending_destination,
                self.font,
                GOLD,
                (self.w // 2, self.h - 90),
            )

            if self.has_dragon_scale:
                instruction = "Click để tiếp tục"
            else:
                instruction = "Mở bản đồ để chọn địa điểm"

            self._text(
                screen,
                instruction,
                self.small,
                WHITE,
                (self.w // 2, self.h - 40),
            )

        super().draw(screen)

    # =====================================================
    # SCENE CONTROL
    # =====================================================

    def is_finished(self):
        return self.finished

    def reset(self):
        """
        Reset riêng ForestScene.
        Không xóa inventory hoặc dữ liệu game_state.
        """
        self.__init__(self.game)

    def get_next_scene(self):
        if not self.finished:
            return None

        if self.has_dragon_scale:
            return "poison_swamp"

        # Không tự chuyển về princess_room.
        # Người chơi sẽ mở bản đồ và tự chọn Hoàng cung.
        return None


def create_forest_scene(game):
    return ForestScene(game)