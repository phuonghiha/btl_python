"""Dialogue, rules, and frog duel that follow the swamp crossing."""

import os
import random

import pygame


FINAL_PLAYER_SIZE = (160, 218)
FINAL_FROG_SIZE = (180, 180)
PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
TITLE_FONT_PATH = os.path.join(
    PROJECT_DIR, "assets", "fonts", "TuyetSac-Bold.otf"
)
CONTENT_FONT_PATH = os.path.join(
    PROJECT_DIR, "assets", "fonts", "UVNAiCapNang.TTF"
)
PAPER = (240, 222, 181)
BORDER = (104, 69, 43)
KNIGHT_TEXT = (184, 134, 11)
FROG_TEXT = (40, 115, 68)


class SwampPuzzle:
    """Own the second swamp puzzle's dialogue, tutorial, duel, and overlay."""

    def __init__(self, player, frog, game_state, screen):
        self.player = player
        self.frog = frog
        self.game_state = game_state
        self.screen = screen

        self.dialogue_name_font = pygame.font.Font(TITLE_FONT_PATH, 23)
        self.dialogue_font = pygame.font.Font(CONTENT_FONT_PATH, 20)
        self.dialogue_button_font = pygame.font.Font(CONTENT_FONT_PATH, 17)

        self._stage = None
        self._speaker = "frog"
        self._animation_timer = 0.0
        self._damage_applied = False
        self._knockback = None
        self._victory_retreat = None
        self._quit = False
        self._reunion_pending = False
        self._current_number = 0
        self._target_number = None
        self._max_numbers_per_turn = None
        self._last_call = []
        self._last_caller = ""
        self._frog_call_text = ""

    @property
    def active(self):
        return self._stage is not None

    @property
    def quit(self):
        return self._quit

    @property
    def reunion_pending(self):
        return self._reunion_pending

    def show_reunion(self):
        """Show the frog's greeting after the player returns from the map."""
        if not self._reunion_pending:
            return
        self._reunion_pending = False
        self._quit = False
        self._stage = "reunion"
        self._speaker = "frog"
        self._animation_timer = 0.0
        self.frog.idle()

    def start(self):
        self._roll_round_settings()
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2
        self.player.x = center_x - 235
        self.player.y = center_y - FINAL_PLAYER_SIZE[1] // 2
        self.player.direction = "right"
        self.player.animation.play("turn_right")
        self.frog.x = center_x + 45
        self.frog.y = center_y - FINAL_FROG_SIZE[1] // 2
        self.frog.turn_left()
        self._start_dialogue("opening_frog")

    def _roll_round_settings(self):
        self._target_number = random.randint(20, 36)
        self._max_numbers_per_turn = random.choice((3, 4, 5))

    def _start_dialogue(self, stage):
        self._stage = stage
        if stage in ("opening_knight", "defeat_line"):
            self._speaker = "knight"
        else:
            self._speaker = "frog"

    def _dialogue_text(self):
        return {
            "opening_frog": "Muốn đoạt Thánh Kiếm ư? Ha! Trước hết, hãy chứng tỏ bản lĩnh của ngươi!",
            "opening_knight": "Ta xin nhận lời. Hãy chuẩn bị cho trận đấu!",
            "defeat_line": "Ta... đã thua rồi!",
            "loss_offer": "Ha ha! Lại thêm một lần bại trận! Ngươi còn muốn tái đấu với ta chăng?",
            "abandon_notice": "Ngươi vẫn chưa có được Thánh Kiếm! Hãy thử thách Ếch Quái Vật một lần nữa để giành lấy thanh kiếm huyền thoại, hoặc tạm rời đầm lầy để khám phá những vùng đất khác. Khi đã chuẩn bị sẵn sàng, hãy quay lại đây!",
            "reunion": "Kẻ thù cũ, ngươi lại trở về rồi! Muốn có được Thánh Kiếm, hãy đánh bại ta trong trận đếm số. Ngươi đã sẵn sàng đối mặt với thử thách chưa?",
            "victory": "Ta đã bại. Thánh Kiếm giờ thuộc về ngươi.",
            "frog_speaking": self._frog_call_text,
        }.get(self._stage, "")

    @staticmethod
    def _wrap_text(font, text, max_width):
        lines = []
        current = ""
        for word in text.split():
            candidate = word if not current else f"{current} {word}"
            if current and font.size(candidate)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines or [""]

    def _bubble_layout(self):
        screen_width, screen_height = self.screen.get_size()
        width = min(320, screen_width - 32)
        lines = self._wrap_text(
            self.dialogue_font, self._dialogue_text(), width - 36
        )
        offer = self._stage in ("loss_offer", "abandon_notice", "reunion")
        has_continue = self._stage in (
            "opening_frog", "opening_knight", "victory"
        )
        button_height = 42 if offer or has_continue else 0
        height = 62 + len(lines) * 27 + button_height

        if self._speaker == "knight":
            x = 16
            speaker_rect = pygame.Rect(
                int(self.player.x), int(self.player.y), *FINAL_PLAYER_SIZE
            )
        else:
            x = screen_width - width - 16
            speaker_rect = pygame.Rect(
                int(self.frog.x), int(self.frog.y), *FINAL_FROG_SIZE
            )

        x = max(8, min(screen_width - width - 8, x))
        y = max(122, min(
            speaker_rect.centery - height // 2,
            screen_height - height - 16,
        ))
        rect = pygame.Rect(x, y, width, height)

        buttons = {}
        if has_continue:
            buttons["continue"] = pygame.Rect(
                rect.centerx - 80, rect.bottom - 48, 160, 34
            )
        elif offer:
            button_width = (width - 54) // 2
            buttons["rematch"] = pygame.Rect(
                rect.x + 18, rect.bottom - 48, button_width, 34
            )
            buttons["quit"] = pygame.Rect(
                rect.right - 18 - button_width,
                rect.bottom - 48,
                button_width,
                34,
            )
        return rect, lines, buttons, speaker_rect

    def _rules_layout(self):
        width, height = self.screen.get_size()
        panel = pygame.Rect(
            24, 0, min(680, width - 48), min(400, height - 150)
        )
        panel.center = (width // 2, height // 2)
        button = pygame.Rect(panel.centerx - 145, panel.bottom - 64, 290, 44)
        return panel, button

    def _choice_layout(self):
        width, height = self.screen.get_size()
        button_width, button_height, gap = 220, 54, 24
        left = width // 2 - button_width - gap // 2
        top = height - button_height - 34
        return (
            pygame.Rect(left, top, button_width, button_height),
            pygame.Rect(
                left + button_width + gap, top, button_width, button_height
            ),
        )

    def _count_button_rects(self):
        width, height = self.screen.get_size()
        button_width, button_height, gap = 96, 46, 8
        count = self._max_numbers_per_turn
        left = width // 2 - (count * button_width + (count - 1) * gap) // 2
        top = height - 87
        return tuple(
            pygame.Rect(
                left + i * (button_width + gap), top,
                button_width, button_height,
            )
            for i in range(count)
        )

    def _start_counting_game(self, knight_goes_first):
        self._current_number = 0
        self._last_call = []
        self._damage_applied = False
        if knight_goes_first:
            self._stage = "knight_turn"
            self._speaker = "knight"
        else:
            self._stage = "frog_turn"
            self._speaker = "frog"
            self._animation_timer = 0.8

    def _prepare_rematch(self):
        """Reset round and failed-animation state without restoring lost HP."""
        self._roll_round_settings()
        self._current_number = 0
        self._last_call = []
        self._last_caller = ""
        self._frog_call_text = ""
        self._damage_applied = False
        self._animation_timer = 0.0
        self._knockback = None
        self._victory_retreat = None
        self._quit = False
        self._reunion_pending = False

        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2
        self.player.x = center_x - 235
        self.player.y = center_y - FINAL_PLAYER_SIZE[1] // 2
        self.player.direction = "right"
        self.player.animation.play("turn_right")
        self.frog.x = center_x + 45
        self.frog.y = center_y - FINAL_FROG_SIZE[1] // 2
        self.frog.turn_left()
        self._stage = "rules"
        self._speaker = "frog"

    def _read_numbers(self, speaker, count):
        last_number = min(self._target_number, self._current_number + count)
        self._last_call = list(range(self._current_number + 1, last_number + 1))
        self._current_number = last_number
        self._last_caller = "ẾCH" if speaker == "frog" else "HIỆP SĨ"
        if speaker == "frog":
            self._frog_call_text = "Ếch cất tiếng: " + ", ".join(map(str, self._last_call))

    def _get_frog_move(self):
        """Choose a legal winning move when one exists.

        With a maximum of M numbers per turn, a position is losing for the
        player to move exactly when the remaining distance is divisible by
        M + 1. Otherwise, leave that multiple for the knight. In a losing
        position every legal move gives the opponent a winning position, so
        take one number as a simple legal fallback.
        """
        remaining = self._target_number - self._current_number
        max_numbers = min(self._max_numbers_per_turn, remaining)
        if max_numbers < 1:
            raise ValueError("The frog cannot move after the target is reached")

        winning_count = remaining % (self._max_numbers_per_turn + 1)
        if 1 <= winning_count <= max_numbers:
            return winning_count
        return 1

    def handle_event(self, position):
        if self._stage in ("opening_frog", "opening_knight"):
            _, _, buttons, _ = self._bubble_layout()
            if buttons.get("continue", pygame.Rect(0, 0, 0, 0)).collidepoint(position):
                self._stage = (
                    "opening_knight"
                    if self._stage == "opening_frog"
                    else "rules"
                )
                self._speaker = "knight"
            return

        if self._stage == "rules":
            _, button = self._rules_layout()
            if button.collidepoint(position):
                self._stage = "choose"
            return

        if self._stage == "choose":
            first, second = self._choice_layout()
            if first.collidepoint(position):
                self._start_counting_game(knight_goes_first=True)
            elif second.collidepoint(position):
                self._start_counting_game(knight_goes_first=False)
            return

        if self._stage == "knight_turn":
            for count, button in enumerate(self._count_button_rects(), start=1):
                if button.collidepoint(position):
                    self._read_numbers("knight", count)
                    break
            else:
                return
            if self._current_number >= self._target_number:
                self.player.attack()
                self._stage = "knight_victory_attack"
                self._animation_timer = 0.45
            else:
                self._stage = "frog_turn"
                self._speaker = "frog"
                self._animation_timer = 0.8
            return

        if self._stage == "loss_offer":
            _, _, buttons, _ = self._bubble_layout()
            if buttons["rematch"].collidepoint(position):
                self._prepare_rematch()
            elif buttons["quit"].collidepoint(position):
                self._stage = "abandon_notice"
                self._speaker = "frog"
            return

        if self._stage == "abandon_notice":
            _, _, buttons, _ = self._bubble_layout()
            if buttons["rematch"].collidepoint(position):
                self._prepare_rematch()
            elif buttons["quit"].collidepoint(position):
                self._stage = None
                self._quit = True
                self._reunion_pending = True
            return

        if self._stage == "reunion":
            _, _, buttons, _ = self._bubble_layout()
            if buttons["rematch"].collidepoint(position):
                self._prepare_rematch()
            elif buttons["quit"].collidepoint(position):
                self._stage = None
                self._quit = True
                self._reunion_pending = True
            return

        if self._stage == "victory":
            _, _, buttons, _ = self._bubble_layout()
            if buttons["continue"].collidepoint(position):
                self._stage = None
                self._quit = True

    def _begin_defeat(self):
        self._stage = "defeat_line"
        self._speaker = "knight"
        self._animation_timer = 0.8
        if not self._damage_applied:
            self.game_state.take_damage(20)
            self._damage_applied = True

    def update(self, dt):
        if self._reunion_pending:
            self.show_reunion()

        if not self.active:
            return

        self.player.update(dt)
        self._animation_timer = max(0, self._animation_timer - dt)

        if self._stage == "frog_turn" and self._animation_timer == 0:
            count = self._get_frog_move()
            self._read_numbers("frog", count)
            if self._current_number >= self._target_number:
                self._begin_defeat()
            else:
                self._stage = "frog_speaking"
                self._speaker = "frog"
                self._animation_timer = 0.9
        elif self._stage == "frog_speaking" and self._animation_timer == 0:
            self._stage = "knight_turn"
            self._speaker = "knight"
        elif self._stage == "defeat_line" and self._animation_timer == 0:
            self.frog.attack()
            self._stage = "defeat_attack"
            self._animation_timer = 0.8
            self._knockback = {
                "start_x": self.player.x,
                "target_x": max(12, self.player.x - 90),
                "elapsed": 0.0,
                "duration": 0.8,
            }
        elif self._stage == "defeat_attack":
            motion = self._knockback
            motion["elapsed"] += dt
            progress = min(motion["elapsed"] / motion["duration"], 1.0)
            self.player.x = (
                motion["start_x"]
                + (motion["target_x"] - motion["start_x"]) * progress
            )
            if self._animation_timer == 0:
                self._knockback = None
                self._stage = "loss_offer"
                self._speaker = "frog"
        elif self._stage == "knight_victory_attack" and self._animation_timer == 0:
            self._stage = "frog_retreat"
            self._victory_retreat = {
                "start_x": self.frog.x,
                "target_x": min(
                    self.screen.get_width() - FINAL_FROG_SIZE[0] - 8,
                    self.frog.x + 100,
                ),
                "elapsed": 0.0,
                "duration": 0.65,
            }
        elif self._stage == "frog_retreat":
            motion = self._victory_retreat
            motion["elapsed"] += dt
            progress = min(motion["elapsed"] / motion["duration"], 1.0)
            self.frog.x = (
                motion["start_x"]
                + (motion["target_x"] - motion["start_x"]) * progress
            )
            if progress >= 1.0:
                self._victory_retreat = None
                self._stage = "victory"
                self._speaker = "frog"

    def _draw_button(self, screen, rect, label, emphasized=False):
        fill = (211, 177, 111) if emphasized else (232, 211, 164)
        pygame.draw.rect(screen, fill, rect, border_radius=9)
        pygame.draw.rect(screen, BORDER, rect, 2, border_radius=9)
        text = self.dialogue_button_font.render(label, True, (55, 42, 27))
        screen.blit(text, text.get_rect(center=rect.center))

    def draw(self, screen):
        stage = self._stage
        if stage is None:
            return

        if stage == "rules":
            self._draw_rules(screen)
        elif stage == "choose":
            first, second = self._choice_layout()
            prompt = self.dialogue_font.render(
                f"Ván này đếm đến {self._target_number}; mỗi lượt đọc tối đa {self._max_numbers_per_turn} số. Ngươi chọn đi trước hay đi sau?", True, PAPER
            )
            screen.blit(prompt, prompt.get_rect(center=(
                screen.get_width() // 2, first.y - 28
            )))
            self._draw_button(screen, first, "ĐI TRƯỚC", emphasized=True)
            self._draw_button(screen, second, "ĐI SAU")
        elif stage in ("knight_victory_attack", "frog_retreat"):
            return
        elif stage in ("knight_turn", "frog_turn", "frog_speaking"):
            self._draw_counting_game(screen)
            if stage == "frog_speaking":
                self._draw_bubble(screen)
        else:
            self._draw_bubble(screen)

    def _draw_rules(self, screen):
        veil = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 145))
        screen.blit(veil, (0, 0))
        panel, button = self._rules_layout()
        pygame.draw.rect(screen, (28, 20, 13), panel.move(0, 6), border_radius=16)
        pygame.draw.rect(screen, PAPER, panel, border_radius=16)
        pygame.draw.rect(screen, BORDER, panel, 4, border_radius=16)
        title = self.dialogue_name_font.render("LUẬT ĐẤU", True, (52, 39, 27))
        screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.y + 24)))
        rules = (
            f"Ván này đếm đến {self._target_number}. Mỗi lượt, mỗi bên được đọc tối đa {self._max_numbers_per_turn} số liên tiếp. "
            "Hãy chọn đi trước hoặc đi sau. Ai đọc đến con số đích trước sẽ thắng."
        )
        lines = self._wrap_text(self.dialogue_font, rules, panel.width - 64)
        y = panel.y + 82
        for line in lines:
            text = self.dialogue_font.render(line, True, (52, 39, 27))
            screen.blit(text, (panel.x + 32, y))
            y += 31
        self._draw_button(screen, button, "ĐÃ HIỂU – TIẾP TỤC", emphasized=True)

    def _draw_bubble(self, screen):
        rect, lines, buttons, speaker_rect = self._bubble_layout()
        pygame.draw.rect(screen, (20, 16, 12), rect.move(0, 5), border_radius=14)

        if self._speaker == "knight":
            tail = [
                (rect.right - 3, rect.centery - 13),
                (rect.right - 3, rect.centery + 13),
                (speaker_rect.left - 3, speaker_rect.centery),
            ]
        else:
            tail = [
                (rect.left + 3, rect.centery - 13),
                (rect.left + 3, rect.centery + 13),
                (speaker_rect.right + 3, speaker_rect.centery),
            ]
        pygame.draw.polygon(screen, BORDER, tail)
        pygame.draw.polygon(screen, PAPER, tail)
        pygame.draw.rect(screen, PAPER, rect, border_radius=14)
        pygame.draw.rect(screen, BORDER, rect, 3, border_radius=14)

        name, color = (
            ("CHƯA LẤY ĐƯỢC THÁNH KIẾM", BORDER)
            if self._stage == "abandon_notice"
            else
            ("HIỆP SĨ", KNIGHT_TEXT)
            if self._speaker == "knight"
            else ("ẾCH", FROG_TEXT)
        )
        name_font = (
            pygame.font.Font(TITLE_FONT_PATH, 18)
            if self._stage == "abandon_notice"
            else self.dialogue_name_font
        )
        screen.blit(name_font.render(name, True, color),
                    (rect.x + 18, rect.y + 12))
        text_y = rect.y + 43
        for line in lines:
            screen.blit(self.dialogue_font.render(line, True, color),
                        (rect.x + 18, text_y))
            text_y += 27

        if "continue" in buttons:
            self._draw_button(screen, buttons["continue"], "TIẾP TỤC", True)
        if "rematch" in buttons:
            if self._stage == "abandon_notice":
                self._draw_button(screen, buttons["rematch"], "ĐẤU TIẾP", True)
                self._draw_button(screen, buttons["quit"], "ĐI NƠI KHÁC")
            elif self._stage == "reunion":
                self._draw_button(screen, buttons["rematch"], "ĐẤU", True)
                self._draw_button(screen, buttons["quit"], "ĐỂ SAU")
            else:
                self._draw_button(screen, buttons["rematch"], "ĐẤU TIẾP", True)
                self._draw_button(screen, buttons["quit"], "BỎ CUỘC")

    def _draw_counting_game(self, screen):
        panel = pygame.Rect(screen.get_width() // 2 - 285, 486, 570, 172)
        pygame.draw.rect(screen, (25, 20, 15), panel.move(0, 5), border_radius=14)
        pygame.draw.rect(screen, PAPER, panel, border_radius=14)
        pygame.draw.rect(screen, BORDER, panel, 3, border_radius=14)
        number = self.dialogue_name_font.render(
            f"ĐANG ĐẾM: {self._current_number} / {self._target_number}", True, (52, 39, 27)
        )
        screen.blit(number, number.get_rect(center=(panel.centerx, panel.y + 34)))
        if self._last_call:
            last_text = self.dialogue_font.render(
                f"{self._last_caller} vừa xướng: " + ", ".join(map(str, self._last_call)),
                True, (52, 39, 27),
            )
            screen.blit(last_text, last_text.get_rect(center=(panel.centerx, panel.y + 75)))
        if self._stage == "knight_turn":
            for count, button in enumerate(self._count_button_rects(), start=1):
                self._draw_button(screen, button, f"ĐỌC {count} SỐ", count == 1)
        elif self._stage == "frog_turn":
            waiting = self.dialogue_font.render("Ếch đang cân nhắc nước đi...", True, FROG_TEXT)
            screen.blit(waiting, waiting.get_rect(center=(panel.centerx, panel.bottom - 31)))
