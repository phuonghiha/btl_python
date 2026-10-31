"""Full Dragon Cave journey, reusing the existing two puzzle modules."""

from pathlib import Path

import pygame

from base_scene import BaseScene, STANDARD_DIALOG_RECT, draw_dialogue_frame
from characters.dragon import Dragon
from characters.knight import Knight
from characters.princess import Princess
from game_fonts import content1, title
from puzzes.dragoncave import DragonBlockGame
from puzzes.dragoncave1 import DragonCave1Scene
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


ROOT = Path(__file__).resolve().parents[1]
SCENE_ASSETS = ROOT / "assets" / "images" / "sence_4"
CHARACTER_ASSETS = ROOT / "assets" / "sprites"


class DragonCaveScene(BaseScene):
    """Runs cave exploration, gem puzzle, dragon fight, and rescue in order."""

    DIALOGUE = (
        ("Hiệp sĩ", "Cuối cùng ta cũng tìm thấy ngươi! Hãy thả công chúa ra!"),
        (
            "Rồng",
            "Ngươi đã vượt qua những cạm bẫy bên ngoài, nhưng chưa chắc đã đủ sức đối đầu với ta.",
        ),
        ("Hiệp sĩ", "Ta nhất định sẽ đưa công chúa trở về!"),
        ("Rồng", "Muốn cứu công chúa, ngươi sẽ phải đánh bại ta!"),
    )
    RESCUE_DIALOGUE = (
        ("Công chúa", "Chàng đã đến cứu ta!"),
        ("Hiệp sĩ", "Ta đã hứa sẽ đưa nàng trở về an toàn."),
    )

    def __init__(self, game):
        super().__init__(game)
        self._load_assets()
        self._font = content1(22)
        self._small_font = content1(18)
        self._title_font = title(38)
        self._scaled_knight_cache = {}
        self.dragon = Dragon()
        self.princess = Princess()
        self.reset()

    def _load_assets(self):
        width, height = self.game.screen.get_size()
        self.width, self.height = width, height
        self.ui_scale = min(width / SCREEN_WIDTH, height / SCREEN_HEIGHT)

        def load_background(filename):
            image = pygame.image.load(str(SCENE_ASSETS / filename)).convert()
            return pygame.transform.smoothscale(image, (width, height))

        self.cave_background = load_background("dragon_cave.png")
        cave_start = load_background("cave1.png")
        cave_deeper = load_background("cave2.png")
        self.exploration_background = self._join_cave_backgrounds(
            cave_start, cave_deeper
        )
        self.inner_darkness = pygame.Surface((width, height), pygame.SRCALPHA)
        self.inner_darkness.fill((18, 9, 9, 88))

        flower = pygame.image.load(str(SCENE_ASSETS / "magicflower.png")).convert_alpha()
        flower_size = max(72, int(138 * self.ui_scale))
        self.flower_image = pygame.transform.smoothscale(
            flower, (flower_size, flower_size)
        )

        self.dragon_defeated_image = pygame.image.load(
            str(SCENE_ASSETS / "dragonchibi.png")
        ).convert_alpha()

    def _join_cave_backgrounds(self, first, second):
        """Blend the two existing cave images across their shared floor."""
        overlap = min(200, self.width // 4)
        world = pygame.Surface(
            (self.width * 2 - overlap, self.height)
        ).convert()
        world.blit(first, (0, 0))

        strip_width = max(1, overlap // 32)
        for x in range(0, overlap, strip_width):
            current_width = min(strip_width, overlap - x)
            strip = second.subsurface(
                (x, 0, current_width, self.height)
            ).copy()
            strip.set_alpha(round(255 * (x + current_width) / overlap))
            world.blit(strip, (self.width - overlap + x, 0))

        second_tail = second.subsurface(
            (overlap, 0, self.width - overlap, self.height)
        )
        world.blit(second_tail, (self.width, 0))
        return world

    def _make_puzzle(self):
        return DragonBlockGame(
            screen=self.game.screen,
            sword=bool(self.game_state.has_holy_sword),
            game_state=self.game_state,
        )

    def reset(self):
        self.phase = "explore"
        self.camera_x = 0.0
        self.floor_y = self.height - int(118 * self.ui_scale)
        self.world_width = self.exploration_background.get_width()
        self.exit_x = self.world_width - int(100 * self.ui_scale)
        self.flower_x = int(self.width * 0.54)
        self.explore_elapsed = 0.0
        self.flower_visible = False
        self.after_flower_timer = 0.0
        self.white_transition_alpha = 0
        self.white_transition_duration = 0.8
        self.flower_used = bool(
            getattr(self.game_state, "dragon_cave_flower_used", False)
        )
        self.explore_notice = "Nhấp vào lối đi để tiến sâu vào hang."
        self.notice_timer = 0.0
        self.flower_glow_timer = 0.0
        self.interaction_timer = 0.0
        self.dialogue_index = 0
        self.rescue_ready = False
        self.retry_button = pygame.Rect(0, 0, 0, 0)
        self.leave_button = pygame.Rect(0, 0, 0, 0)
        self.explore_player_size = (
            max(64, int(104 * self.ui_scale)),
            max(84, int(142 * self.ui_scale)),
        )
        self.battle = self._make_puzzle()
        # Retain the original puzzle attribute for the existing battle tests/tools.
        self.puzzle = self.battle
        self.gem_puzzle = None
        self.knight = Knight(
            int(90 * self.ui_scale),
            self.floor_y - self.explore_player_size[1],
        )

        if self.game_state.princess_saved:
            self._set_phase("completed")
        elif self.game_state.dragon_defeated:
            self._begin_rescue()
        elif self.game_state.dragon_cave_puzzle_solved:
            self._begin_boss_dialogue()

    def start_battle(self):
        """Enter the existing battle directly for focused battle playtests."""
        self.battle = self._make_puzzle()
        self.puzzle = self.battle
        self._set_phase("battle")

    def _set_phase(self, phase):
        self.phase = phase

    def _show_notice(self, text, duration=3.0):
        self.explore_notice = text
        self.notice_timer = duration

    def _flower_rect(self):
        rect = self.flower_image.get_rect()
        rect.center = (
            self.flower_x,
            self.floor_y - rect.height // 2 + int(8 * self.ui_scale),
        )
        return rect

    def _near_flower(self):
        return abs(self.knight.x - self.flower_x) <= int(170 * self.ui_scale)

    def _begin_gem_puzzle(self):
        if not self.flower_used:
            self._show_notice(
                "Tìm Magic Flower rồi hấp thụ sức mạnh trước khi đi sâu hơn."
            )
            return
        self._set_phase("gem_puzzle")
        self.gem_puzzle = DragonCave1Scene(
            self.game,
            on_solved=self._begin_boss_dialogue,
        )

    def _begin_boss_dialogue(self):
        self.game_state.dragon_cave_puzzle_solved = True
        self._set_phase("dialogue")
        self.dialogue_index = 0
        self.camera_x = 0
        self.knight.target = None
        self.knight.x = int(105 * self.ui_scale)
        self.knight.y = self.height - int(235 * self.ui_scale)
        self.dragon.play_idle()

    def _begin_fire_attack(self):
        self._set_phase("fire_attack")
        self.fire_timer = 0.0
        self.dragon.play_fire_attack()

    def _begin_battle(self):
        self._set_phase("battle")
        self.battle = self._make_puzzle()
        self.puzzle = self.battle

    def _begin_rescue(self):
        self._set_phase("rescue")
        self.dialogue_index = 0
        self.rescue_ready = False
        self.knight.target = None
        self.knight.x = int(115 * self.ui_scale)
        self.knight.y = self.height - int(235 * self.ui_scale)
        self.knight.move_to(int(self.width * 0.56), self.knight.y)
        self.dragon.play_idle()

    def _finish_rescue(self):
        self.game_state.princess_saved = True
        self.game_state.complete_puzzle("dragon_cave")
        self.game_state.ending = "princess_rescued"
        self._set_phase("completed")
        self.game.change_scene("world_map")

    def handle_event(self, event):
        if super().handle_event(event):
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.phase == "explore":
            self._handle_explore_click(event.pos)
        elif self.phase == "gem_puzzle" and self.gem_puzzle is not None:
            self.gem_puzzle.handle_event(event)
        elif self.phase == "dialogue":
            self.dialogue_index += 1
            if self.dialogue_index >= len(self.DIALOGUE):
                self._begin_fire_attack()
        elif self.phase == "battle":
            self.battle.handle_event(event)
        elif self.phase == "retry":
            if self.retry_button.collidepoint(event.pos):
                self._begin_battle()
            elif self.leave_button.collidepoint(event.pos):
                self.game.change_scene("world_map")
        elif self.phase == "rescue" and self.rescue_ready:
            self.dialogue_index += 1
            if self.dialogue_index >= len(self.RESCUE_DIALOGUE):
                self._finish_rescue()
        elif self.phase == "completed":
            self.game.change_scene("world_map")

    def _handle_explore_click(self, position):
        if self.knight.target is not None:
            return

        if not self.flower_visible:
            flower_hitbox = pygame.Rect(0, 0, 0, 0)
        else:
            flower_hitbox = self._flower_rect().move(-self.camera_x, 0).inflate(
                int(32 * self.ui_scale), int(32 * self.ui_scale)
            )
        if flower_hitbox.collidepoint(position):
            if self.flower_used:
                self._show_notice("Magic Flower đã được sử dụng.")
            elif self._near_flower():
                self._use_magic_flower()
            else:
                flower_target = max(0, self.flower_x - int(105 * self.ui_scale))
                self.knight.move_to(flower_target, self.knight.y)
                self._show_notice("Hiệp sĩ đang tiến đến Magic Flower.", 2.5)
            return

        if position[1] < self.height * 0.42:
            return

        world_target_x = max(
            0,
            min(self.world_width - self.explore_player_size[0], position[0] + self.camera_x),
        )
        if world_target_x >= self.exit_x and not self.flower_used:
            self._show_notice("Hãy tìm và dùng Magic Flower trước khi đi sâu hơn.")
            return
        self.knight.move_to(world_target_x, self.knight.y)
        if world_target_x >= self.exit_x - int(30 * self.ui_scale):
            self._show_notice("Lối vào sâu trong hang đang ở phía trước.", 2.0)

    def _use_magic_flower(self):
        self.flower_used = True
        self.game_state.dragon_cave_flower_used = True
        self.game_state.heal(self.game_state.max_health)
        self.interaction_timer = 0.9
        self.flower_glow_timer = 1.4
        self.after_flower_timer = 3.0
        self.knight.move_to(self.exit_x, self.knight.y)
        self._show_notice(
            "Magic Flower đã hồi phục toàn bộ sinh lực! Hiệp sĩ tiếp tục tiến sâu vào hang...",
            3.0,
        )

    def update(self, dt):
        if self.inventory_open:
            return

        if self.phase == "explore":
            if self.knight.target is not None:
                self.explore_elapsed += dt
            if self.explore_elapsed >= 3.0:
                self.flower_visible = True
            self.knight.update(dt)
            max_camera = max(0, self.world_width - self.width)
            self.camera_x = max(
                0,
                min(max_camera, self.knight.x - self.width * 0.40),
            )
            self.flower_glow_timer = max(0, self.flower_glow_timer - dt)
            self.interaction_timer = max(0, self.interaction_timer - dt)
            if self.notice_timer > 0:
                self.notice_timer = max(0, self.notice_timer - dt)
            if self.after_flower_timer > 0:
                self.after_flower_timer = max(0.0, self.after_flower_timer - dt)
                if self.after_flower_timer <= 0:
                    self._set_phase("white_transition")
                    self.white_transition_alpha = 0
            if self._near_flower() and not self.flower_used and self.flower_visible:
                self.explore_notice = "Nhấn vào hoa để hấp thụ sức mạnh ma thuật."
                self.notice_timer = 0
            if self.after_flower_timer <= 0 and self.knight.target is None and self.knight.x >= self.exit_x:
                if self.flower_used:
                    self._begin_gem_puzzle()
                else:
                    self._show_notice("Hãy tìm và dùng Magic Flower trước khi đi sâu hơn.")
        elif self.phase == "white_transition":
            self.white_transition_alpha = min(
                255,
                self.white_transition_alpha + int(255 * dt / self.white_transition_duration),
            )
            if self.white_transition_alpha >= 255:
                self._begin_gem_puzzle()
        elif self.phase == "gem_puzzle" and self.gem_puzzle is not None:
            self.gem_puzzle.update(dt)
        elif self.phase == "fire_attack":
            self.fire_timer += dt
            self.dragon.update(dt)
            if self.fire_timer >= 0.75 and self.dragon.is_animation_finished():
                self.dragon.play_idle()
                self._begin_battle()
        elif self.phase == "battle":
            self.battle.update(dt)
            if self.battle.win:
                self._begin_rescue()
            elif self.battle.game_over and self.game_state.health > 0:
                self._set_phase("retry")
        elif self.phase == "rescue":
            self.knight.update(dt)
            if self.knight.target is None:
                self.rescue_ready = True
        elif self.phase == "completed" and self.notice_timer > 0:
            self.notice_timer = max(0, self.notice_timer - dt)

    def draw(self, screen):
        if self.phase == "explore":
            self._draw_exploration(screen)
        elif self.phase == "white_transition":
            self._draw_exploration(screen)
            white_overlay = pygame.Surface((self.width, self.height))
            white_overlay.fill((255, 255, 255))
            white_overlay.set_alpha(self.white_transition_alpha)
            screen.blit(white_overlay, (0, 0))
        elif self.phase == "gem_puzzle" and self.gem_puzzle is not None:
            self.gem_puzzle.draw(screen)
        elif self.phase in ("dialogue", "fire_attack"):
            self._draw_inner_cave(screen)
            if self.phase == "dialogue":
                self._draw_dialogue(screen, self.DIALOGUE, self.dialogue_index)
        elif self.phase == "battle":
            self.battle.draw()
        elif self.phase == "retry":
            self.battle.draw()
            self._draw_retry_prompt(screen)
        elif self.phase in ("rescue", "completed"):
            self._draw_rescue(screen)
        super().draw(screen)

    def _draw_exploration(self, screen):
        screen.blit(self.exploration_background, (-round(self.camera_x), 0))
        floor_y = self.floor_y
        flower_rect = self._flower_rect().move(-round(self.camera_x), 0)
        if not self.flower_used and self.flower_visible:
            pulse = 5 + int(4 * (1 + pygame.time.get_ticks() % 900 / 900))
            glow = pygame.Surface(
                (flower_rect.width + 70, flower_rect.height + 70),
                pygame.SRCALPHA,
            )
            pygame.draw.ellipse(
                glow,
                (116, 121, 255, 50),
                glow.get_rect().inflate(-pulse * 2, -pulse * 2),
            )
            screen.blit(glow, glow.get_rect(center=flower_rect.center))
            screen.blit(self.flower_image, flower_rect)

        self._draw_knight_at(
            screen,
            self.knight.x - self.camera_x,
            self.knight.y,
            self.explore_player_size,
        )
        if not self.flower_used and self.flower_visible and self._near_flower():
            self.explore_notice = "Nhấn vào hoa để hấp thụ sức mạnh ma thuật."
        elif self.flower_used and self.notice_timer <= 0:
            self.explore_notice = "Nhấp vào lối đi để tiến sâu vào hang."
        if self.explore_notice:
            self._draw_hint(screen, self.explore_notice)

    def _draw_inner_cave(self, screen):
        screen.blit(self.cave_background, (0, 0))
        screen.blit(self.inner_darkness, (0, 0))
        dragon_position = (int(self.width * 0.55), int(self.height * 0.04))
        dragon_size = (int(self.height * 0.80), int(self.height * 0.80))
        self.dragon.draw(screen, dragon_position, dragon_size)
        knight_size = (int(self.height * 0.30), int(self.height * 0.42))
        self._draw_knight_at(
            screen,
            int(self.width * 0.10),
            self.height - knight_size[1] - int(24 * self.ui_scale),
            knight_size,
        )

    def _draw_rescue(self, screen):
        screen.blit(self.cave_background, (0, 0))
        screen.blit(self.inner_darkness, (0, 0))
        dragon_frame = self.dragon.animation.get_current_frame()
        if dragon_frame is not None:
            defeated_dragon = pygame.transform.smoothscale(
                self.dragon_defeated_image,
                (int(self.height * 0.52), int(self.height * 0.52)),
            )
            defeated_dragon.set_alpha(95)
            screen.blit(
                defeated_dragon,
                (int(self.width * 0.60), int(self.height * 0.34)),
            )
        princess_center = (int(self.width * 0.78), int(self.height * 0.72))
        self.princess.draw(screen, princess_center, self.ui_scale)
        knight_size = (int(self.height * 0.30), int(self.height * 0.42))
        self._draw_knight_at(
            screen,
            self.knight.x,
            self.knight.y,
            knight_size,
        )
        if self.rescue_ready:
            self._draw_dialogue(
                screen,
                self.RESCUE_DIALOGUE,
                self.dialogue_index,
            )
        elif self.phase == "completed":
            self._draw_hint(screen, "Công chúa đã được giải cứu. Hành trình hoàn tất!")

    def _draw_knight_at(self, screen, x, y, size):
        frame = self.knight.animation.get_current_frame()
        if frame is None:
            return
        cache_key = (id(frame), size)
        image = self._scaled_knight_cache.get(cache_key)
        if image is None:
            image = pygame.transform.smoothscale(frame, size)
            self._scaled_knight_cache[cache_key] = image
        screen.blit(image, (round(x), round(y)))

    def _draw_dialogue(self, screen, lines, index):
        box = STANDARD_DIALOG_RECT.copy()
        box.width = min(box.width, self.width - 48)
        box.centerx = self.width // 2
        draw_dialogue_frame(screen, box)
        speaker, text = lines[min(index, len(lines) - 1)]
        speaker_image = self._title_font.render(speaker, True, (112, 65, 34))
        screen.blit(speaker_image, (box.x + 24, box.y + 14))
        self._draw_wrapped_text(
            screen,
            text,
            self._font,
            (55, 42, 31),
            pygame.Rect(box.x + 25, box.y + 56, box.width - 50, box.height - 72),
        )
        prompt = self._small_font.render("Nhấp để tiếp tục", True, (112, 75, 42))
        screen.blit(prompt, prompt.get_rect(right=box.right - 16, bottom=box.bottom - 10))

    def _draw_hint(self, screen, text):
        box = pygame.Rect(
            int(24 * self.ui_scale),
            self.height - int(86 * self.ui_scale),
            int(self.width * 0.48),
            int(64 * self.ui_scale),
        )
        draw_dialogue_frame(screen, box)
        self._draw_wrapped_text(screen, text, self._small_font, (55, 42, 31), box.inflate(-24, -14))

    def _draw_wrapped_text(self, screen, text, font, color, rect):
        lines = []
        current = ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if current and font.size(candidate)[0] > rect.width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        line_height = font.get_linesize()
        total_height = line_height * len(lines)
        y = rect.centery - total_height // 2
        for line in lines:
            image = font.render(line, True, color)
            screen.blit(image, image.get_rect(centerx=rect.centerx, top=y))
            y += line_height

    def _draw_retry_prompt(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        box = pygame.Rect(
            self.width // 2 - int(250 * self.ui_scale),
            self.height // 2 - int(90 * self.ui_scale),
            int(500 * self.ui_scale),
            int(200 * self.ui_scale),
        )
        draw_dialogue_frame(screen, box)
        title_image = self._title_font.render("Trận đấu kết thúc", True, (89, 55, 30))
        screen.blit(title_image, title_image.get_rect(center=(box.centerx, box.y + 40)))
        message = self._small_font.render(
            "Hiệp sĩ còn máu. Bạn có thể thử thách rồng lần nữa.",
            True,
            (55, 42, 31),
        )
        screen.blit(message, message.get_rect(center=(box.centerx, box.y + 82)))
        button_y = box.bottom - int(60 * self.ui_scale)
        self.retry_button = pygame.Rect(
            box.x + int(24 * self.ui_scale),
            button_y,
            int(210 * self.ui_scale),
            int(42 * self.ui_scale),
        )
        self.leave_button = pygame.Rect(
            box.right - int(234 * self.ui_scale),
            button_y,
            int(210 * self.ui_scale),
            int(42 * self.ui_scale),
        )
        self._draw_button(screen, self.retry_button, "Đánh lại")
        self._draw_button(screen, self.leave_button, "Về bản đồ")

    def _draw_button(self, screen, rect, label):
        pygame.draw.rect(screen, (119, 77, 44), rect, border_radius=7)
        pygame.draw.rect(screen, (210, 169, 97), rect, 2, border_radius=7)
        image = self._small_font.render(label, True, (255, 239, 198))
        screen.blit(image, image.get_rect(center=rect.center))
