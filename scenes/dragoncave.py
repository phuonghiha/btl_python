"""Full Dragon Cave journey, reusing the existing two puzzle modules."""

from pathlib import Path
import math
import random

import pygame

from base_scene import BaseScene, draw_dialogue_frame
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
        
        self._font = content1(23)
        self._small_font = content1(18)
        self._title_font = title(22)
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
        self.end_frame_image = pygame.image.load(
            str(SCENE_ASSETS / "end.png")
        ).convert_alpha()
        frame_width = int(width * 0.62)
        frame_height = int(height * 0.65)
        image_width, image_height = self.end_frame_image.get_size()
        frame_scale = min(
            frame_width / image_width,
            frame_height / image_height,
        )
        self.end_frame_image = pygame.transform.smoothscale(
            self.end_frame_image,
            (
                max(1, int(image_width * frame_scale)),
                max(1, int(image_height * frame_scale)),
            ),
        )
        self.victory_dim_overlay = pygame.Surface(
            (width, height), pygame.SRCALPHA
        )
        self.victory_dim_overlay.fill((0, 0, 0, 92))

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
        self.victory_wait_timer = 0.0
        self.victory_elapsed = 0.0
        self.victory_particle_time = 0.0
        self.victory_particles = self._make_victory_particles()
        self.retry_button = pygame.Rect(0, 0, 0, 0)
        self.leave_button = pygame.Rect(0, 0, 0, 0)
        self.explore_player_size = (
            max(64, int(104 * self.ui_scale)),
            max(84, int(142 * self.ui_scale)),
        )
        self.battle = self._make_puzzle()
        
        self.puzzle = self.battle
        self.gem_puzzle = None
        self.knight = Knight(
            int(90 * self.ui_scale),
            self.floor_y - self.explore_player_size[1],
        )

        if self.game_state.princess_saved:
            self._set_phase("completed")
            self.victory_elapsed = 0.5
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
        
        self.gem_puzzle = None

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
        knight_width = int(self.height * 0.30)
        knight_height = int(self.height * 0.42)
        princess_x = int(self.width * 0.78)
        princess_y = int(self.height * 0.72)
        self.knight.move_to(
            princess_x - knight_width - int(18 * self.ui_scale),
            princess_y - knight_height // 2,
        )
        self.dragon.play_idle()

    def _finish_rescue(self):
        self.game_state.princess_saved = True
        self.game_state.complete_puzzle("dragon_cave")
        self.game_state.ending = "princess_rescued"
        self.rescue_ready = False
        self.victory_wait_timer = 1.5
        self.victory_elapsed = 0.0
        self.victory_particle_time = 0.0
        self._set_phase("victory_wait")

    def _make_victory_particles(self):
        frame_rect = self.end_frame_image.get_rect(center=(self.width // 2, self.height // 2))
        particles = []
        for _ in range(32):
            edge = random.randrange(4)
            along = random.random()
            offset = random.randint(7, 30) * self.ui_scale
            if edge == 0:
                x, y = frame_rect.left + along * frame_rect.width, frame_rect.top - offset
            elif edge == 1:
                x, y = frame_rect.left + along * frame_rect.width, frame_rect.bottom + offset
            elif edge == 2:
                x, y = frame_rect.left - offset, frame_rect.top + along * frame_rect.height
            else:
                x, y = frame_rect.right + offset, frame_rect.top + along * frame_rect.height
            particles.append((x, y, random.uniform(1.5, 3.4) * self.ui_scale, random.random() * 6.283))
        return particles

    
    def handle_event(self, event):
        if self.phase in ("victory_wait", "completed"):
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and (
                    self.map_button_rect.collidepoint(event.pos)
                    or self.restart_button_rect.collidepoint(event.pos)
                )
            ):
                super().handle_event(event)
            return
        if super().handle_event(event):
            return

        
        
        if self.phase == "battle":
            self.battle.handle_event(event)
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

        elif self.phase == "retry":
            if self.retry_button.collidepoint(event.pos):
                self._begin_battle()

            elif self.leave_button.collidepoint(event.pos):
                self.game.change_scene("world_map")

        elif self.phase == "rescue" and self.rescue_ready:
            self.dialogue_index += 1

            if self.dialogue_index >= len(self.RESCUE_DIALOGUE):
                self._finish_rescue()

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
        if self.inventory_open and self.phase not in ("victory_wait", "completed"):
            return

        if self.phase == "victory_wait":
            self.victory_wait_timer = max(0.0, self.victory_wait_timer - dt)
            if self.victory_wait_timer <= 0:
                self._set_phase("completed")
            return
        if self.phase == "completed":
            self.victory_elapsed = min(0.5, self.victory_elapsed + dt)
            self.victory_particle_time += dt
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
        elif self.phase in ("rescue", "victory_wait", "completed"):
            self._draw_rescue(screen)
            if self.phase == "completed":
                self._draw_victory(screen)
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
        dragon_scale = 0.76 if self.phase == "fire_attack" else 0.70
        dragon_size = (
            int(self.height * dragon_scale),
            int(self.height * dragon_scale),
        )
        dragon_floor = self.height - int(118 * self.ui_scale)
        dragon_position = (
            int(self.width * 0.55),
            max(0, dragon_floor - dragon_size[1]),
        )
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
        knight_size = (int(self.height * 0.30), int(self.height * 0.42))
        princess_size = tuple(max(1, int(dimension * 0.85)) for dimension in knight_size)
        self.princess.draw(screen, princess_center, princess_size)
        self._draw_knight_at(
            screen,
            self.knight.x,
            self.knight.y,
            knight_size,
        )
        if self.phase == "rescue" and self.rescue_ready:
            self._draw_rescue_dialogue(
                screen, princess_center, princess_size, knight_size
            )

    def _draw_victory(self, screen):
        fade = max(0, min(255, round(255 * self.victory_elapsed / 0.5)))
        screen.blit(self.victory_dim_overlay, (0, 0))

        frame_rect = self.end_frame_image.get_rect(
            center=(self.width // 2, self.height // 2)
        )
        self.end_frame_image.set_alpha(fade)
        screen.blit(self.end_frame_image, frame_rect)
        self.end_frame_image.set_alpha(255)

        title_font = content1(max(25, int(40 * self.ui_scale)))
        body_font = content1(max(18, int(26 * self.ui_scale)))
        heading = title_font.render("CHIẾN THẮNG", True, (111, 60, 20))
        heading.set_alpha(fade)
        heading_rect = heading.get_rect(
            center=(frame_rect.centerx, frame_rect.top + int(frame_rect.height * 0.40))
        )
        screen.blit(heading, heading_rect)
        trophy_size = max(20, int(34 * self.ui_scale))
        trophy = pygame.Surface((trophy_size, trophy_size), pygame.SRCALPHA)
        gold = (180, 105, 25, fade)
        pygame.draw.polygon(
            trophy,
            gold,
            [
                (int(trophy_size * 0.18), int(trophy_size * 0.12)),
                (int(trophy_size * 0.82), int(trophy_size * 0.12)),
                (int(trophy_size * 0.72), int(trophy_size * 0.60)),
                (trophy_size // 2, int(trophy_size * 0.76)),
                (int(trophy_size * 0.28), int(trophy_size * 0.60)),
            ],
        )
        pygame.draw.arc(
            trophy, gold,
            pygame.Rect(0, int(trophy_size * 0.18), int(trophy_size * 0.36), int(trophy_size * 0.40)),
            -1.2, 1.2, max(2, int(2 * self.ui_scale)),
        )
        pygame.draw.arc(
            trophy, gold,
            pygame.Rect(int(trophy_size * 0.64), int(trophy_size * 0.18), int(trophy_size * 0.36), int(trophy_size * 0.40)),
            1.9, 4.4, max(2, int(2 * self.ui_scale)),
        )
        pygame.draw.rect(
            trophy, gold,
            pygame.Rect(int(trophy_size * 0.44), int(trophy_size * 0.72), int(trophy_size * 0.12), int(trophy_size * 0.16)),
        )
        pygame.draw.rect(
            trophy, gold,
            pygame.Rect(int(trophy_size * 0.30), int(trophy_size * 0.86), int(trophy_size * 0.40), max(2, int(trophy_size * 0.10))),
        )
        trophy_y = heading_rect.centery - trophy_size // 2
        screen.blit(trophy, (heading_rect.left - trophy_size - int(12 * self.ui_scale), trophy_y))
        screen.blit(trophy, (heading_rect.right + int(12 * self.ui_scale), trophy_y))

        congratulation = body_font.render(
            "Chúc mừng hiệp sĩ dũng cảm!", True, (92, 55, 28)
        )
        congratulation.set_alpha(fade)
        screen.blit(
            congratulation,
            congratulation.get_rect(
                center=(frame_rect.centerx, frame_rect.top + int(frame_rect.height * 0.52))
            ),
        )

        message = "Bạn đã đánh bại rồng và giải cứu công chúa thành công!"
        wrapped = self._wrap_dialogue_lines(
            message, body_font, int(frame_rect.width * 0.72)
        )
        line_height = body_font.get_linesize()
        message_center_y = frame_rect.top + int(frame_rect.height * 0.64)
        message_top = message_center_y - len(wrapped) * line_height // 2
        for index, line in enumerate(wrapped):
            text_image = body_font.render(line, True, (92, 55, 28))
            text_image.set_alpha(fade)
            screen.blit(
                text_image,
                text_image.get_rect(
                    center=(
                        frame_rect.centerx,
                        message_top + index * line_height + line_height // 2,
                    )
                ),
            )

        sparkles = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for x, y, radius, phase in self.victory_particles:
            pulse = (math.sin(self.victory_particle_time * 4.0 + phase) + 1) / 2
            alpha = int(fade * (0.25 + 0.75 * pulse))
            center = (round(x), round(y))
            pygame.draw.circle(
                sparkles,
                (255, 220, 125, alpha),
                center,
                max(1, round(radius * (0.7 + 0.6 * pulse))),
            )
            if pulse > 0.72:
                reach = max(2, round(radius * 2.2))
                pygame.draw.line(
                    sparkles,
                    (255, 238, 180, alpha),
                    (center[0] - reach, center[1]),
                    (center[0] + reach, center[1]),
                    1,
                )
                pygame.draw.line(
                    sparkles,
                    (255, 238, 180, alpha),
                    (center[0], center[1] - reach),
                    (center[0], center[1] + reach),
                    1,
                )
        screen.blit(sparkles, (0, 0))

    def _draw_rescue_dialogue(
        self, screen, princess_center, princess_size, knight_size
    ):
        speaker, text = self.RESCUE_DIALOGUE[
            min(self.dialogue_index, len(self.RESCUE_DIALOGUE) - 1)
        ]
        scale = self.ui_scale
        box_width = int(260 * scale)
        box_height = int(88 * scale)
        gap = int(10 * scale)
        vertical_gap = int(4 * scale)

        if speaker == "Công chúa":
            
            head_x = int(self.knight.x + knight_size[0] * 0.50)
            box_x = min(self.width - box_width - gap, head_x + gap)
            character_top = int(self.knight.y)
        else:
            head_x = int(self.knight.x + knight_size[0] * 0.45)
            box_x = max(gap, head_x - box_width - gap)
            character_top = int(self.knight.y)
        box_y = max(gap, character_top - box_height - vertical_gap)

        box = pygame.Rect(box_x, box_y, box_width, box_height)
        draw_dialogue_frame(screen, box)
        speaker_font = content1(max(18, int(21 * scale)))
        text_font = content1(max(16, int(18 * scale)))
        speaker_image = speaker_font.render(speaker, True, (112, 65, 34))
        screen.blit(speaker_image, (box.x + int(14 * scale), box.y + int(8 * scale)))
        text_rect = pygame.Rect(
            box.x + int(14 * scale),
            box.y + int(38 * scale),
            box.width - int(28 * scale),
            box.height - int(48 * scale),
        )
        self._draw_left_wrapped_text(screen, text, text_font, (55, 42, 31), text_rect)

    def _draw_left_wrapped_text(self, screen, text, font, color, rect):
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
            screen.blit(image, (rect.left, y))
            y += line_height

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
        speaker, text = lines[min(index, len(lines) - 1)]

        scale = self.ui_scale
        knight_size = (int(self.height * 0.30), int(self.height * 0.42))
        dragon_size = int(self.height * 0.70)
        box_width = int((400 if speaker == "Hiệp sĩ" else 420) * scale)
        gap = int(7 * scale)
        padding = max(8, int(14 * scale))
        speaker_font = title(max(15, int(18 * scale)))
        body_font = content1(max(14, int(17 * scale)))
        prompt_font = content1(max(11, int(13 * scale)))
        speaker_image = speaker_font.render(speaker, True, (112, 65, 34))
        prompt = prompt_font.render("Click để tiếp tục", True, (112, 75, 42))
        text_width = box_width - padding * 2
        lines_to_draw = self._wrap_dialogue_lines(text, body_font, text_width)
        line_height = body_font.get_linesize()
        text_top = int(34 * scale)
        text_bottom = int(10 * scale) + prompt.get_height()
        box_height = max(
            int(82 * scale),
            text_top + len(lines_to_draw) * line_height + text_bottom,
        )

        if speaker == "Hiệp sĩ":
            knight_x = int(self.width * 0.10)
            knight_y = self.height - knight_size[1] - int(24 * scale)
            head_x = knight_x + int(knight_size[0] * 0.48)
            box_x = min(self.width - box_width - gap, head_x + gap)
            box_y = max(gap, knight_y - box_height - gap)
        else:
            dragon_x = int(self.width * 0.55)
            dragon_y = max(
                0,
                self.height - int(118 * scale) - dragon_size,
            )
            box_x = max(
                gap,
                dragon_x - box_width - gap + int(24 * scale),
            )
            box_y = dragon_y + int(dragon_size * 0.08)

        box = pygame.Rect(box_x, box_y, box_width, box_height)
        draw_dialogue_frame(screen, box)

        screen.blit(speaker_image, (box.x + padding, box.y + int(8 * scale)))
        text_x = box.x + padding
        text_y = box.y + text_top
        for line_index, line in enumerate(lines_to_draw):
            line_image = body_font.render(line, True, (55, 42, 31))
            screen.blit(
                line_image,
                (text_x, text_y + line_index * line_height),
            )

        screen.blit(
            prompt,
            prompt.get_rect(
                right=box.right - padding,
                bottom=box.bottom - int(8 * scale),
            ),
        )

    @staticmethod
    def _wrap_dialogue_lines(text, font, max_width):
        lines = []
        current = ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if current and font.size(candidate)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines or ["" ]

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
        self._draw_battle_button(screen, self.retry_button, "Đánh lại")
        self._draw_battle_button(screen, self.leave_button, "Về bản đồ")

    def _draw_battle_button(self, screen, rect, label):
        pygame.draw.rect(screen, (119, 77, 44), rect, border_radius=7)
        pygame.draw.rect(screen, (210, 169, 97), rect, 2, border_radius=7)
        image = self._small_font.render(label, True, (255, 239, 198))
        screen.blit(image, image.get_rect(center=rect.center))
