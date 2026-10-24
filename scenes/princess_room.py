"""Point-and-click quest scene in the princess's room."""

from dataclasses import dataclass
import os

import pygame

from game_fonts import content1, title
from animation.animation_manager import AnimationManager
from characters.knight import Knight
from base_scene import BaseScene, STANDARD_DIALOG_RECT, draw_dialogue_frame
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
BG_PATH = os.path.join(ASSETS, "images", "sence_1", "background.png")
SCENE_ASSETS = os.path.join(ASSETS, "images", "sence_1")
ZOOM_FACTOR = 5
KNIGHT_DRAW_SIZE = (300, 414)
# The room floor starts below the bed, bedding, and the balcony sky area.
WALKABLE_FLOOR = pygame.Rect(0, 520, SCREEN_WIDTH, SCREEN_HEIGHT - 520)
BED_EDGE_X = 610
BED_CLEARANCE_Y = 630
CAT_DRAW_SIZE = (129, 129)
MAGNIFIER_SIZE = (54, 54)


@dataclass
class PrincessRoomState:
    intro_shown: bool = False
    cat_questioned: bool = False
    puzzle_solved: bool = False
    chest_opened: bool = False
    pink_yarn_collected: bool = False
    cat_moved: bool = False
    letter_revealed: bool = False
    letter_read: bool = False
    magnifier_collected: bool = False
    magnifier_active: bool = False
    dragon_scale_found: bool = False
    dragon_scale_collected: bool = False
    princess_room_completed: bool = False


class PrincessRoomScene(BaseScene):
    """Room exploration, vintage dialogue, inventory and the dragon clue."""

    def __init__(self, game):
        super().__init__(game)
        self.state = PrincessRoomState()
        self.background = self._load_background()
        try:
            self.knight = Knight(SCREEN_WIDTH // 2 - KNIGHT_DRAW_SIZE[0] // 2, 550 - KNIGHT_DRAW_SIZE[1])
        except (pygame.error, OSError, FileNotFoundError):
            self.knight = None
        self.knight_waypoints = []
        self.pending_chest_click = None
        self.chest_closed_image = self._load_prop("chest_closed.png")
        self.chest_open_image = self._load_prop("chest_open.png")
        self.yarn_image = self._load_prop("Yarn_ball.png")
        self.letter_image = self._load_prop("Letter.png")
        self.scale_image = self._load_prop("Dragon_scale.png")
        self.magnifier_image = self._load_prop("magnifying glass.png")
        self.magnifier_icon = self._scaled(self.magnifier_image, MAGNIFIER_SIZE)
        self.chest_closed_scaled = self._scaled(self.chest_closed_image, (78, 64))
        self.chest_open_scaled = self._scaled(self.chest_open_image, (78, 64))
        self.yarn_icon = self._scaled(self.yarn_image, (50, 50))
        self.letter_item_icon = self._scaled(self.letter_image, (64, 38))
        self.letter_panel_image = self._scaled(self.letter_image, (760, 370))
        self.scale_tiny = (
            pygame.transform.smoothscale(self.scale_image, (4, 5))
            if self.scale_image
            else None
        )
        self.cat = self._make_cat()
        self.cat_x = 930.0
        self.cat_y = 595
        self.cat_hitbox = pygame.Rect(0, 0, *CAT_DRAW_SIZE)
        self.cat_hitbox.midbottom = (int(self.cat_x), self.cat_y)
        self.chest_hitbox = pygame.Rect(4, 360, 78, 64)
        self.yarn_hitbox = pygame.Rect(28, 382, 34, 32)
        self.letter_hitbox = pygame.Rect(898, 542, 64, 38)
        self.magnifier_hitbox = pygame.Rect(574, 629, *MAGNIFIER_SIZE)
        self.scale_hitbox = pygame.Rect(900, 425, 12, 10)
        self.lens_radius = 100
        self.lens_rect = pygame.Rect(0, 0, 200, 200)
        self.lens_click_count = 0
        self.lens_last_click_ms = 0
        self.lens_world_center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.puzzle_input_rect = pygame.Rect(0, 0, 0, 0)
        self.puzzle_input_active = False
        self.modal = None
        self.dialogue = ("Hiệp sĩ", "Sao con mèo này lại nằm ở đây","Nó là rất đáng nghi...")
        self.dialog_pages = []
        self.dialog_page = 0
        self.type_progress = 0.0
        self.puzzle_text = ""
        self.puzzle_message = ""
        self.puzzle_cursor_time = 0.0
        self.notice = ""
        self.notice_time = 0.0
        self.mouse_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.font = content1(23)
        self.small = content1(18)
        self.title_font = title(36)
        self.items = {
            "pink_yarn": "Cuộn len hồng",
            "magnifying_glass": "Kính lúp",
            "red_dragon_scale": "Vảy rồng đỏ",
        }
        self.item_images = {
            "pink_yarn": "assets/images/sence_1/Yarn_ball.png",
            "magnifying_glass": "assets/images/sence_1/magnifying glass.png",
            "red_dragon_scale": "assets/images/sence_1/Dragon_scale.png",
        }
        self.close_rect = pygame.Rect(0, 0, 0, 0)
        self.submit_rect = pygame.Rect(0, 0, 0, 0)
        self.after_dialog = None
        self.dialog_style = "standard"
        self._say("Hiệp sĩ", "Con mèo này thật là đáng nghi...", self._mark_intro_shown)

    def _mark_intro_shown(self):
        self.state.intro_shown = True

    @staticmethod
    def _load_prop(filename):
        path = os.path.join(SCENE_ASSETS, filename)
        try:
            return pygame.image.load(path).convert_alpha()
        except (pygame.error, OSError):
            return None

    @staticmethod
    def _scaled(image, size):
        return pygame.transform.smoothscale(image, size) if image else None

    def reset(self):
        self.__init__(self.game)

    @staticmethod
    def _load_background():
        try:
            image = pygame.image.load(BG_PATH).convert()
            iw, ih = image.get_size()
            scale = max(SCREEN_WIDTH / iw, SCREEN_HEIGHT / ih)
            size = int(iw * scale), int(ih * scale)
            image = pygame.transform.smoothscale(image, size)
            left = (size[0] - SCREEN_WIDTH) // 2
            top = (size[1] - SCREEN_HEIGHT) // 2
            return image.subsurface((left, top, SCREEN_WIDTH, SCREEN_HEIGHT)).copy()
        except (pygame.error, OSError):
            image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            image.fill((76, 58, 71))
            pygame.draw.rect(image, (142, 110, 94), (0, 450, SCREEN_WIDTH, 270))
            pygame.draw.rect(image, (35, 66, 108), (700, 100, 390, 370))
            return image

    @staticmethod
    def _make_cat():
        animation = AnimationManager()
        base = os.path.join(ASSETS, "sprites", "cat")
        try:
            animation.load_image("sit", os.path.join(base, "stand_up", "n_1.png"))
            animation.load_folder("stand_up", os.path.join(base, "stand_up"), fps=3, loop=False)
            animation.load_folder("walk", os.path.join(base, "walk"), fps=6, loop=True)
            animation.play("sit")
            return animation
        except (pygame.error, OSError, FileNotFoundError):
            return None

    def _say(self, speaker, text, on_close=None, style="standard"):
        self.modal = "dialog"
        self.dialogue = (speaker, text)
        self.dialog_style = style
        self.dialog_pages = self._wrap(text, self.small if style == "cat" else self.font, 220 if style == "cat" else 780)
        self.dialog_page = 0
        self.type_progress = 0.0
        self.after_dialog = on_close

    @staticmethod
    def _wrap(text, font, width):
        lines, line = [], ""
        for word in text.split():
            candidate = word if not line else line + " " + word
            if font.size(candidate)[0] <= width:
                line = candidate
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines or [""]

    def _notify(self, text):
        self.notice, self.notice_time = text, 2.6

    def _add_item(self, item):
        if self.add_item(item, self.items[item], self.item_images[item]):
            self._notify("Đã nhận được: " + self.items[item])

    def handle_event(self, event):
        if super().handle_event(event):
            self.state.magnifier_active = (
                self.selected_item == "magnifying_glass"
            )
            return
        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
            self._update_lens_mapping()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state.magnifier_active:
                self.state.magnifier_active = False
                self.selected_item = None
                return
            if self.modal:
                if self.modal == "puzzle":
                    self.modal = None
                    self.puzzle_input_active = False
                elif self.modal == "letter":
                    self.modal = None
                elif self.modal == "dialog":
                    self._advance_dialog()
                return
            self.inventory_open = False
            self.selected_item = None
            return

        if self.modal == "dialog":
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button != 1:
                    return
                if event.type == pygame.KEYDOWN and event.key not in (pygame.K_RETURN, pygame.K_SPACE):
                    return
                self._advance_dialog()
            return
        if self.modal == "puzzle":
            self._handle_puzzle_event(event)
            return
        if self.modal == "letter":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.modal = None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.modal = None
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state.magnifier_active:
                if self.lens_rect.collidepoint(event.pos):
                    now = pygame.time.get_ticks()
                    if now - self.lens_last_click_ms <= 900:
                        self.lens_click_count += 1
                    else:
                        self.lens_click_count = 1
                    self.lens_last_click_ms = now
                    if self.lens_click_count >= 3:
                        self.state.magnifier_active = False
                        self.selected_item = None
                        self.lens_click_count = 0
                        return
                else:
                    self.lens_click_count = 0
            if self.selected_item:
                self._use_selected(event.pos)
            else:
                self._room_click(event.pos)

    def _advance_dialog(self):
        visible_lines = self.dialog_pages[self.dialog_page:self.dialog_page + 3]
        total = sum(len(line) for line in visible_lines)
        if self.type_progress < total:
            self.type_progress = total
            return
        self.dialog_page += 3
        if self.dialog_page < len(self.dialog_pages):
            self.type_progress = 0
            return
        callback = getattr(self, "after_dialog", None)
        self.after_dialog = None
        self.modal = None
        if callback:
            callback()

    def _handle_puzzle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(event.pos):
                self.modal = None
                self.puzzle_input_active = False
            elif self.submit_rect.collidepoint(event.pos):
                self._submit_puzzle_answer()
            else:
                self.puzzle_input_active = self.puzzle_input_rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.puzzle_input_active:
                    self.puzzle_text = self.puzzle_text[:-1]
            elif event.key == pygame.K_RETURN:
                if self.puzzle_input_active:
                    self._submit_puzzle_answer()
            elif self.puzzle_input_active and event.unicode.isdigit() and len(self.puzzle_text) < 4:
                self.puzzle_text += event.unicode
            elif event.key == pygame.K_ESCAPE:
                self.modal = None
                self.puzzle_input_active = False

    def _submit_puzzle_answer(self):
        if self.puzzle_text.strip() == "136":
            self.state.puzzle_solved = True
            self.game_state.complete_puzzle("princess_chest")
            self.modal = "dialog"
            self.puzzle_input_active = False
            self._say("Hiệp sĩ", "Mở khóa thành công!", self._open_chest)
        else:
            self.puzzle_message = "Sai rồi! Lêu lêuuuuu"
            self.puzzle_text = ""
            self.puzzle_input_active = True

    def _open_chest(self):
        self.modal = None
        self.state.chest_opened = True
        self._notify("Rương đã mở. Bên trong có cuộn len màu hồng.")

    def _use_selected(self, pos):
        if self.selected_item == "magnifying_glass":
            if self.cat_hitbox.collidepoint(pos):
                self.state.magnifier_active = False
            world_pos = self._lens_screen_to_world(pos)
            if self._scale_is_visible_in_lens() and self.scale_hitbox.inflate(5, 5).collidepoint(world_pos) and self.state.magnifier_active and self.state.letter_read:
                self._move_knight_next_to_scale()
                self._collect_scale()
            return
        if self.selected_item == "pink_yarn" and self.cat_hitbox.collidepoint(pos):
            self._move_knight_to((self.cat_x - 140, self.cat_y))
            self.game_state.inventory.remove("pink_yarn")
            self.selected_item = None
            self._say("Mèo", "Meo~ bảo bối của ta đây rồi!", self._start_cat_walk, style="cat")
            return
        self.selected_item = None

    def _start_cat_walk(self):
        self.cat_x = 930.0
        if self.cat:
            self.cat.play("stand_up")
        else:
            self.state.cat_moved = True
            self.state.letter_revealed = True

    def _collect_scale(self):
        if self.state.dragon_scale_collected:
            return
        if self.knight:
            self.knight.target = None
            self.knight_waypoints.clear()
            self.knight.direction = "front"
            self.knight.animation.play("front")
        self.state.magnifier_active = False
        self.state.dragon_scale_found = self.state.dragon_scale_collected = True
        self._add_item("red_dragon_scale")
        self.selected_item = None
        self._notify("Đã tìm thấy Vảy Rồng!")
        self._say(
            "Hiệp sĩ",
            "Đây là vảy rồng sao? Ta phải tìm đường đến chỗ con rồng để cứu nàng. "
            "Nghe nói Rừng Tinh Linh có thể giúp ta giải đáp bí ẩn về chiếc vảy này...",
            self._finish_room,
        )

    def _finish_room(self):
        self.state.princess_room_completed = True

    def _room_click(self, pos):
        if self.state.magnifier_active and self.state.letter_read and self._scale_is_visible_in_lens() and self.scale_hitbox.inflate(5, 5).collidepoint(self._lens_screen_to_world(pos)):
            self._move_knight_next_to_scale()
            self._collect_scale()
        elif self.magnifier_hitbox.collidepoint(pos) and not self.state.magnifier_collected:
            self.state.magnifier_collected = True
            self._add_item("magnifying_glass")
        elif self.state.letter_revealed and self.letter_hitbox.collidepoint(pos):
            self.modal = "letter"
            self.state.letter_read = True
        elif (
            self.state.chest_opened
            and not self.state.pink_yarn_collected
            and self.yarn_hitbox.collidepoint(pos)
        ):
            self.state.pink_yarn_collected = True
            self._add_item("pink_yarn")
        elif self.cat_hitbox.collidepoint(pos):
            self._move_knight_to((self.cat_x - 140, self.cat_y))
            if self.selected_item == "pink_yarn":
                self._use_selected(pos)
            elif not self.state.cat_moved:
                self._say("Mèo", "Nếu muốn có manh mối về công chúa hãy tìm ra thứ đồ yêu thích của ta trong căn phòng này", self._mark_cat_questioned, style="cat")
        elif self.chest_hitbox.collidepoint(pos):
            if self.state.chest_opened and self.state.pink_yarn_collected:
                return
            self._move_knight_to(
                (self.chest_hitbox.right + 120, BED_CLEARANCE_Y),
                route_around_bed=True,
            )
            if self.knight:
                self.pending_chest_click = pos
            else:
                self._handle_chest_arrival(pos)

    def _handle_chest_arrival(self, clicked_pos):
        if not self.state.cat_questioned:
            self._say("Hiệp sĩ", "Ta nên hỏi con mèo kia xem nó biết gì trước đã.")
        elif not self.state.chest_opened:
            self.modal = "puzzle"
            self.puzzle_text = self.puzzle_message = ""
            self.puzzle_input_active = False
        elif not self.state.pink_yarn_collected and self.yarn_hitbox.collidepoint(clicked_pos):
            self.state.pink_yarn_collected = True
            self._add_item("pink_yarn")

    def _move_knight_next_to_scale(self):
        foot_y = (
            self.knight.y + KNIGHT_DRAW_SIZE[1]
            if self.knight
            else WALKABLE_FLOOR.top
        )
        self._move_knight_to(
            (
                self.scale_hitbox.centerx + 130,
                foot_y,
            )
        )

    def _move_knight_to(self, foot_position, route_around_bed=False):
        if self.knight:
            self.pending_chest_click = None
            self.knight_waypoints.clear()
            foot_x = max(0, min(SCREEN_WIDTH, foot_position[0]))
            foot_y = max(
                BED_CLEARANCE_Y if foot_x < BED_EDGE_X else WALKABLE_FLOOR.top,
                min(SCREEN_HEIGHT, foot_position[1]),
            )
            x = foot_x - KNIGHT_DRAW_SIZE[0] // 2
            y = foot_y - KNIGHT_DRAW_SIZE[1]
            x = max(0, min(SCREEN_WIDTH - KNIGHT_DRAW_SIZE[0], x))
            if route_around_bed and foot_x < BED_EDGE_X:
                waypoint_x = BED_EDGE_X + 50 - KNIGHT_DRAW_SIZE[0] // 2
                waypoint_y = SCREEN_HEIGHT - 55 - KNIGHT_DRAW_SIZE[1]
                self.knight_waypoints.append((x, y))
                self.knight.move_to(waypoint_x, waypoint_y)
            else:
                self.knight.move_to(x, y)

    def _lens_screen_to_world(self, position):
        if not self.lens_rect.collidepoint(position):
            return position
        center = self.lens_rect.center
        return (
            self.lens_world_center[0] + (position[0] - center[0]) / ZOOM_FACTOR,
            self.lens_world_center[1] + (position[1] - center[1]) / ZOOM_FACTOR,
        )

    def _update_lens_mapping(self):
        crop_size = self.lens_radius * 2 // ZOOM_FACTOR
        self.lens_rect.size = (self.lens_radius * 2, self.lens_radius * 2)
        self.lens_rect.center = self.mouse_pos
        left = max(0, min(SCREEN_WIDTH - crop_size, self.mouse_pos[0] - crop_size // 2))
        top = max(0, min(SCREEN_HEIGHT - crop_size, self.mouse_pos[1] - crop_size // 2))
        self.lens_world_center = (left + crop_size / 2, top + crop_size / 2)
        return left, top, crop_size

    def _scale_is_visible_in_lens(self):
        dx = self.scale_hitbox.centerx - self.lens_world_center[0]
        dy = self.scale_hitbox.centery - self.lens_world_center[1]
        return dx * dx + dy * dy <= (self.lens_radius / ZOOM_FACTOR) ** 2

    def _mark_cat_questioned(self):
        self.state.cat_questioned = True

    def update(self, dt):
        if self.inventory_open:
            return
        if self.knight:
            self.knight.update(dt)
            if self.knight.target is None:
                if self.knight_waypoints:
                    self.knight.move_to(*self.knight_waypoints.pop(0))
                elif self.pending_chest_click is not None:
                    clicked_pos = self.pending_chest_click
                    self.pending_chest_click = None
                    self._handle_chest_arrival(clicked_pos)
        if self.modal == "dialog" and self.dialog_page < len(self.dialog_pages):
            page = self.dialog_pages[self.dialog_page:self.dialog_page + 3]
            self.type_progress = min(sum(map(len, page)), self.type_progress + dt * 42)
        self.puzzle_cursor_time += dt
        if self.notice_time > 0:
            self.notice_time = max(0, self.notice_time - dt)
        if self.state.magnifier_active and self.state.letter_read:
            dx = self.mouse_pos[0] - self.scale_hitbox.centerx
            dy = self.mouse_pos[1] - self.scale_hitbox.centery
            if dx * dx + dy * dy <= (self.lens_radius / ZOOM_FACTOR) ** 2:
                self.state.dragon_scale_found = True
        if self.cat and not self.state.cat_moved:
            self.cat.update(dt)
            if self.cat.current_animation == "stand_up" and self.cat.is_finished():
                self.cat.play("walk")
            elif self.cat.current_animation == "walk":
                self.cat_x += 180 * dt
                if self.cat_x - CAT_DRAW_SIZE[0] // 2 > self.letter_hitbox.right:
                    self.state.letter_revealed = True
                if self.cat_x > SCREEN_WIDTH + 110:
                    self.state.cat_moved = True

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        # Visible interactables use the room's existing art where possible;
        # missing prop art is drawn as simple, readable fantasy placeholders.
        self._draw_chest(screen)
        if self.knight:
            self.knight.draw(screen, size=KNIGHT_DRAW_SIZE)
        if self.state.letter_revealed or not self.state.cat_moved:
            if self.letter_item_icon:
                screen.blit(self.letter_item_icon, self.letter_hitbox)
            else:
                pygame.draw.rect(screen, (231, 207, 151), self.letter_hitbox, border_radius=4)
        if not self.state.cat_moved:
            self._draw_cat(screen)
        if not self.state.magnifier_collected:
            self._draw_magnifier_item(screen, self.magnifier_hitbox.center, 0.48)
        self._draw_scale(screen)
        if self.modal == "dialog":
            if self.dialog_style == "cat":
                self._draw_cat_dialog(screen)
            else:
                self._draw_dialog(screen)
        elif self.modal == "puzzle":
            self._draw_puzzle(screen)
        elif self.modal == "letter":
            self._draw_letter(screen)
        if self.state.magnifier_active:
            self._draw_lens(screen)
        if self.notice_time > 0:
            draw_dialogue_frame(screen, pygame.Rect(350, 22, 580, 52))
            self._text(screen, self.notice, self.small, (70, 45, 26), (640, 48), True)
        super().draw(screen)

    def _draw_cat(self, screen):
        if self.cat:
            frame = self.cat.get_current_frame()
            if frame:
                frame = pygame.transform.smoothscale(frame, CAT_DRAW_SIZE)
                screen.blit(frame, frame.get_rect(midbottom=(int(self.cat_x), self.cat_y)))
        else:
            pygame.draw.ellipse(screen, (210, 157, 127), (self.cat_x - 49, self.cat_y - 84, 98, 71))
            pygame.draw.circle(screen, (225, 178, 145), (int(self.cat_x), self.cat_y - 84), 31)
        self.cat_hitbox.size = CAT_DRAW_SIZE
        self.cat_hitbox.midbottom = (int(self.cat_x), self.cat_y)

    def _draw_chest(self, screen):
        image = self.chest_open_scaled if self.state.chest_opened else self.chest_closed_scaled
        if image:
            screen.blit(image, (4, 360))
            if self.state.chest_opened and not self.state.pink_yarn_collected:
                self._draw_yarn(screen, self.yarn_hitbox.center, 15)
        else:
            x, y = 4, 360
            pygame.draw.rect(screen, (97, 54, 35), (x, y, 78, 48), border_radius=8)
            pygame.draw.rect(screen, (175, 119, 61), (x, y, 78, 48), 4, border_radius=8)
            pygame.draw.rect(screen, (207, 166, 79), (x + 54, y + 20, 18, 24), border_radius=4)

    def _draw_yarn(self, screen, center, radius=18):
        if self.yarn_image:
            image = self.yarn_icon if radius == 25 else pygame.transform.smoothscale(self.yarn_image, (radius * 2, radius * 2))
            screen.blit(image, image.get_rect(center=center))
            return
        pygame.draw.circle(screen, (205, 85, 143), center, radius)
        for dy in (-8, 0, 8):
            pygame.draw.arc(screen, (255, 193, 218), (center[0] - radius + 3, center[1] + dy - 7, radius * 2 - 6, 14), 0.2, 2.9, 2)

    def _draw_scale(self, screen):
        if self.state.dragon_scale_collected:
            return
        if self.scale_image:
            if self.scale_tiny:
                screen.blit(self.scale_tiny, self.scale_tiny.get_rect(center=self.scale_hitbox.center))
            return
        color = (180, 34, 40) if self.state.magnifier_active else (105, 73, 63)
        pygame.draw.ellipse(screen, color, self.scale_hitbox)
        pygame.draw.arc(screen, (244, 174, 90), self.scale_hitbox, 0.1, 3.0, 2)

    @staticmethod
    def _draw_magnifier(screen, center, scale=1):
        radius = int(20 * scale)
        pygame.draw.circle(screen, (222, 207, 168), center, radius, max(2, int(5 * scale)))
        pygame.draw.line(screen, (104, 67, 39), (center[0] + radius - 2, center[1] + radius - 2), (center[0] + radius * 2, center[1] + radius * 2), max(3, int(7 * scale)))

    def _draw_magnifier_item(self, screen, center, fallback_scale=1):
        if self.magnifier_icon:
            screen.blit(self.magnifier_icon, self.magnifier_icon.get_rect(center=center))
        else:
            self._draw_magnifier(screen, center, fallback_scale)

    def _draw_lens(self, screen):
        source = self.background.copy()
        left, top, crop_size = self._update_lens_mapping()
        crop = source.subsurface((left, top, crop_size, crop_size)).copy()
        enlarged = pygame.transform.smoothscale(crop, self.lens_rect.size)
        if not self.state.dragon_scale_collected and self.scale_image and self._scale_is_visible_in_lens():
            magnified_size = (self.scale_tiny.get_width() * 15, self.scale_tiny.get_height() * 15)
            magnified_scale = pygame.transform.smoothscale(self.scale_image, magnified_size)
            scale_center = (
                round(self.lens_rect.centerx + (self.scale_hitbox.centerx - self.lens_world_center[0]) * ZOOM_FACTOR),
                round(self.lens_rect.centery + (self.scale_hitbox.centery - self.lens_world_center[1]) * ZOOM_FACTOR),
            )
            enlarged.blit(magnified_scale, magnified_scale.get_rect(center=(scale_center[0] - self.lens_rect.left, scale_center[1] - self.lens_rect.top)))
        lens = pygame.Surface(self.lens_rect.size, pygame.SRCALPHA)
        lens.blit(enlarged, (0, 0))
        mask = pygame.Surface(lens.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (self.lens_radius, self.lens_radius), self.lens_radius)
        lens.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(lens, self.lens_rect.topleft)
        pygame.draw.circle(screen, (191, 143, 63), self.lens_rect.center, self.lens_radius, 7)

    def _draw_dialog(self, screen):
        box = STANDARD_DIALOG_RECT
        draw_dialogue_frame(screen, box)
        self._text(screen, self.dialogue[0], self.font, (112, 65, 34), (box.x + 27, box.y + 18))
        page = self.dialog_pages[self.dialog_page:self.dialog_page + 3]
        remaining = int(self.type_progress)
        y = box.y + 50
        for line in page:
            shown = line[:remaining]
            remaining -= len(shown)
            self._text(screen, shown, self.font, (55, 42, 31), (box.x + 28, y))
            y += 25
        self._text(screen, "Click", self.small, (112, 75, 42), (box.right - 50, box.y + 30), True)

    def _draw_cat_dialog(self, screen):
        box = pygame.Rect(0, 0, 260, 106)
        box.bottom = self.cat_hitbox.top - 12
        box.left = self.cat_hitbox.centerx + 35
        box.clamp_ip(pygame.Rect(12, 12, SCREEN_WIDTH - 24, SCREEN_HEIGHT - 24))
        if box.colliderect(self.restart_button_rect):
            box.right = self.restart_button_rect.left - 12
        draw_dialogue_frame(screen, box)
        self._text(screen, self.dialogue[0], self.small, (112, 65, 34), (box.x + 16, box.y + 12))
        page = self.dialog_pages[self.dialog_page:self.dialog_page + 3]
        remaining = int(self.type_progress)
        y = box.y + 39
        for line in page:
            shown = line[:remaining]
            remaining -= len(shown)
            self._text(screen, shown, self.small, (55, 42, 31), (box.x + 16, y))
            y += 21
        prompt = self.small.render("Click", True, (112, 75, 42))
        screen.blit(prompt, prompt.get_rect(right=box.right - 12, bottom=box.bottom - 10))

    def _draw_puzzle(self, screen):
        box = pygame.Rect(360, 155, 560, 410)
        draw_dialogue_frame(screen, box)
        self.close_rect = pygame.Rect(box.right - 48, box.y + 12, 34, 34)
        self.submit_rect = pygame.Rect(box.centerx - 88, box.y + 300, 176, 48)
        self._text(screen, "Rương báu", self.title_font, (89, 55, 30), (box.centerx, box.y + 46), True)
        for i, text in enumerate(("2 + 3 = 10", "4 + 5 = 36", "6 + 7 = 78", "8 + 9 = ?")):
            self._text(screen, text, self.font, (56, 44, 32), (box.centerx, box.y + 100 + i * 37), True)
        self.puzzle_input_rect = pygame.Rect(box.centerx - 80, box.y + 255, 160, 40)
        field = self.puzzle_input_rect
        pygame.draw.rect(screen, (255, 250, 229) if self.puzzle_input_active else (255, 247, 220), field, border_radius=5)
        pygame.draw.rect(screen, (185, 119, 47) if self.puzzle_input_active else (125, 84, 47), field, 3 if self.puzzle_input_active else 2, border_radius=5)
        shown_answer = self.puzzle_text
        if self.puzzle_input_active and int(self.puzzle_cursor_time / 0.5) % 2 == 0:
            shown_answer += "|"
        if shown_answer:
            self._text(screen, shown_answer, self.font, (72, 51, 33), (field.x + 12, field.centery - self.font.get_height() // 2))
        self._button(screen, self.submit_rect, "XÁC NHẬN")
        self._button(screen, self.close_rect, "×", smaller=True)
        if self.puzzle_message:
            self._text(screen, self.puzzle_message, self.small, (145, 41, 33), (box.centerx, box.bottom - 27), True)

    def _draw_letter(self, screen):
        box = pygame.Rect(260, 170, 760, 370)
        if self.letter_panel_image:
            screen.blit(self.letter_panel_image, box)
        else:
            self._panel(screen, box, paper=True)
        self._text(screen, "Lá thư bí ẩn", self.title_font, (97, 57, 31), (box.centerx, box.y + 70), True)
        self._text(screen, "Thứ đỏ rực đang ngủ dưới ánh trăng.", self.font, (64, 45, 32), (box.centerx, box.y + 180), True)
        self._button(screen, pygame.Rect(box.centerx - 80, box.bottom - 75, 160, 46), "ĐÓNG THƯ")

    @staticmethod
    def _panel(screen, rect, paper=False):
        pygame.draw.rect(screen, (222, 194, 139) if paper else (221, 199, 158), rect, border_radius=13)
        pygame.draw.rect(screen, (105, 67, 39), rect, 4, border_radius=13)
        pygame.draw.rect(screen, (242, 220, 177), rect.inflate(-12, -12), 1, border_radius=9)

    def _button(self, screen, rect, label, smaller=False):
        pygame.draw.rect(screen, (119, 77, 44), rect, border_radius=7)
        pygame.draw.rect(screen, (210, 169, 97), rect, 2, border_radius=7)
        self._text(screen, label, self.small if smaller else self.font, (255, 239, 198), rect.center, True)

    @staticmethod
    def _text(screen, text, font, color, pos, center=False):
        image = font.render(text, True, color)
        rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        screen.blit(image, rect)

