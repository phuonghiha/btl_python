import math
import os
import random
import sys
import pygame

pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

WIDTH, HEIGHT = 1280, 720
FPS = 60
TITLE = "Rừng tinh linh"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCENE_DIR = os.path.join(BASE_DIR, "assets", "images", "sence_2")
HOUSE_PATH = os.path.join(
    SCENE_DIR, "793802490_29353841374216909_1805474976622337015_n.png"
)
NO_HOUSE_PATH = os.path.join(SCENE_DIR, "forest_no_house.png")

WHITE = (250, 248, 224)
INK = (38, 48, 31)
DARK = (15, 28, 18)
GREEN = (42, 82, 45)
GOLD = (242, 205, 104)
WOOD = (115, 72, 38)
WOOD_LIGHT = (197, 151, 91)
CREAM = (245, 229, 181)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

def get_font(size, bold=False):
    # Swamp scene dùng Arial; giữ cùng kiểu chữ để khung thoại đồng bộ.
    return pygame.font.SysFont("arial", size, bold=bold)

FONT = get_font(25)
SMALL = get_font(19)
TITLE_FONT = get_font(32, True)
PUZZLE_FONT = get_font(22, True)

def load_image(path):
    if not os.path.isfile(path):
        return None
    try:
        return pygame.image.load(path).convert()
    except pygame.error:
        return None

def cover(image, size=(WIDTH, HEIGHT)):
    iw, ih = image.get_size()
    scale = max(size[0] / iw, size[1] / ih)
    scaled = pygame.transform.smoothscale(
        image, (int(iw * scale), int(ih * scale))
    )
    x = (scaled.get_width() - size[0]) // 2
    y = (scaled.get_height() - size[1]) // 2
    return scaled.subsurface((x, y, size[0], size[1])).copy()

house_original = load_image(HOUSE_PATH)
forest_original = load_image(NO_HOUSE_PATH)

if house_original is not None:
    HOUSE_BG = cover(house_original)
else:
    HOUSE_BG = None
if forest_original is not None:
    FOREST_BG = cover(forest_original)
else:
    FOREST_BG = None

def draw_fallback_forest(surface, with_house=False):
    surface.fill((107, 166, 190))
    pygame.draw.rect(surface, (91, 145, 83), (0, 360, WIDTH, 360))
    for i in range(12):
        x = i * 120 - 25
        pygame.draw.rect(surface, (83, 65, 45), (x + 35, 90, 28, 410))
        pygame.draw.circle(surface, (40, 101, 57), (x + 48, 110), 100)
        pygame.draw.circle(surface, (55, 125, 64), (x + 5, 175), 76)
    pygame.draw.polygon(surface, (199, 180, 126),
                        [(0, 610), (330, 460), (670, 520), (1000, 410),
                         (1280, 470), (1280, 720), (0, 720)])
    if with_house:
        pygame.draw.rect(surface, (125, 79, 49), (760, 205, 190, 175))
        pygame.draw.polygon(surface, (71, 52, 45),
                            [(730, 220), (850, 115), (980, 220)])
        pygame.draw.rect(surface, (243, 190, 78), (815, 260, 38, 55))
        pygame.draw.rect(surface, (243, 190, 78), (875, 260, 38, 55))

if HOUSE_BG is None:
    HOUSE_BG = pygame.Surface((WIDTH, HEIGHT))
    draw_fallback_forest(HOUSE_BG, True)
if FOREST_BG is None:
    FOREST_BG = pygame.Surface((WIDTH, HEIGHT))
    draw_fallback_forest(FOREST_BG, False)

def draw_text(surface, text, font, color, pos, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(rendered, rect)
    return rect

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = word if not current else current + " " + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def draw_dialog(surface, speaker, text, progress=None):
    # Khung thoại xanh đậm, viền vàng kem theo phong cách fantasy của swamp scene.
    panel = pygame.Surface((WIDTH - 100, 190), pygame.SRCALPHA)
    panel.fill((15, 28, 18, 224))
    pygame.draw.rect(panel, GOLD, panel.get_rect(), 3, border_radius=14)
    pygame.draw.rect(panel, (93, 122, 74), (12, 12, panel.get_width()-24, 42),
                     border_radius=8)
    name = get_font(23, True).render(speaker, True, GOLD)
    panel.blit(name, (28, 18))
    lines = wrap_text(text, FONT, WIDTH - 170)
    visible = text if progress is None else text[:progress]
    lines = wrap_text(visible, FONT, WIDTH - 170)
    for i, line in enumerate(lines[:3]):
        panel.blit(FONT.render(line, True, WHITE), (28, 69 + i * 34))
    screen.blit(panel, (50, HEIGHT - 215))
    draw_text(screen, "ENTER / SPACE / click để tiếp tục", SMALL, WHITE,
              (WIDTH - 365, HEIGHT - 48))

def draw_knight_silhouette(surface, x, y, scale=1.0, alpha=220):
    layer = pygame.Surface((180, 260), pygame.SRCALPHA)
    c = (37, 44, 47, alpha)
    pygame.draw.circle(layer, c, (90, 43), int(27 * scale))
    pygame.draw.rect(layer, c, (63, 70, 54, 90), border_radius=12)
    pygame.draw.polygon(layer, c, [(65, 88), (28, 130), (44, 143), (78, 112)])
    pygame.draw.polygon(layer, c, [(111, 88), (145, 120), (134, 135), (102, 112)])
    pygame.draw.polygon(layer, c, [(67, 155), (55, 235), (77, 235), (91, 165)])
    pygame.draw.polygon(layer, c, [(94, 164), (105, 235), (127, 235), (113, 155)])
    pygame.draw.polygon(layer, (180, 187, 172, alpha),
                        [(72, 36), (85, 25), (103, 36), (101, 49), (77, 49)])
    layer = pygame.transform.smoothscale(layer, (int(180*scale), int(260*scale)))
    surface.blit(layer, (x, y))

def draw_spirit(surface, x, y, expression="curious", scale=1.0):
    """Tinh linh vẽ bằng hình cơ bản để file chạy được ngay cả khi chưa thêm sprite."""
    w, h = int(190 * scale), int(225 * scale)
    layer = pygame.Surface((w, h), pygame.SRCALPHA)
    # Hai chiếc lá trên đầu
    pygame.draw.ellipse(layer, (182, 222, 60), (int(w*.16), 2, int(w*.37), int(h*.27)))
    pygame.draw.ellipse(layer, (137, 204, 53), (int(w*.48), 0, int(w*.34), int(h*.30)))
    pygame.draw.line(layer, (71, 139, 46), (int(w*.34), int(h*.22)),
                     (int(w*.18), int(h*.06)), max(1, int(2*scale)))
    pygame.draw.line(layer, (71, 139, 46), (int(w*.56), int(h*.22)),
                     (int(w*.73), int(h*.06)), max(1, int(2*scale)))
    # Thân tròn, má và lá đuôi
    pygame.draw.ellipse(layer, (119, 197, 94), (int(w*.08), int(h*.19), int(w*.84), int(h*.62)))
    pygame.draw.ellipse(layer, (246, 239, 183), (int(w*.16), int(h*.39), int(w*.68), int(h*.39)))
    pygame.draw.ellipse(layer, (255, 255, 221), (int(w*.38), int(h*.23), int(w*.25), int(h*.16)))
    pygame.draw.ellipse(layer, (255, 179, 139), (int(w*.22), int(h*.54), int(w*.13), int(h*.08)))
    pygame.draw.ellipse(layer, (255, 179, 139), (int(w*.65), int(h*.54), int(w*.13), int(h*.08)))
    if expression in ("angry", "stern"):
        pygame.draw.ellipse(layer, (166, 93, 14), (int(w*.27), int(h*.45), int(w*.16), int(h*.12)))
        pygame.draw.ellipse(layer, (166, 93, 14), (int(w*.58), int(h*.45), int(w*.16), int(h*.12)))
        pygame.draw.line(layer, (68, 68, 39), (int(w*.25), int(h*.44)),
                         (int(w*.43), int(h*.41)), max(2, int(4*scale)))
        pygame.draw.line(layer, (68, 68, 39), (int(w*.57), int(h*.41)),
                         (int(w*.75), int(h*.44)), max(2, int(4*scale)))
        pygame.draw.arc(layer, (104, 66, 41),
                        (int(w*.43), int(h*.61), int(w*.15), int(h*.08)), math.pi, 2*math.pi, 2)
    elif expression == "surprised":
        pygame.draw.circle(layer, (255, 180, 25), (int(w*.35), int(h*.49)), int(10*scale))
        pygame.draw.circle(layer, (255, 180, 25), (int(w*.66), int(h*.49)), int(10*scale))
        pygame.draw.ellipse(layer, (190, 62, 62), (int(w*.47), int(h*.58), int(w*.09), int(h*.12)))
    elif expression == "happy":
        pygame.draw.arc(layer, (153, 94, 18), (int(w*.25), int(h*.43), int(w*.20), int(h*.14)), 0, math.pi, 3)
        pygame.draw.arc(layer, (153, 94, 18), (int(w*.57), int(h*.43), int(w*.20), int(h*.14)), 0, math.pi, 3)
        pygame.draw.arc(layer, (153, 94, 18), (int(w*.40), int(h*.57), int(w*.20), int(h*.12)), math.pi, 2*math.pi, 3)
    else:
        pygame.draw.ellipse(layer, (255, 174, 18), (int(w*.27), int(h*.44), int(w*.17), int(h*.16)))
        pygame.draw.ellipse(layer, (255, 174, 18), (int(w*.57), int(h*.44), int(w*.17), int(h*.16)))
        pygame.draw.circle(layer, WHITE, (int(w*.32), int(h*.47)), max(2, int(4*scale)))
        pygame.draw.circle(layer, WHITE, (int(w*.62), int(h*.47)), max(2, int(4*scale)))
        pygame.draw.circle(layer, (196, 88, 85), (int(w*.51), int(h*.58)), max(2, int(3*scale)))
    # Cuống cong và chiếc lá cuối đuôi
    pygame.draw.arc(layer, (65, 139, 49),
                    (int(w*.36), int(h*.70), int(w*.35), int(h*.43)), 0.2, math.pi, max(4, int(7*scale)))
    pygame.draw.ellipse(layer, (106, 183, 45), (int(w*.48), int(h*.84), int(w*.36), int(h*.15)))
    surface.blit(layer, (x, y))

class EchoRipple:
    """Các vòng âm vang loang ra từ tâm màn hình; chữ cũng được nhân bóng mờ."""
    def __init__(self):
        self.elapsed = 0.0
        self.duration = 4.8
        self.active = True

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False

    def draw(self, surface, text):
        if not self.active:
            return
        center = (WIDTH // 2, HEIGHT // 2 - 20)
        for i in range(5):
            phase = (self.elapsed * 210 + i * 115) % 620
            radius = int(35 + phase)
            alpha = max(0, int(145 * (1 - phase / 620)))
            ring = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (207, 231, 188, alpha),
                                (center[0] - radius, center[1] - radius * .48,
                                 radius * 2, radius * .96), 2)
            surface.blit(ring, (0, 0))
        font = get_font(31, True)
        base = font.render(text, True, (245, 247, 219))
        rect = base.get_rect(center=center)
        for offset in (28, 18, 9):
            ghost = font.render(text, True, (167, 208, 169))
            ghost.set_alpha(max(0, 65 - int(offset * 1.5)))
            surface.blit(ghost, rect.move(0, offset))
        surface.blit(base, rect)

class WoodPuzzle:
    """Puzzle 3x2: kéo 6 mảnh tranh vào đúng ô khung gỗ."""
    COLS, ROWS = 3, 2
    TILE_W, TILE_H = 190, 145

    def __init__(self, image):
        self.image = pygame.transform.smoothscale(
            image, (self.COLS * self.TILE_W, self.ROWS * self.TILE_H)
        )
        self.frame = pygame.Rect(180, 170, self.COLS*self.TILE_W, self.ROWS*self.TILE_H)
        self.tiles = []
        self.dragging = None
        self.offset = (0, 0)
        self.completed = False
        self._make_tiles()

    def _make_tiles(self):
        self.tiles.clear()
        positions = [(40, 180), (80, 390), (430, 470), (850, 160), (900, 420), (560, 470)]
        order = list(range(self.COLS * self.ROWS))
        random.shuffle(order)
        for index in range(self.COLS * self.ROWS):
            col, row = index % self.COLS, index // self.COLS
            source = pygame.Rect(col*self.TILE_W, row*self.TILE_H, self.TILE_W, self.TILE_H)
            tile_image = self.image.subsurface(source).copy()
            self.tiles.append({
                "index": index, "image": tile_image,
                "rect": pygame.Rect(positions[index], (self.TILE_W, self.TILE_H)),
                "placed": False, "correct": False
            })
        # Mỗi mảnh bắt đầu ở một vị trí rời rạc, không theo thứ tự khung.
        random.shuffle(self.tiles)
        for tile, pos in zip(self.tiles, positions):
            tile["rect"].topleft = pos
            tile["placed"] = False
            tile["correct"] = False

    def handle_event(self, event):
        if self.completed:
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self._make_tiles()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for tile in reversed(self.tiles):
                if tile["rect"].collidepoint(event.pos):
                    self.dragging = tile
                    self.offset = (event.pos[0] - tile["rect"].x,
                                   event.pos[1] - tile["rect"].y)
                    self.tiles.remove(tile)
                    self.tiles.append(tile)
                    break
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.dragging["rect"].x = event.pos[0] - self.offset[0]
            self.dragging["rect"].y = event.pos[1] - self.offset[1]
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            tile = self.dragging
            self.dragging = None
            idx = tile["index"]
            col, row = idx % self.COLS, idx // self.COLS
            target = pygame.Rect(self.frame.x + col*self.TILE_W,
                                 self.frame.y + row*self.TILE_H,
                                 self.TILE_W, self.TILE_H)
            if target.inflate(45, 45).collidepoint(tile["rect"].center):
                tile["rect"] = target
                tile["placed"] = True
                tile["correct"] = True
            else:
                tile["placed"] = False
                tile["correct"] = False
            self.completed = all(t["correct"] for t in self.tiles)

    def draw(self, surface):
        # Lớp nền bảng gỗ.
        board = pygame.Rect(160, 150, self.frame.width + 40, self.frame.height + 40)
        pygame.draw.rect(surface, (72, 48, 31), board, border_radius=12)
        pygame.draw.rect(surface, (184, 132, 75), board, 7, border_radius=12)
        for row in range(self.ROWS):
            for col in range(self.COLS):
                cell = pygame.Rect(self.frame.x + col*self.TILE_W,
                                   self.frame.y + row*self.TILE_H,
                                   self.TILE_W, self.TILE_H)
                pygame.draw.rect(surface, (51, 59, 38), cell)
                pygame.draw.rect(surface, (207, 168, 111), cell, 3)
        for tile in self.tiles:
            surface.blit(tile["image"], tile["rect"])
            pygame.draw.rect(surface, (228, 196, 132), tile["rect"], 4)
            pygame.draw.line(surface, (95, 60, 35),
                             tile["rect"].topleft,
                             (tile["rect"].right, tile["rect"].top), 2)
        draw_text(surface, "GHÉP TRANH NGÔI NHÀ", TITLE_FONT, GOLD, (WIDTH//2, 48), True)
        draw_text(surface, "Kéo từng miếng gỗ vào ô tương ứng trong khung. Nhấn R để xáo lại.",
                  SMALL, WHITE, (WIDTH//2, 94), True)
        draw_text(surface, f"Đã ghép: {sum(1 for t in self.tiles if t['correct'])}/6",
                  SMALL, WHITE, (WIDTH//2, 126), True)

class StoryGame:
    def __init__(self):
        self.scene = "approach"
        self.timer = 0.0
        self.house_alpha = 0
        self.house_direction = 1
        self.dialog_index = 0
        self.char_progress = 0.0
        self.ripple = EchoRipple()
        self.spirit_expression = "curious"
        self.spirit_image = None
        self.puzzle = WoodPuzzle(HOUSE_BG)
        self.dialogs = [
            ("Tinh linh", "Ồ... cuối cùng cũng có kẻ tìm được lối vào khu rừng này.", "curious"),
            ("Hiệp sĩ", "Ngươi là ai? Ta vừa thấy một ngôi nhà ở đây, nhưng nó đã biến mất.", "surprised"),
            ("Tinh linh", "Ngôi nhà không biến mất. Ngươi chỉ chưa chứng minh được rằng mình nhìn thấy điều cần nhìn.", "stern"),
            ("Tinh linh", "Ngươi đã ghép lại ký ức của khu rừng. Ta công nhận trí tuệ của ngươi.", "happy"),
            ("Hiệp sĩ", "Vậy hãy nói cho ta biết: làm thế nào để đạt được điều ta mong muốn?", "curious"),
            ("Tinh linh", "Hãy nói điều ngươi tìm kiếm, hiệp sĩ. Nếu điều đó nằm trong quyền năng của ta, ta sẽ giúp.", "happy"),
        ]

    def handle_event(self, event):
        if self.scene == "puzzle":
            self.puzzle.handle_event(event)
            if self.puzzle.completed:
                self.scene = "spirit_reveal"
                self.timer = 0
            return
        if event.type not in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            return
        advance = (
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        ) or (
            event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE)
        )
        if not advance:
            return
        if self.scene == "approach":
            self.scene = "echo"
            self.timer = 0
            self.ripple = EchoRipple()
        elif self.scene == "echo":
            self.scene = "puzzle_intro"
        elif self.scene == "puzzle_intro":
            self.scene = "puzzle"
        elif self.scene == "spirit_reveal":
            self.scene = "dialog"
            self.dialog_index = 0
            self.char_progress = 0
        elif self.scene == "dialog":
            full_text = self.dialogs[self.dialog_index][1]
            if self.char_progress < len(full_text):
                self.char_progress = len(full_text)
            else:
                self.dialog_index += 1
                if self.dialog_index >= len(self.dialogs):
                    self.scene = "ending"
                else:
                    self.char_progress = 0
                    self.spirit_expression = self.dialogs[self.dialog_index][2]
        elif self.scene == "ending":
            self.scene = "approach"
            self.timer = 0
            self.dialog_index = 0
            self.char_progress = 0
            self.puzzle = WoodPuzzle(HOUSE_BG)

    def update(self, dt):
        self.timer += dt
        if self.scene == "approach":
            # Ngôi nhà hiện lên qua sương, rồi mờ dần khi hiệp sĩ đến gần.
            self.house_alpha = int(150 + 105 * (0.5 + 0.5 * math.sin(self.timer * 2.3)))
            self.house_direction = 1
        elif self.scene == "echo":
            self.ripple.update(dt)
        elif self.scene == "spirit_reveal":
            self.spirit_expression = "surprised" if self.timer < 1.1 else "curious"
        elif self.scene == "dialog":
            text = self.dialogs[self.dialog_index][1]
            self.char_progress = min(len(text), self.char_progress + dt * 42)

    def draw(self):
        if self.scene == "approach":
            screen.blit(FOREST_BG, (0, 0))
            # Chồng ảnh ngôi nhà với alpha dao động để tạo cảm giác thấp thoáng.
            ghost = HOUSE_BG.copy()
            ghost.set_alpha(self.house_alpha)
            screen.blit(ghost, (0, 0))
            # Sương trôi ngang.
            mist = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for i in range(8):
                x = int((self.timer * (24 + i*4) + i*190) % (WIDTH + 240)) - 120
                y = 140 + i*65
                pygame.draw.ellipse(mist, (235, 243, 218, 24),
                                    (x, y, 260, 55))
            screen.blit(mist, (0, 0))
            draw_knight_silhouette(screen, 145, 370, 1.0, 220)
            draw_text(screen, "RỪNG TINH LINH", TITLE_FONT, GOLD, (WIDTH//2, 42), True)
            draw_dialog(screen, "Hiệp sĩ", "Một ngôi nhà...? Mình chưa từng thấy nó trên bản đồ.", len(
                "Một ngôi nhà...? Mình chưa từng thấy nó trên bản đồ."
            ) if self.timer > 2 else int(self.timer * 26))
        elif self.scene == "echo":
            screen.blit(FOREST_BG, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((8, 20, 15, 110))
            screen.blit(overlay, (0, 0))
            self.ripple.draw(screen, "KẺ XÂM NHẬP TỪ ĐÂU ĐẾN?")
            if self.ripple.elapsed > 0.5:
                draw_text(screen, "Nếu ngươi có bản lĩnh, hãy chứng minh trí tuệ của ngươi...",
                          FONT, WHITE, (WIDTH//2, HEIGHT-155), True)
            if self.ripple.elapsed > 2.1:
                draw_text(screen, "Khiến cho ta công nhận, và ta sẽ thực hiện yêu cầu của ngươi...",
                          SMALL, CREAM, (WIDTH//2, HEIGHT-120), True)
            draw_text(screen, "Tiếng vọng lan qua khu rừng...", SMALL, GOLD,
                      (WIDTH//2, 45), True)
            draw_text(screen, "ENTER / SPACE / click để tìm hiểu", SMALL, WHITE,
                      (WIDTH//2, HEIGHT-45), True)
        elif self.scene == "puzzle_intro":
            screen.blit(FOREST_BG, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((12, 25, 16, 125))
            screen.blit(overlay, (0, 0))
            draw_text(screen, "KÝ ỨC BỊ ĐÁNH RƠI", TITLE_FONT, GOLD,
                      (WIDTH//2, 70), True)
            draw_text(screen, "Trên nền đất là bức tranh khu rừng, những miếng gỗ vương vãi",
                      FONT, WHITE, (WIDTH//2, 285), True)
            draw_text(screen, "và một khung gỗ trống. Hãy xếp lại bức tranh ngôi nhà.",
                      FONT, WHITE, (WIDTH//2, 330), True)
            draw_text(screen, "ENTER / SPACE / click để bắt đầu", SMALL, WHITE,
                      (WIDTH//2, HEIGHT-70), True)
        elif self.scene == "puzzle":
            screen.blit(FOREST_BG, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((7, 20, 13, 145))
            screen.blit(overlay, (0, 0))
            self.puzzle.draw(screen)
        elif self.scene == "spirit_reveal":
            screen.blit(FOREST_BG, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((28, 54, 30, 100))
            screen.blit(overlay, (0, 0))
            # Hào quang xuất hiện thành nhiều vòng sáng.
            for i in range(5):
                radius = int(55 + ((self.timer * 100 + i*70) % 190))
                glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                alpha = max(0, 110 - radius//2)
                pygame.draw.circle(glow, (218, 245, 137, alpha),
                                   (WIDTH//2, 320), radius, 3)
                screen.blit(glow, (0, 0))
            draw_spirit(screen, WIDTH//2-95, 165, self.spirit_expression, 1.0)
            draw_text(screen, "Một tinh linh lá cây hiện ra giữa ánh sáng!", TITLE_FONT,
                      GOLD, (WIDTH//2, 65), True)
            draw_text(screen, "ENTER / SPACE / click để đối thoại", SMALL, WHITE,
                      (WIDTH//2, HEIGHT-65), True)
        elif self.scene == "dialog":
            screen.blit(FOREST_BG, (0, 0))
            # Làm nền dịu đi để nhân vật và khung thoại nổi bật.
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 25, 14, 85))
            screen.blit(overlay, (0, 0))
            speaker, text, expression = self.dialogs[self.dialog_index]
            draw_spirit(screen, 110, 135, expression, 1.15)
            draw_knight_silhouette(screen, 850, 310, .72, 230)
            shown = text[:int(self.char_progress)]
            draw_dialog(screen, speaker, shown)
            if self.char_progress >= len(text):
                draw_text(screen, "▼", SMALL, GOLD, (WIDTH-83, HEIGHT-43), True)
        elif self.scene == "ending":
            screen.blit(FOREST_BG, (0, 0))
            draw_spirit(screen, WIDTH//2-95, 135, "happy", 1.0)
            draw_dialog(screen, "Tinh linh", "Cuộc gặp gỡ mới chỉ bắt đầu. Hãy tiếp tục hành trình của ngươi.")
            draw_text(screen, "ENTER để xem lại phân cảnh", SMALL, WHITE,
                      (WIDTH//2, HEIGHT-18), True)

def main():
    game = StoryGame()
    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                game.handle_event(event)
        game.update(dt)
        game.draw()
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
