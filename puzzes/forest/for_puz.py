
import pygame
import random
import math


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    j = len(polygon) - 1

    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        if (yi > y) != (yj > y):
            intersect_x = (xj - xi) * (y - yj) / (yi - yj) + xi
            if x < intersect_x:
                inside = not inside
        j = i

    return inside



class Piece:
    def __init__(self, points, target_x, target_y, house_texture,
                 board_size, screen_width, screen_height):
        self.min_px = min(p[0] for p in points)
        self.min_py = min(p[1] for p in points)
        self.max_px = max(p[0] for p in points)
        self.max_py = max(p[1] for p in points)

        self.original_points = [
            (x - self.min_px, y - self.min_py)
            for x, y in points
        ]

        self.width = self.max_px - self.min_px + 1
        self.height = self.max_py - self.min_py + 1

        self.target_x = target_x + self.min_px
        self.target_y = target_y + self.min_py

        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        self.correct = False
        self.alpha = 255

        size = (self.width + 2, self.height + 2)

        self.wood_surface = pygame.Surface(
            size, pygame.SRCALPHA
        )
        self.house_surface = pygame.Surface(
            size, pygame.SRCALPHA
        )

        mask = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.polygon(
            mask, (255, 255, 255, 255),
            self.original_points
        )

        # Bề mặt gỗ cho mảnh ghép ở ngoài khay.
        pygame.draw.polygon(
            self.wood_surface,
            (139, 88, 43, 255),
            self.original_points
        )

        # Vân gỗ.
        for y in range(5, self.height, 12):
            pygame.draw.line(
                self.wood_surface,
                (100, 59, 30, 180),
                (0, y),
                (self.width, y - 3),
                2
            )

        # Chỉ giữ phần vân nằm bên trong mảnh.
        self.wood_surface.blit(
            mask, (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT
        )

        pygame.draw.polygon(
            self.wood_surface,
            (75, 43, 22, 255),
            self.original_points,
            3
        )

        # Cắt đúng vùng ảnh ngôi nhà tương ứng với mảnh.
        crop = pygame.Surface(size, pygame.SRCALPHA)
        crop.blit(
            house_texture,
            (-self.min_px, -self.min_py)
        )
        crop.blit(
            mask, (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT
        )

        self.house_surface.blit(crop, (0, 0))

        pygame.draw.polygon(
            self.house_surface,
            (255, 215, 0, 255),
            self.original_points,
            2
        )

        self.randomize_position(screen_width, screen_height)

    def randomize_position(self, screen_width, screen_height):
        margin = 20
        tray_left = (screen_width - 400) // 2 - 20
        tray_right = (screen_width + 400) // 2 + 20

        left_space = tray_left - margin
        right_space = screen_width - margin - tray_right

        if left_space >= self.width and right_space >= self.width:
            side = random.choice(["left", "right"])
        elif left_space >= self.width:
            side = "left"
        else:
            side = "right"

        if side == "left":
            min_x = margin
            max_x = tray_left - self.width
        else:
            min_x = tray_right
            max_x = screen_width - margin - self.width

        self.x = random.randint(min_x, max(min_x, max_x))
        self.y = random.randint(
            margin,
            max(margin, screen_height - self.height - margin)
        )

    def get_points(self):
        return [
            (self.x + px, self.y + py)
            for px, py in self.original_points
        ]

    def contains(self, pos):
        return point_in_polygon(pos, self.get_points())

    def draw(self, surface):
        if self.alpha <= 0:
            return

        # Ngoài khay: gỗ.
        # Đặt đúng vị trí: hiện ảnh ngôi nhà.
        current_surface = (
            self.house_surface if self.correct
            else self.wood_surface
        )

        if self.alpha < 255:
            temp = current_surface.copy()
            temp.fill(
                (255, 255, 255, self.alpha),
                special_flags=pygame.BLEND_RGBA_MULT
            )
            surface.blit(temp, (self.x, self.y))
        else:
            surface.blit(current_surface, (self.x, self.y))

    def update_snap(self):
        distance = math.hypot(
            self.x - self.target_x,
            self.y - self.target_y
        )

        if distance < 40:
            self.x = self.target_x
            self.y = self.target_y
            self.correct = True
            return True

        return False



class TangramGame:
    def __init__(
        self,
        screen,
        image_path= "assets/images/sence_2/793802490_29353841374216909_1805474976622337015_n.png",
        width=1600,
        height=900
    ):
        self.screen = screen
        self.WIDTH = width
        self.HEIGHT = height
        self.clock = pygame.time.Clock()

        self.BOARD_SIZE = 400
        self.BOARD_X = (self.WIDTH - self.BOARD_SIZE) // 2
        self.BOARD_Y = (self.HEIGHT - self.BOARD_SIZE) // 2

        self.font = pygame.font.Font(None, 46)
        self.small_font = pygame.font.Font(None, 32)

        self.image_path = image_path
        self.load_and_process_assets()

        self.dark = pygame.Surface(
            (self.WIDTH, self.HEIGHT)
        )
        self.dark.set_alpha(70)
        self.dark.fill((0, 0, 0))

        self.flash_surface = pygame.Surface(
            (self.WIDTH, self.HEIGHT)
        )
        self.flash_surface.fill((255, 255, 255))
        self.flash_alpha = 0

        self.pieces = []
        self.init_pieces()

        self.selected_piece = None
        self.completed = False
        self.fade_started = False
        self.fade_alpha = 255

    def load_and_process_assets(self):
        # Ảnh gốc có ngôi nhà.
        self.bg_with_house = pygame.transform.smoothscale(
            pygame.image.load(self.image_path).convert(),
            (self.WIDTH, self.HEIGHT)
        )

        # Ảnh nền cây cổ thụ KHÔNG có ngôi nhà.
        # Hãy đặt ảnh nền sạch tại đường dẫn này.
        self.bg_no_house_path = (
            "assets/images/sence_2/forest_no_house.png"
        )

        self.bg_no_house = pygame.transform.smoothscale(
            pygame.image.load(self.bg_no_house_path).convert(),
            (self.WIDTH, self.HEIGHT)
        )

        # Cắt vùng ngôi nhà từ ảnh gốc làm ảnh cho các mảnh ghép.
        crop_x = int(self.WIDTH * 0.58)
        crop_y = int(self.HEIGHT * 0.10)
        crop_w = int(self.WIDTH * 0.28)
        crop_h = int(self.HEIGHT * 0.45)

        house_crop = self.bg_with_house.subsurface(
            pygame.Rect(crop_x, crop_y, crop_w, crop_h)
        ).copy()

        self.house_texture = pygame.transform.smoothscale(
            house_crop,
            (self.BOARD_SIZE, self.BOARD_SIZE)
        )

    def init_pieces(self):
        S = self.BOARD_SIZE
        BX, BY = self.BOARD_X, self.BOARD_Y

        pieces_data = [
            [(0, 0), (S // 2, S // 2), (0, S)],
            [(0, S), (S // 2, S // 2), (S, S)],
            [(S // 2, 0), (S, 0), (S, S // 2)],
            [(S // 4, S // 4), (S // 2, S // 2),
             (S * 3 // 4, S // 4)],
            [(S * 3 // 4, S * 3 // 4),
             (S, S // 2), (S, S)],
            [(S // 2, S // 2), (S * 3 // 4, S // 4),
             (S, S // 2), (S * 3 // 4, S * 3 // 4)],
            [(0, 0), (S // 2, 0),
             (S * 3 // 4, S // 4), (S // 4, S // 4)]
        ]

        self.pieces = [
            Piece(
                pts, BX, BY,
                self.house_texture,
                self.BOARD_SIZE,
                self.WIDTH,
                self.HEIGHT
            )
            for pts in pieces_data
        ]

    def reset(self):
        self.completed = False
        self.fade_started = False
        self.fade_alpha = 255
        self.flash_alpha = 0
        self.selected_piece = None

        for piece in self.pieces:
            piece.correct = False
            piece.alpha = 255
            piece.randomize_position(
                self.WIDTH, self.HEIGHT
            )

    def handle_event(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and not self.completed
        ):
            mouse = event.pos

            for piece in reversed(self.pieces):
                if not piece.correct and piece.contains(mouse):
                    self.selected_piece = piece
                    piece.dragging = True
                    piece.offset_x = mouse[0] - piece.x
                    piece.offset_y = mouse[1] - piece.y

                    self.pieces.remove(piece)
                    self.pieces.append(piece)
                    break

        elif (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
        ):
            if self.selected_piece is not None:
                self.selected_piece.dragging = False
                self.selected_piece.update_snap()
                self.selected_piece = None

        # elif (
        #     event.type == pygame.KEYDOWN
        #     and event.key == pygame.K_r
        # ):
        #     self.reset()

    def update(self):
        if self.selected_piece is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            self.selected_piece.x = mouse_x - self.selected_piece.offset_x
            self.selected_piece.y = mouse_y - self.selected_piece.offset_y

            # Giữ mảnh ghép nằm trọn trong màn hình khi kéo.
            self.selected_piece.x = max(
                0,
                min(
                    self.selected_piece.x,
                    self.WIDTH - self.selected_piece.width
                )
            )

            self.selected_piece.y = max(
                0,
                min(
                    self.selected_piece.y,
                    self.HEIGHT - self.selected_piece.height
                )
            )

        if not self.completed:
            self.completed = all(
                piece.correct for piece in self.pieces
            )

            if self.completed:
                self.fade_started = True
                self.flash_alpha = 255

        if self.fade_started:
            self.fade_alpha = max(0, self.fade_alpha - 5)

            for piece in self.pieces:
                piece.alpha = self.fade_alpha

            if self.flash_alpha > 0:
                self.flash_alpha = max(
                    0, self.flash_alpha - 6
                )

    def draw(self):
        # if self.completed and self.flash_alpha < 180:
        #     self.screen.blit(self.bg_with_house, (0, 0))
        # else:
        #     self.screen.blit(self.bg_no_house, (0, 0))
        #
        #     if not self.completed:
        #         self.screen.blit(self.dark, (0, 0))
        if self.completed and self.flash_alpha < 180:
            self.screen.blit(self.bg_with_house, (0, 0))
        else:
            self.screen.blit(self.bg_no_house, (0, 0))
            if not self.completed:
                self.screen.blit(self.dark, (0, 0))
        if self.fade_alpha > 0:
            margin = 16
            tray_w = self.BOARD_SIZE + margin * 2
            tray_h = self.BOARD_SIZE + margin * 2
            tray_x = self.BOARD_X - margin
            tray_y = self.BOARD_Y - margin

            tray_surface = pygame.Surface(
                (tray_w, tray_h), pygame.SRCALPHA
            )

            pygame.draw.rect(
                tray_surface,
                (120, 80, 45, self.fade_alpha),
                (0, 0, tray_w, tray_h),
                border_radius=12
            )

            pygame.draw.rect(
                tray_surface,
                (60, 40, 20, self.fade_alpha),
                (0, 0, tray_w, tray_h),
                4,
                border_radius=12
            )

            pygame.draw.rect(
                tray_surface,
                (30, 20, 10, self.fade_alpha),
                (margin, margin, self.BOARD_SIZE, self.BOARD_SIZE)
            )

            self.screen.blit(tray_surface, (tray_x, tray_y))

        if self.fade_alpha > 0:
            for piece in self.pieces:
                piece.draw(self.screen)

        if self.flash_alpha > 0:
            self.flash_surface.set_alpha(self.flash_alpha)
            self.screen.blit(self.flash_surface, (0, 0))

        if not self.completed:
            count = sum(
                piece.correct for piece in self.pieces
            )

            progress = self.small_font.render(
                f"Tiến độ: {count}/{len(self.pieces)}",
                True,
                (255, 255, 255)
            )

            self.screen.blit(progress, (25, 25))

        if (
            self.completed
            and self.fade_alpha == 0
            and self.flash_alpha == 0
        ):
            text_surface = self.font.render(
                "HOÀN THÀNH!", True, (255, 255, 255)
            )

            box = pygame.Surface(
                (
                    text_surface.get_width() + 60,
                    text_surface.get_height() + 30
                ),
                pygame.SRCALPHA
            )

            box.fill((0, 0, 0, 150))

            box_x = self.WIDTH // 2 - box.get_width() // 2
            self.screen.blit(box, (box_x, 35))

            self.screen.blit(
                text_surface,
                (
                    self.WIDTH // 2 - text_surface.get_width() // 2,
                    50
                )
            )

            # reset_text = self.small_font.render(
            #     "Nhấn R để chơi lại",
            #     True,
            #     (255, 255, 255)
            # )
            #
            # self.screen.blit(
            #     reset_text,
            #     (
            #         self.WIDTH // 2 - reset_text.get_width() // 2,
            #         110
            #     )
            # )

    def run_frame(self, events):
        for event in events:
            self.handle_event(event)

        self.update()
        self.draw()


def forest_puzzle():
    pygame.init()

    WIDTH, HEIGHT = 1280, 700

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("House Tangram Puzzle")

    game = TangramGame(
        screen,
        "assets/images/sence_2/793802490_29353841374216909_1805474976622337015_n.png",
        WIDTH,
        HEIGHT
    )

    running = True

    while running:
        game.clock.tick(60)
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

        game.run_frame(events)
        pygame.display.flip()

    pygame.quit()