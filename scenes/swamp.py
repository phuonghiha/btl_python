"""Scene controller for the poisonous swamp and its lily-pad puzzle."""

import glob
import math
import os

import pygame

from game_fonts import content1
from characters.frog import Frog
from player import Player
from puzzes.swamp import MAX_JUMP_DISTANCE, LilyPadPuzzle
from puzzes.swamp.swamp_puzzle import (
    CONTENT_FONT_PATH,
    FINAL_FROG_SIZE,
    FINAL_PLAYER_SIZE,
    SwampPuzzle,
    TITLE_FONT_PATH,
)
from base_scene import BaseScene, draw_dialogue_frame
from settings import (
    SCREEN_WIDTH,
)

HINT_INK = (104, 69, 43)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENE_ASSET_DIR = os.path.join(BASE_DIR, "assets", "images", "sence_3")
BACKGROUND_PATH = os.path.join(SCENE_ASSET_DIR, "bg.png")
BACKGROUND2_PATH = os.path.join(SCENE_ASSET_DIR, "background2.png")
LILY_PAD_DIR = os.path.join(SCENE_ASSET_DIR, "Lá sen")

PAD_SIZE = 96
PLAYER_SIZE = (76, 104)
FROG_SIZE = (92, 92)
WRONG_PAD_DAMAGE = 12
POISON_DAMAGE_PER_SECOND = 5
JUMP_DURATION = 0.42
JUMP_ARC_HEIGHT = 72
WRONG_SINK_DURATION = 0.65
WRONG_SINK_OFFSET = 22
WRONG_RETURN_DURATION = 0.85
WRONG_RETURN_ARC = 96

LEFT_BANK = (
    (0, 280), (70, 300), (140, 340), (220, 380), (300, 430),
    (370, 500), (450, 570), (540, 650), (620, 720), (0, 720),
)
FAR_BANK = (
    (800, 204), (825, 177), (860, 155), (920, 145), (980, 153),
    (1035, 170), (1090, 190), (1120, 207), (1100, 224),
    (1050, 235), (990, 235), (925, 228), (860, 220), (825, 215),
)


def _numbered_pngs(folder):
    paths = glob.glob(os.path.join(folder, "*.png"))
    return sorted(
        paths,
        key=lambda path: int(
            os.path.splitext(os.path.basename(path))[0].rsplit("-", 1)[1]
        ),
    )


def _point_in_polygon(point, polygon):
    x, y = point
    inside = False
    previous_x, previous_y = polygon[-1]
    for current_x, current_y in polygon:
        crosses_y = (current_y > y) != (previous_y > y)
        if crosses_y:
            intersection_x = (
                (previous_x - current_x) * (y - current_y)
                / (previous_y - current_y)
                + current_x
            )
            if x < intersection_x:
                inside = not inside
        previous_x, previous_y = current_x, current_y
    return inside


class SwampScene(BaseScene):

    def __init__(self, game):
        super().__init__(game)

        background = pygame.image.load(BACKGROUND_PATH).convert()
        self.background = pygame.transform.smoothscale(
            background, (SCREEN_WIDTH, game.screen.get_height())
        )
        background2 = pygame.image.load(BACKGROUND2_PATH).convert()
        self.background2 = pygame.transform.smoothscale(
            background2, (SCREEN_WIDTH, game.screen.get_height())
        )
        self._show_background2 = False

        pad_paths = _numbered_pngs(LILY_PAD_DIR)
        if len(pad_paths) != 8:
            raise ValueError(
                f"Expected 8 lily-pad images in {LILY_PAD_DIR}, "
                f"found {len(pad_paths)}"
            )
        self.pad_images = {}
        for direction, path in enumerate(pad_paths):
            self.pad_images[direction] = pygame.image.load(path).convert_alpha()
        self._sized_pad_images = {}
        glow_size = PAD_SIZE + 48
        self.pad_glow = pygame.Surface(
            (glow_size, glow_size), pygame.SRCALPHA
        )
        self._sized_pad_glows = {}
        glow_center = glow_size // 2
        for radius, alpha in ((62, 14), (50, 24), (38, 38)):
            pygame.draw.circle(
                self.pad_glow,
                (255, 255, 255, alpha),
                (glow_center, glow_center),
                radius,
            )

        self.puzzle = LilyPadPuzzle()
        self.player_start = (190, 505)
        self.player = Player(*self.player_start)
        self.player_land = "left"
        self.frog = Frog(900, 80)
        self.frog.jump()
        self.duel_puzzle = SwampPuzzle(
            self.player, self.frog, self.game_state, game.screen
        )
        self._sword_inventory_synced = False

        self.font = content1(24)
        self.small_font = content1(18)
        self._jump = None
        self._wrong_sink = None
        self._wrong_pad_landing = None
        self._wrong_pad_to_respawn = None
        self._returning_after_wrong = False
        self._return_to_left_bank = False
        self._finish_after_jump = False
        self._final_pad_after_jump = False
        self._reached_final_pad = False
        self._reached_far_bank = False
        self.message = (
            "Màn sương độc phủ kín mặt đầm. Hãy bước lên những lá sen để sang bờ bên kia; mặt nước bên dưới chẳng hề hiền hòa."
        )
        self.message_timer = 0

    def reset(self):
        """Rebuild the scene after a full game restart."""
        self.__init__(self.game)

    def _player_feet(self):
        return (
            self.player.x + PLAYER_SIZE[0] / 2,
            self.player.y + PLAYER_SIZE[1],
        )

    def _start_jump(
        self,
        target,
        *,
        return_to_left_bank=False,
        finish=False,
        duration=JUMP_DURATION,
        arc_height=JUMP_ARC_HEIGHT,
    ):
        self._jump = {
            "start": (self.player.x, self.player.y),
            "target": target,
            "elapsed": 0.0,
            "duration": duration,
            "arc_height": arc_height,
        }
        self._return_to_left_bank = return_to_left_bank
        self._finish_after_jump = finish

        dx = target[0] - self.player.x
        dy = target[1] - self.player.y
        if abs(dx) > abs(dy):
            animation = "walk_right" if dx >= 0 else "walk_left"
        else:
            animation = "back" if dy < 0 else "front"
        self.player.animation.play(animation)

    def _player_target(self, screen_position):
        return (
            screen_position[0] - PLAYER_SIZE[0] // 2,
            screen_position[1] - PLAYER_SIZE[1],
        )

    def handle_event(self, event):
        if super().handle_event(event):
            return

        if (
            event.type != pygame.MOUSEBUTTONDOWN
            or event.button != 1
            or self._jump is not None
            or self._wrong_sink is not None
            or self.game_state.health <= 0
        ):
            return

        position = event.pos
        if self.duel_puzzle.active:
            self.duel_puzzle.handle_event(position)
            if self.duel_puzzle.quit:
                self.game.change_scene("world_map")
            return
        if self.duel_puzzle.quit:
            return

        if self._reached_final_pad or self.puzzle.is_complete:
            if _point_in_polygon(position, FAR_BANK):
                if math.dist(self._player_feet(), position) > MAX_JUMP_DISTANCE:
                    self.message = "Bờ bên kia vẫn còn xa. Hãy tìm một điểm đặt chân thích hợp trước khi tiếp tục!"
                    self.message_timer = 1.7
                    return
                self._reached_final_pad = False
                self.player_land = None
                self._start_jump(self._player_target(position), finish=True)
            return

        pad_id = self.puzzle.pad_at(position)
        if pad_id is not None:
            self._handle_pad_click(pad_id)
            return

        if self.player_land == "left" and _point_in_polygon(position, LEFT_BANK):
            feet = self._player_feet()
            if _point_in_polygon(feet, LEFT_BANK):
                self.player.move_to(*self._player_target(position))
            return

        if (
            self.player_land is None
            and not self._reached_final_pad
            and _point_in_polygon(position, LEFT_BANK)
            and math.dist(self._player_feet(), position) <= MAX_JUMP_DISTANCE
        ):
            self.player.target = None
            self._start_jump(
                self._player_target(position), return_to_left_bank=True
            )
            return

        if (
            self.player_land == "far"
            and self._reached_far_bank
            and _point_in_polygon(position, FAR_BANK)
            and _point_in_polygon(self._player_feet(), FAR_BANK)
        ):
            self.player.move_to(*self._player_target(position))

    def _handle_pad_click(self, pad_id):
        if self.player.target is not None:
            self.player.target = None

        result = self.puzzle.select(pad_id, self._player_feet())
        if result == "too_far":
            self.message = "Hỡi hiệp sĩ, chiếc lá sen kia nằm ngoài tầm với. Chớ cưỡng cầu, hãy tìm một lối đi gần hơn!"
            self.message_timer = 1.7
            return
        if result == "stay":
            return
        if result == "wrong":
            self.game_state.take_damage(WRONG_PAD_DAMAGE)
            self.message = "Lá sen quá yếu! Nó không thể chịu nổi sức nặng của ngươi!!"
            self.message_timer = 2.5
            self.player.target = None
            self.player_land = None
            self._wrong_pad_landing = pad_id
            pad = next(pad for pad in self.puzzle.pads if pad.pad_id == pad_id)
            target = (pad.x - PLAYER_SIZE[0] // 2, pad.y - PLAYER_SIZE[1] + 16)
            self._start_jump(target)
            return

        pad = next(pad for pad in self.puzzle.pads if pad.pad_id == pad_id)
        self.player_land = None
        if result == "complete":
            self._final_pad_after_jump = True
        target = (pad.x - PLAYER_SIZE[0] // 2, pad.y - PLAYER_SIZE[1] + 16)
        self._start_jump(target)

    def update(self, dt):
        if self.inventory_open:
            return

        if self.game_state.health <= 0:
            return

        if self.message_timer > 0:
            self.message_timer = max(0, self.message_timer - dt)
            if self.message_timer == 0 and self._reached_final_pad:
                self.message = "Bờ bên kia đã ở rất gần, hỡi hiệp sĩ. Hãy vững bước qua những chiếc lá sen cuối cùng!"
            elif self.message_timer == 0 and not self._reached_far_bank:
                self.message = "Hỡi hiệp sĩ, muốn sang được bờ bên kia, ngươi phải bước lên những lá sen giữa hồ. Nhưng hãy cẩn trọng, không phải chiếc lá nào cũng đủ sức nâng đỡ ngươi!"

        if not self._reached_far_bank and not self.game_state.has_poison_protection:
            self.game_state.take_damage(POISON_DAMAGE_PER_SECOND * dt)
            if self.game_state.health <= 0:
                return

        self.frog.update(dt)
        if (
            not self._show_background2
            and self.frog.animation.current_animation != "jump"
        ):
            self.frog.jump()

        self.duel_puzzle.update(dt)
        if self.duel_puzzle.sword_awarded and not self._sword_inventory_synced:
            self.add_item(
                "holy_sword", "Kiếm thánh", "assets/images/Sword.png"
            )
            self.game_state.has_holy_sword = True
            self._sword_inventory_synced = True
        if self.duel_puzzle.active:
            return

        if self._wrong_sink is not None:
            self.player.animation.update(dt)
            self._wrong_sink["elapsed"] += dt
            progress = min(
                self._wrong_sink["elapsed"] / WRONG_SINK_DURATION, 1.0
            )
            self.player.y = (
                self._wrong_sink["start_y"] + WRONG_SINK_OFFSET * progress
            )
            if progress >= 1:
                self._wrong_sink = None
                self._returning_after_wrong = True
                self._start_jump(
                    self.player_start,
                    duration=WRONG_RETURN_DURATION,
                    arc_height=WRONG_RETURN_ARC,
                )
            return

        if self._jump is None:
            if self.player_land is not None:
                self.player.update(dt)
            else:
                self.player.animation.update(dt)
            return

        self.player.animation.update(dt)
        self._jump["elapsed"] += dt
        progress = min(
            self._jump["elapsed"] / self._jump["duration"], 1.0
        )
        start_x, start_y = self._jump["start"]
        target_x, target_y = self._jump["target"]
        arc = self._jump["arc_height"] * 4 * progress * (1 - progress)
        self.player.x = start_x + (target_x - start_x) * progress
        self.player.y = start_y + (target_y - start_y) * progress - arc

        if progress < 1:
            return

        self.player.x, self.player.y = target_x, target_y
        self._jump = None
        self.player.animation.play("front")

        if self._wrong_pad_landing is not None:
            self._wrong_pad_to_respawn = self.puzzle.remove_decoy(
                self._wrong_pad_landing
            )
            self._wrong_pad_landing = None
            self._wrong_sink = {
                "start_y": self.player.y,
                "elapsed": 0.0,
            }
        elif self._returning_after_wrong:
            self._returning_after_wrong = False
            self.puzzle.return_to_shore()
            self.puzzle.restore_decoy(self._wrong_pad_to_respawn)
            self._wrong_pad_to_respawn = None
            self.player_land = "left"
        elif self._return_to_left_bank:
            self._return_to_left_bank = False
            self.puzzle.return_to_shore()
            self.player_land = "left"
        elif self._final_pad_after_jump:
            self._final_pad_after_jump = False
            self._reached_final_pad = True
            self.player_land = None
            self.message = "Màn sương độc vẫn giăng kín đầm. Hãy tiếp tục hành trình trên những lá sen."
            self.message_timer = 0
        elif self._finish_after_jump:
            self._finish_after_jump = False
            self._reached_far_bank = True
            self._show_background2 = True
            self.player_land = "far"
            self.message = ""
            self.message_timer = 0
            self.duel_puzzle.start()
            self.game_state.complete_puzzle("lily_pad")

    def draw(self, screen):
        background = (
            self.background2 if self._show_background2 else self.background
        )
        screen.blit(background, (0, 0))

        if not self._show_background2:
            hovered_pad_id = self.puzzle.pad_at(pygame.mouse.get_pos())
            player_feet = self._player_feet()
            for pad in self.puzzle.pads:
                if (
                    pad.pad_id == hovered_pad_id
                    and self.puzzle.is_within_jump_range(
                        pad.pad_id, player_feet
                    )
                ):
                    glow = self.pad_glow
                    if pad.size != PAD_SIZE:
                        glow = self._sized_pad_glows.get(pad.size)
                        if glow is None:
                            glow_size = round(
                                self.pad_glow.get_width()
                                * pad.size / PAD_SIZE
                            )
                            glow = pygame.transform.smoothscale(
                                self.pad_glow, (glow_size, glow_size)
                            )
                            self._sized_pad_glows[pad.size] = glow
                    screen.blit(
                        glow,
                        glow.get_rect(center=(pad.x, pad.y)),
                    )
                nearest_direction = round(pad.direction) % 8
                turn_steps = (pad.direction - nearest_direction + 4) % 8 - 4
                cache_key = (pad.direction, pad.size)
                image = self._sized_pad_images.get(cache_key)
                if image is None:
                    image = self.pad_images[nearest_direction]
                    if abs(turn_steps) > 1e-6:
                        rotated = pygame.transform.rotate(
                            image, -turn_steps * 45
                        )
                        crop = pygame.Surface(
                            image.get_size(), pygame.SRCALPHA
                        )
                        crop.blit(
                            rotated,
                            rotated.get_rect(center=crop.get_rect().center),
                        )
                        image = crop
                    if image.get_size() != (pad.size, pad.size):
                        image = pygame.transform.smoothscale(
                            image, (pad.size, pad.size)
                        )
                    self._sized_pad_images[cache_key] = image
                screen.blit(image, image.get_rect(center=(pad.x, pad.y)))

        frog_size = FINAL_FROG_SIZE if self._show_background2 else FROG_SIZE
        player_size = FINAL_PLAYER_SIZE if self._show_background2 else PLAYER_SIZE
        self.frog.draw(screen, size=frog_size)
        if self._wrong_sink is None:
            self.player.draw(screen, size=player_size)
        else:
            self._draw_half_submerged_player(screen)
        self.duel_puzzle.draw(screen)
        self._draw_interface(screen)
        super().draw(screen)

    def _draw_half_submerged_player(self, screen):
        frame = self.player.animation.get_current_frame()
        if frame is None:
            return

        frame = pygame.transform.smoothscale(frame, PLAYER_SIZE)
        visible_height = PLAYER_SIZE[1] // 2
        visible_part = frame.subsurface(
            (0, 0, PLAYER_SIZE[0], visible_height)
        )
        screen.blit(visible_part, (int(self.player.x), int(self.player.y)))

        ripple = pygame.Rect(
            int(self.player.x + 3),
            int(self.player.y + visible_height - 5),
            PLAYER_SIZE[0] - 6,
            14,
        )
        pygame.draw.ellipse(screen, (158, 190, 132), ripple, 2)

    def _draw_interface(self, screen):
        if self.message:
            max_text_width = screen.get_width() - 184
            words = self.message.split()
            lines = []
            current = ""
            for word in words:
                candidate = word if not current else f"{current} {word}"
                if current and self.small_font.size(candidate)[0] > max_text_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                lines.append(current)
            rendered_lines = [
                self.small_font.render(line, True, HINT_INK) for line in lines
            ]
            hint_width = min(
                screen.get_width() - 160,
                max((line.get_width() for line in rendered_lines), default=0) + 40,
            )
            hint_height = max(54, len(rendered_lines) * 24 + 20)
            hint_panel = pygame.Rect(
                24, screen.get_height() - hint_height - 18, hint_width, hint_height
            )
            draw_dialogue_frame(screen, hint_panel)
            text_y = hint_panel.y + 10
            for line in rendered_lines:
                screen.blit(
                    line,
                    line.get_rect(centerx=hint_panel.centerx, top=text_y),
                )
                text_y += 24
