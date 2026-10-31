import pygame
import random
import math
from pathlib import Path
from game_fonts import content1, title


class DragonBlockGame:
    ROWS = 8
    COLS = 8
    CELL = 60
    BOARD_X = 460
    BOARD_Y = 230

    MOVE_TIME = 160
    FALL_TIME = 240
    CLEAR_TIME = 420
    PUSH_TIME = 280
    ATTACK_TIME = 520

    MAX_HP = 100

    # Match each piece color to its fixed length: white=1, green=2,
    # red=3, yellow=4.
    PIECE_TYPES = {
        "white": {"length": 1, "color": (248, 239, 222)},
        "green": {"length": 2, "color": (112, 148, 112)},
        "red": {"length": 3, "color": (198, 64, 50)},
        "yellow": {"length": 4, "color": (255, 190, 48)},
    }
    COLORS = {
        piece_type["length"]: piece_type["color"]
        for piece_type in PIECE_TYPES.values()
    }
    SWORD_DAMAGE = {1: 12, 2: 27, 3: 45, 4: 60}
    NO_SWORD_DAMAGE = {1: 2, 2: 4, 3: 6, 4: 8}
    DRAGON_ATTACK_MISSES = 2
    DRAGON_SHIELD_THRESHOLDS = (70, 50, 30)

    def __init__(self, screen, sword=True, game_state=None):
        self.screen = screen
        self.game_state = game_state
        self.width, self.height = screen.get_size()
        self.ui_scale = min(self.width / 1400, self.height / 900)
        self.CELL = max(40, int(68 * self.ui_scale))
        self.BOARD_X = int(self.width * 0.46 - self.COLS * self.CELL / 2)
        self.BOARD_Y = int(190 * self.ui_scale)
        dragon_image_path = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "images"
            / "sence_4"
            / "dragonchibi.png"
        )
        self.dragon_image = pygame.image.load(
            str(dragon_image_path)
        ).convert_alpha()
        character_size = max(100, int(170 * self.ui_scale))
        self.dragon_image = pygame.transform.smoothscale(
            self.dragon_image,
            (character_size, character_size)
        )
        knight_image_path = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "sprites"
            / "knight"
            / "front"
            / "1.png"
        )
        self.knight_image = pygame.image.load(
            str(knight_image_path)
        ).convert_alpha()
        self.knight_image = pygame.transform.smoothscale(
            self.knight_image,
            (character_size, character_size),
        )
        self.dragon_attack_flash_timer = 0

        self.font_big = title(max(24, int(34 * self.ui_scale)))
        self.font = content1(max(16, int(22 * self.ui_scale)))
        self.font_small = content1(max(13, int(18 * self.ui_scale)))

        self.game_over = False
        self.win = False

        self.knight_hp = min(
            self.MAX_HP,
            getattr(game_state, "health", self.MAX_HP),
        )
        self.dragon_hp = self.MAX_HP

        self.dragon_shield = False
        self.shield_level = None
        self.activated_shield_levels = set()
        self.dragon_defense_done = False

        self.sword = sword

        self.turn = 0
        self.failed_turns = 0
        self.dragon_attacks_received = 0
        self.rows_cleared_this_attack = 0

        self.board = [
            [None for _ in range(self.COLS)]
            for _ in range(self.ROWS)
        ]

        self.next_piece_id = 1

        self.selected_piece = None
        self.drag_offset = 0
        self.drag_current_col = None
        self.drag_mouse_x = None
        self.drag_start_col = None

        self.animation = None

        self.message = "Kéo một khối sang trái/phải để bắt đầu"
        self.message_timer = 0

        self.next_row_preview = []

        self.create_initial_board()

    def new_piece(self, length, row, col, color=None):
        if length not in self.COLORS:
            raise ValueError(f"Unsupported piece length: {length}")

        # The color always follows the length, even when a caller supplies a color.
        color = self.COLORS[length]

        piece = {
            "id": self.next_piece_id,
            "color": color,
            "length": length,
            "cells": [
                (row, col + i)
                for i in range(length)
            ],
        }

        self.next_piece_id += 1

        return piece

    def can_place(self, row, col, length, ignore_id=None):
        if row < 0 or row >= self.ROWS:
            return False

        if col < 0 or col + length > self.COLS:
            return False

        for c in range(col, col + length):
            p = self.board[row][c]

            if p is not None and p["id"] != ignore_id:
                return False

        return True

    def place_piece(self, piece):
        for r, c in piece["cells"]:
            if 0 <= r < self.ROWS and 0 <= c < self.COLS:
                self.board[r][c] = piece

    def rebuild_piece_cells(self):
        pieces = {}

        for r in range(self.ROWS):
            for c in range(self.COLS):
                p = self.board[r][c]

                if p is not None:
                    pieces[p["id"]] = p

        for p in pieces.values():
            p["cells"] = []

        for r in range(self.ROWS):
            for c in range(self.COLS):
                p = self.board[r][c]

                if p is not None:
                    p["cells"].append((r, c))

    def clear_board(self):
        self.board = [
            [None for _ in range(self.COLS)]
            for _ in range(self.ROWS)
        ]

    def create_initial_board(self):
        self.clear_board()

        self.next_piece_id = 1

        starting_pieces = [
            (4, self.ROWS - 1, 0),
            (1, self.ROWS - 1, 6),
            (3, self.ROWS - 2, 0),
            (2, self.ROWS - 2, 5),
        ]
        for length, row, col in starting_pieces:
            self.place_piece(self.new_piece(length, row, col))

        self.rebuild_piece_cells()
        self.apply_gravity()
        self.generate_next_row_preview()

        self.message = "Kéo các khối để hoàn thành một hàng"

    def difficulty(self):
        if self.turn <= 2:
            return [1], 3, 4

        if self.turn <= 5:
            return [1, 2], 3, 4

        if self.turn <= 8:
            return [1, 2, 3], 3, 4

        return [1, 2, 3, 4], 3, 4

    def random_piece_length(self):
        lengths = [1, 2, 3, 4]
        if self.sword:
            weights = [42, 30, 20, 8]
        else:
            weights = [48, 30, 17, 5]
        return random.choices(
            lengths,
            weights=weights,
            k=1
        )[0]

    def generate_next_row_preview(self):
        _, min_count, max_count = self.difficulty()

        target_count = random.randint(
            min_count,
            max_count
        )

        preview = []
        occupied = set()
        tries = 0

        while len(preview) < target_count and tries < 100:
            tries += 1

            length = self.random_piece_length()

            possible = []

            for col in range(
                self.COLS - length + 1
            ):
                valid = True

                for i in range(length):
                    if col + i in occupied:
                        valid = False
                        break

                if valid:
                    possible.append(col)

            if not possible:
                continue

            col = random.choice(possible)

            for i in range(length):
                occupied.add(col + i)

            preview.append({
                "col": col,
                "length": length,
                "color": self.COLORS[length],
            })

        self.next_row_preview = preview

    def create_new_bottom_row(self):
        row = self.ROWS - 1

        self.board[row] = [
            None for _ in range(self.COLS)
        ]

        for item in self.next_row_preview:
            piece = self.new_piece(
                item["length"],
                row,
                item["col"],
                item["color"]
            )

            self.place_piece(piece)

        self.rebuild_piece_cells()

        self.generate_next_row_preview()

    def add_blocks_until_three_rows(self):
        occupied_rows = 0

        for r in range(self.ROWS):
            if any(
                self.board[r][c] is not None
                for c in range(self.COLS)
            ):
                occupied_rows += 1

        if occupied_rows < 3:
            self.create_new_bottom_row()
            self.apply_gravity()

    def get_pieces(self):
        result = {}

        for row in self.board:
            for p in row:
                if p is not None:
                    result[p["id"]] = p

        return list(result.values())

    def get_full_rows(self):
        rows = []

        for r in range(self.ROWS):
            if all(
                self.board[r][c] is not None
                for c in range(self.COLS)
            ):
                rows.append(r)

        return rows

    def calculate_gravity_result(self):
        pieces = self.get_pieces()

        new_positions = {}
        occupied = set()

        pieces.sort(
            key=lambda p: min(
                r for r, _ in p["cells"]
            ),
            reverse=True
        )

        for piece in pieces:
            cells = piece["cells"]

            shift = 0

            while True:
                next_shift = shift + 1
                valid = True

                for r, c in cells:
                    nr = r + next_shift

                    if nr >= self.ROWS:
                        valid = False
                        break

                    if (nr, c) in occupied:
                        valid = False
                        break

                if not valid:
                    break

                shift = next_shift

            moved = [
                (r + shift, c)
                for r, c in cells
            ]

            new_positions[piece["id"]] = moved

            for cell in moved:
                occupied.add(cell)

        return new_positions

    def apply_gravity(self):
        pieces = {}

        for p in self.get_pieces():
            pieces[p["id"]] = p

        new_positions = self.calculate_gravity_result()

        self.board = [
            [None for _ in range(self.COLS)]
            for _ in range(self.ROWS)
        ]

        for pid, cells in new_positions.items():
            p = pieces.get(pid)

            if p is None:
                continue

            p["cells"] = cells

            self.place_piece(p)

        self.rebuild_piece_cells()

    def start_message(self, text, duration=1300):
        self.message = text
        self.message_timer = duration

    def check_top(self):
        for c in range(self.COLS):
            if self.board[0][c] is not None:
                self.game_over = True
                self.win = False
                self.animation = None

                self.start_message(
                    "Các khối đã chạm đỉnh! Bạn thua rồi!",
                    3000
                )

                return True

        return False

    def start_move_animation(
        self,
        piece,
        old_cells,
        new_cells
    ):
        self.animation = {
            "type": "move",
            "time": 0,
            "piece_id": piece["id"],
            "old_cells": old_cells,
            "new_cells": new_cells,
        }

    def start_fall_animation(
        self,
        old_positions,
        new_positions,
        source="normal"
    ):
        self.animation = {
            "type": "fall",
            "time": 0,
            "old_positions": old_positions,
            "new_positions": new_positions,
            "source": source,
        }

    def start_clear_animation(
        self,
        rows,
        source
    ):
        self.animation = {
            "type": "clear",
            "time": 0,
            "rows": rows,
            "source": source,
        }

    def start_push_animation(
        self,
        old_board
    ):
        self.animation = {
            "type": "push",
            "time": 0,
            "old_board": old_board,
        }

    def start_attack_animation(
        self,
        rows,
        source,
        rows_cleared=None
    ):
        row = rows[len(rows) // 2]

        sx = (
            self.BOARD_X
            + self.COLS * self.CELL / 2
        )

        sy = (
            self.BOARD_Y
            + row * self.CELL
            + self.CELL / 2
        )

        ex = (
            self.BOARD_X
            + self.COLS * self.CELL / 2
        )

        ey = self.BOARD_Y - 105

        self.animation = {
            "type": "attack",
            "time": 0,
            "source": source,
            "rows_cleared": rows_cleared or len(rows),
            "start": (sx, sy),
            "end": (ex, ey),
        }

    def move_piece(
        self,
        piece,
        target_col
    ):
        cells = piece["cells"]

        row = cells[0][0]
        start_col = min(c for _, c in cells)

        if not self.can_slide_piece(
            row,
            start_col,
            target_col,
            piece["length"],
            piece["id"]
        ):
            return False

        old_cells = list(cells)

        new_cells = [
            (row, target_col + i)
            for i in range(piece["length"])
        ]

        old_board = [
            r[:]
            for r in self.board
        ]

        for r, c in old_cells:
            self.board[r][c] = None

        if not self.can_place(
            row,
            target_col,
            piece["length"]
        ):
            self.board = old_board
            return False

        piece["cells"] = new_cells

        self.place_piece(piece)
        self.rebuild_piece_cells()

        self.start_move_animation(
            piece,
            old_cells,
            new_cells
        )

        return True

    def can_slide_piece(
        self,
        row,
        start_col,
        target_col,
        length,
        piece_id
    ):
        if not 0 <= target_col <= self.COLS - length:
            return False

        direction = 1 if target_col > start_col else -1
        positions = range(
            start_col + direction,
            target_col + direction,
            direction
        )
        return all(
            self.can_place(row, col, length, piece_id)
            for col in positions
        )

    def player_move_finished(self):
        self.rebuild_piece_cells()

        self.apply_gravity()

        if self.check_top():
            return

        rows = self.get_full_rows()

        if rows:
            self.failed_turns = 0
            self.rows_cleared_this_attack = 0
            self.start_clear_animation(
                rows,
                "player"
            )

            return

        self.failed_turns += 1
        self.finish_player_turn()

    def finish_player_turn(self):
        self.turn += 1

        old_board = [
            r[:]
            for r in self.board
        ]

        self.push_board_up()
        self.create_new_bottom_row()

        self.start_push_animation(
            old_board
        )

    def push_board_up(self):
        new_board = [
            [None for _ in range(self.COLS)]
            for _ in range(self.ROWS)
        ]

        for r in range(1, self.ROWS):
            for c in range(self.COLS):
                new_board[r - 1][c] = self.board[r][c]

        self.board = new_board

        self.rebuild_piece_cells()

    def after_push(self):
        old_positions = {}

        for p in self.get_pieces():
            old_positions[p["id"]] = list(
                p["cells"]
            )

        new_positions = self.calculate_gravity_result()

        moved = False

        for pid in old_positions:
            if old_positions[pid] != new_positions.get(
                pid,
                old_positions[pid]
            ):
                moved = True
                break

        if moved:
            pieces = {
                p["id"]: p
                for p in self.get_pieces()
            }

            for pid, cells in new_positions.items():
                pieces[pid]["cells"] = cells

            self.board = [
                [None for _ in range(self.COLS)]
                for _ in range(self.ROWS)
            ]

            for p in pieces.values():
                self.place_piece(p)

            self.rebuild_piece_cells()

            self.start_fall_animation(
                old_positions,
                new_positions,
                "after_push"
            )

        else:
            self.resolve_after_push()

    def resolve_after_push(self):
        if self.check_top():
            return

        rows = self.get_full_rows()

        if rows:
            self.rows_cleared_this_attack = 0
            self.start_clear_animation(
                rows,
                "player"
            )

            return

        attack_threshold = self.DRAGON_ATTACK_MISSES
        if self.failed_turns >= attack_threshold:
            self.failed_turns = 0
            self.dragon_attack()
            return

        self.start_message(
            "Đến lượt bạn",
            700
        )

    def finish_after_fall(
        self,
        source
    ):
        self.rebuild_piece_cells()

        if self.check_top():
            return

        rows = self.get_full_rows()

        if rows:
            self.start_clear_animation(
                rows,
                "dragon"
                if source == "dragon"
                else "player"
            )

            return

        if source == "dragon":
            self.finish_dragon_attack()
        else:
            self.resolve_after_push()

    def clear_rows(
        self,
        rows
    ):
        rows = set(rows)

        pieces_to_remove = set()

        for r in rows:
            for c in range(self.COLS):
                p = self.board[r][c]

                if p is not None:
                    pieces_to_remove.add(
                        p["id"]
                    )

        for r in range(self.ROWS):
            for c in range(self.COLS):
                p = self.board[r][c]

                if (
                    p is not None
                    and p["id"] in pieces_to_remove
                ):
                    self.board[r][c] = None

        self.rebuild_piece_cells()

        self.apply_gravity()

    def player_attack(self):
        rows_cleared = self.rows_cleared_this_attack
        if rows_cleared <= 0:
            return

        damage_table = self.SWORD_DAMAGE if self.sword else self.NO_SWORD_DAMAGE
        damage = damage_table.get(rows_cleared, max(damage_table.values()))

        if self.dragon_shield:
            blocked_level = self.shield_level
            self.dragon_shield = False
            self.shield_level = None
            self.failed_turns = 0
            self.rows_cleared_this_attack = 0
            self.start_message(
                f"Khiên rồng mốc {blocked_level}% đã chặn đòn!",
                1400,
            )
            return

        old_hp = self.dragon_hp
        next_thresholds = [
            level
            for level in self.DRAGON_SHIELD_THRESHOLDS
            if level not in self.activated_shield_levels and level < old_hp
        ]
        if next_thresholds:
            next_threshold = max(next_thresholds)
            if old_hp - damage < next_threshold:
                damage = old_hp - next_threshold

        self.dragon_hp = max(0, self.dragon_hp - damage)
        self.check_shield_activation(old_hp)

        self.failed_turns = 0
        self.rows_cleared_this_attack = 0

        if self.dragon_hp == 0:
            self.win = True
            self.game_over = True
            if self.game_state is not None:
                self.game_state.dragon_defeated = True
            self.start_message("RỒNG ĐÃ BỊ ĐÁNH BẠI!", 4000)
        elif not self.dragon_shield:
            self.start_message(f"Hiệp sĩ gây {damage} sát thương!", 900)
    def check_shield_activation(
        self,
        old_hp
    ):
        for level in self.DRAGON_SHIELD_THRESHOLDS:
            if (
                old_hp > level >= self.dragon_hp
                and level not in self.activated_shield_levels
            ):
                self.activated_shield_levels.add(level)
                self.dragon_shield = True
                self.shield_level = level
                self.start_message(
                    f"Rồng còn {level}% máu - khiên đã kích hoạt!",
                    1600,
                )
                return

    def dragon_attack_result(self):
        if self.dragon_defense_done:
            return

        self.dragon_defense_done = True
        damage = 15 if self.sword else 25
        self.knight_hp = max(0, self.knight_hp - damage)
        if self.game_state is not None:
            self.game_state.take_damage(damage)

        self.start_message(f"Rồng tấn công! Hiệp sĩ mất {damage} máu!", 1400)
        if self.knight_hp <= 0:
            self.game_over = True
            self.win = False
            self.start_message("HIỆP SĨ ĐÃ THẤT BẠI!", 3000)

    def finish_clear_animation(self):
        rows = self.animation["rows"]
        source = self.animation["source"]

        if source == "player":
            self.failed_turns = 0
            self.rows_cleared_this_attack += len(rows)

        self.clear_rows(rows)
        self.animation = None

        cascade_rows = self.get_full_rows()
        if cascade_rows:
            self.start_clear_animation(cascade_rows, source)
            return

        self.add_blocks_until_three_rows()
        cascade_rows = self.get_full_rows()
        if cascade_rows:
            self.start_clear_animation(cascade_rows, source)
            return

        self.start_attack_animation(
            rows,
            source,
            self.rows_cleared_this_attack
            if source == "player"
            else len(rows),
        )

    def finish_attack_animation(self):
        source = self.animation["source"]
        self.rows_cleared_this_attack = self.animation["rows_cleared"]

        self.animation = None

        if self.game_over:
            return

        if source == "player":
            self.player_attack()

            if self.game_over:
                return

            self.finish_player_turn()

        else:
            self.finish_dragon_attack()

    def find_dragon_attack_position(self):
        candidates = []

        lengths = [1, 2, 3, 4]

        for length in lengths:
            for row in range(self.ROWS):
                for col in range(
                    self.COLS - length + 1
                ):
                    if self.can_place(
                        row,
                        col,
                        length
                    ):
                        candidates.append(
                            (
                                row,
                                col,
                                length
                            )
                        )

        if not candidates:
            return None

        return random.choice(
            candidates
        )

    def dragon_attack(self):
        self.dragon_defense_done = False
        self.dragon_attacks_received += 1
        self.dragon_attack_flash_timer = self.ATTACK_TIME
        block_count = 2 if not self.sword else 1

        for _ in range(block_count):
            position = self.find_dragon_attack_position()
            if position is None:
                self.game_over = True
                self.win = False
                self.animation = None
                self.start_message("Rồng đã lấp đầy bàn chơi!", 3000)
                return

            row, col, length = position
            self.place_piece(self.new_piece(length, row, col))
            self.rebuild_piece_cells()

        old_positions = {
            piece["id"]: list(piece["cells"])
            for piece in self.get_pieces()
        }
        new_positions = self.calculate_gravity_result()
        pieces = {piece["id"]: piece for piece in self.get_pieces()}

        self.board = [
            [None for _ in range(self.COLS)]
            for _ in range(self.ROWS)
        ]
        for piece_id, cells in new_positions.items():
            pieces[piece_id]["cells"] = cells
            self.place_piece(pieces[piece_id])
        self.rebuild_piece_cells()

        moved = any(
            old_positions[piece_id] != new_positions.get(
                piece_id, old_positions[piece_id]
            )
            for piece_id in old_positions
        )
        self.start_message("Rồng đẩy thêm khối vào bàn chơi!", 1100)

        if moved:
            self.start_fall_animation(old_positions, new_positions, "dragon")
            return

        rows = self.get_full_rows()
        if rows:
            self.start_clear_animation(rows, "dragon")
        else:
            self.finish_dragon_attack()
    def finish_dragon_attack(self):
        if self.check_top():
            return

        rows = self.get_full_rows()
        if rows:
            self.start_clear_animation(rows, "dragon")
            return

        self.dragon_attack_result()
        if self.game_over:
            return
        if self.message_timer <= 0:
            self.start_message("Đến lượt bạn", 900)
    def update_animation(
        self,
        dt
    ):
        if self.animation is None:
            return

        self.animation["time"] += dt

        kind = self.animation["type"]

        if (
            kind == "move"
            and self.animation["time"] >= self.MOVE_TIME
        ):
            self.animation = None
            self.player_move_finished()

        elif (
            kind == "fall"
            and self.animation["time"] >= self.FALL_TIME
        ):
            source = self.animation["source"]

            self.animation = None

            self.finish_after_fall(
                source
            )

        elif (
            kind == "clear"
            and self.animation["time"] >= self.CLEAR_TIME
        ):
            self.finish_clear_animation()

        elif (
            kind == "push"
            and self.animation["time"] >= self.PUSH_TIME
        ):
            self.animation = None

            self.after_push()

        elif (
            kind == "attack"
            and self.animation["time"] >= self.ATTACK_TIME
        ):
            self.finish_attack_animation()

    def ease(self, t):
        t = max(
            0.0,
            min(1.0, t)
        )

        return t * t * (3 - 2 * t)

    def board_pos_to_cell(
        self,
        pos
    ):
        x, y = pos

        col = int(
            (
                x - self.BOARD_X
            ) // self.CELL
        )

        row = int(
            (
                y - self.BOARD_Y
            ) // self.CELL
        )

        if (
            0 <= row < self.ROWS
            and 0 <= col < self.COLS
        ):
            return row, col

        return None

    def mouse_down(
        self,
        pos
    ):
        if (
            self.game_over
            or self.animation is not None
        ):
            return

        cell = self.board_pos_to_cell(
            pos
        )

        if cell is None:
            return

        row, col = cell

        piece = self.board[row][col]

        if piece is None:
            return

        self.selected_piece = piece

        start_col = min(
            c for _, c in piece["cells"]
        )

        self.drag_start_col = start_col
        self.drag_current_col = start_col

        self.drag_mouse_x = pos[0]

        piece_x = (
            self.BOARD_X
            + start_col * self.CELL
        )

        self.drag_offset = (
            pos[0] - piece_x
        )

    def mouse_motion(
        self,
        pos
    ):
        if self.selected_piece is None:
            return

        self.drag_mouse_x = pos[0]

        piece = self.selected_piece

        row = piece["cells"][0][0]

        piece_left_x = (
            self.drag_mouse_x
            - self.drag_offset
        )

        target_col = round(
            (
                piece_left_x
                - self.BOARD_X
            )
            / self.CELL
        )

        target_col = max(
            0,
            min(
                self.COLS
                - piece["length"],
                target_col
            )
        )

        start_col = min(c for _, c in piece["cells"])
        if self.can_slide_piece(
            row,
            start_col,
            target_col,
            piece["length"],
            piece["id"]
        ):
            self.drag_current_col = target_col

    def mouse_up(self):
        if self.selected_piece is None:
            return

        piece = self.selected_piece

        target_col = self.drag_current_col

        old_col = min(
            c for _, c in piece["cells"]
        )

        self.selected_piece = None
        self.drag_current_col = None
        self.drag_mouse_x = None
        self.drag_start_col = None

        if target_col is None:
            return

        if target_col == old_col:
            return

        self.move_piece(
            piece,
            target_col
        )

    def update(
        self,
        dt
    ):
        dt *= 1000
        if self.message_timer > 0:
            self.message_timer -= dt

            if self.message_timer < 0:
                self.message_timer = 0

        self.update_animation(dt)
        self.dragon_attack_flash_timer = max(
            0,
            self.dragon_attack_flash_timer - dt,
        )

    def handle_event(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            self.mouse_down(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_motion(event.pos)
        elif (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
        ):
            self.mouse_up()

    def draw_block(
        self,
        rect,
        color,
        selected=False,
        alpha=255
    ):
        surface = pygame.Surface(
            (
                rect.width,
                rect.height
            ),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            surface,
            (*color, alpha),
            (
                3,
                3,
                rect.width - 6,
                rect.height - 6
            ),
            border_radius=10
        )

        pygame.draw.rect(
            surface,
            (
                255,
                255,
                255,
                min(alpha, 90)
            ),
            (
                7,
                7,
                rect.width - 14,
                8
            ),
            border_radius=4
        )

        pygame.draw.rect(
            surface,
            (
                61,
                19,
                5,
                min(alpha, 130)
            ),
            (
                3,
                3,
                rect.width - 6,
                rect.height - 6
            ),
            2,
            border_radius=10
        )

        if selected:
            pygame.draw.rect(
                surface,
                (
                    255,
                    112,
                    25,
                    alpha
                ),
                (
                    1,
                    1,
                    rect.width - 2,
                    rect.height - 2
                ),
                4,
                border_radius=12
            )

        self.screen.blit(
            surface,
            rect.topleft
        )

    def draw_board_grid(self):
        board_rect = pygame.Rect(
            self.BOARD_X,
            self.BOARD_Y,
            self.COLS * self.CELL,
            self.ROWS * self.CELL
        )

        pygame.draw.rect(
            self.screen,
            (61, 19, 5),
            board_rect,
            border_radius=12
        )

        pygame.draw.rect(
            self.screen,
            (177, 92, 64),
            board_rect,
            4,
            border_radius=12
        )

        for r in range(self.ROWS):
            for c in range(self.COLS):
                rect = pygame.Rect(
                    self.BOARD_X
                    + c * self.CELL
                    + 2,
                    self.BOARD_Y
                    + r * self.CELL
                    + 2,
                    self.CELL - 4,
                    self.CELL - 4
                )

                pygame.draw.rect(
                    self.screen,
                    (207, 177, 158),
                    rect,
                    1,
                    border_radius=6
                )

    def draw_piece_at_cells(
        self,
        piece,
        cells,
        selected=False,
        alpha=255
    ):
        if not cells:
            return

        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        rect = pygame.Rect(
            self.BOARD_X + min(cols) * self.CELL,
            self.BOARD_Y + min(rows) * self.CELL,
            (max(cols) - min(cols) + 1) * self.CELL,
            (max(rows) - min(rows) + 1) * self.CELL
        )
        self.draw_block(rect, piece["color"], selected, alpha)

    def draw_dragging_piece(self):
        if self.selected_piece is None:
            return

        if self.drag_mouse_x is None:
            return

        piece = self.selected_piece

        row = piece["cells"][0][0]

        target_col = (
            self.drag_current_col
            if self.drag_current_col is not None
            else min(c for _, c in piece["cells"])
        )
        x = self.BOARD_X + target_col * self.CELL

        y = (
            self.BOARD_Y
            + row * self.CELL
        )

        rect = pygame.Rect(
            int(x),
            y,
            piece["length"] * self.CELL,
            self.CELL
        )
        self.draw_block(rect, piece["color"], True)

        if self.drag_current_col is not None:
            target_x = (
                self.BOARD_X
                + self.drag_current_col
                * self.CELL
            )

            target_rect = pygame.Rect(
                target_x,
                y,
                piece["length"]
                * self.CELL,
                self.CELL
            )

            pygame.draw.rect(
                self.screen,
                (255, 240, 130),
                target_rect,
                2,
                border_radius=8
            )

    def draw_normal_board(self):
        self.draw_board_grid()

        drawn = set()

        selected_id = None

        if self.selected_piece is not None:
            selected_id = self.selected_piece["id"]

        for r in range(self.ROWS):
            for c in range(self.COLS):
                p = self.board[r][c]

                if p is None:
                    continue

                if p["id"] in drawn:
                    continue

                if p["id"] == selected_id:
                    continue

                drawn.add(
                    p["id"]
                )

                self.draw_piece_at_cells(
                    p,
                    p["cells"]
                )

        self.draw_dragging_piece()

    def draw_move_animation(self):
        anim = self.animation

        self.draw_board_grid()

        selected_id = anim["piece_id"]

        drawn = set()

        for r in range(self.ROWS):
            for c in range(self.COLS):
                p = self.board[r][c]

                if p is None:
                    continue

                if p["id"] in drawn:
                    continue

                if p["id"] == selected_id:
                    continue

                drawn.add(
                    p["id"]
                )

                self.draw_piece_at_cells(
                    p,
                    p["cells"]
                )

        t = self.ease(
            anim["time"]
            / self.MOVE_TIME
        )

        old_cells = anim["old_cells"]
        new_cells = anim["new_cells"]

        old_col = min(
            c for _, c in old_cells
        )

        new_col = min(
            c for _, c in new_cells
        )

        row = old_cells[0][0]

        current_col = (
            old_col
            + (
                new_col
                - old_col
            ) * t
        )

        piece = None

        for p in self.get_pieces():
            if p["id"] == selected_id:
                piece = p
                break

        if piece is None:
            return

        rect = pygame.Rect(
            self.BOARD_X + int(current_col * self.CELL),
            self.BOARD_Y + row * self.CELL,
            piece["length"] * self.CELL,
            self.CELL
        )
        self.draw_block(rect, piece["color"], True)

    def draw_fall_animation(self):
        anim = self.animation

        self.draw_board_grid()

        old_positions = anim[
            "old_positions"
        ]

        new_positions = anim[
            "new_positions"
        ]

        t = self.ease(
            anim["time"]
            / self.FALL_TIME
        )

        pieces = {
            p["id"]: p
            for p in self.get_pieces()
        }

        for pid, old_cells in old_positions.items():
            if pid not in pieces:
                continue

            if pid not in new_positions:
                continue

            p = pieces[pid]

            new_cells = new_positions[pid]
            old_r, old_c = old_cells[0]
            new_r, new_c = new_cells[0]
            r = old_r + (new_r - old_r) * t
            c = old_c + (new_c - old_c) * t
            rect = pygame.Rect(
                self.BOARD_X + int(c * self.CELL),
                self.BOARD_Y + int(r * self.CELL),
                len(old_cells) * self.CELL,
                self.CELL
            )
            self.draw_block(rect, p["color"])

    def draw_clear_animation(self):
        self.draw_normal_board()

        t = (
            self.animation["time"]
            / self.CLEAR_TIME
        )

        alpha = int(
            255
            * max(
                0,
                1 - t
            )
        )

        for row in self.animation["rows"]:
            for col in range(self.COLS):
                rect = pygame.Rect(
                    self.BOARD_X
                    + col * self.CELL,
                    self.BOARD_Y
                    + row * self.CELL,
                    self.CELL,
                    self.CELL
                )

                surface = pygame.Surface(
                    (
                        self.CELL,
                        self.CELL
                    ),
                    pygame.SRCALPHA
                )

                pygame.draw.rect(
                    surface,
                    (
                        255,
                        240,
                        100,
                        alpha
                    ),
                    (
                        2,
                        2,
                        self.CELL - 4,
                        self.CELL - 4
                    ),
                    border_radius=8
                )

                self.screen.blit(
                    surface,
                    rect.topleft
                )

    def draw_push_animation(self):
        self.draw_board_grid()

        t = self.ease(
            self.animation["time"]
            / self.PUSH_TIME
        )

        old_board = self.animation[
            "old_board"
        ]

        pieces = {}
        for r, row in enumerate(old_board):
            for c, piece in enumerate(row):
                if piece is not None:
                    pieces.setdefault(piece["id"], [piece, []])[1].append((r, c))

        for piece, cells in pieces.values():
            row = min(r for r, _ in cells)
            col = min(c for _, c in cells)
            rect = pygame.Rect(
                self.BOARD_X + col * self.CELL,
                self.BOARD_Y + int((row - t) * self.CELL),
                len(cells) * self.CELL,
                self.CELL
            )
            self.draw_block(rect, piece["color"])

        new_row_pieces = {}
        for col, piece in enumerate(self.board[self.ROWS - 1]):
            if piece is not None:
                new_row_pieces.setdefault(piece["id"], [piece, []])[1].append(col)

        for piece, cols in new_row_pieces.values():
            rect = pygame.Rect(
                self.BOARD_X + min(cols) * self.CELL,
                self.BOARD_Y + int((self.ROWS - t) * self.CELL),
                len(cols) * self.CELL,
                self.CELL
            )
            self.draw_block(rect, piece["color"])

    def draw_attack_animation(self):
        self.draw_normal_board()

        anim = self.animation

        t = max(
            0.0,
            min(
                1.0,
                anim["time"]
                / self.ATTACK_TIME
            )
        )

        sx, sy = anim["start"]
        ex, ey = anim["end"]

        current_x = (
            sx
            + (
                ex - sx
            ) * t
        )

        current_y = (
            sy
            + (
                ey - sy
            ) * t
        )

        if anim["source"] == "player":
            color = (
                255,
                245,
                130
            )
        else:
            color = (
                220,
                100,
                255
            )

        points = [
            (sx, sy)
        ]

        steps = 10

        for i in range(
            1,
            steps + 1
        ):
            k = i / steps

            px = (
                sx
                + (
                    current_x
                    - sx
                ) * k
            )

            py = (
                sy
                + (
                    current_y
                    - sy
                ) * k
            )

            px += math.sin(
                i * 2.2
                + t * 15
            ) * 8

            points.append(
                (
                    int(px),
                    int(py)
                )
            )

        if len(points) >= 2:
            pygame.draw.lines(
                self.screen,
                color,
                False,
                points,
                6
            )

            pygame.draw.lines(
                self.screen,
                (255, 255, 255),
                False,
                points,
                2
            )

        pygame.draw.circle(
            self.screen,
            color,
            (
                int(current_x),
                int(current_y)
            ),
            12
        )

    def draw_dragon(self):
        cx = (
            self.BOARD_X
            + self.COLS
            * self.CELL
            // 2
        )
        cy = self.BOARD_Y - int(104 * self.ui_scale)
        image_rect = self.dragon_image.get_rect(
            center=(cx, cy)
        )
        self.screen.blit(self.dragon_image, image_rect)
        bar_width = max(220, int(360 * self.ui_scale))
        bar_height = max(19, int(28 * self.ui_scale))
        bar_rect = pygame.Rect(
            image_rect.centerx - bar_width // 2,
            image_rect.bottom + int(2 * self.ui_scale),
            bar_width,
            bar_height,
        )
        pygame.draw.rect(self.screen, (61, 19, 5), bar_rect, border_radius=5)
        fill_rect = bar_rect.inflate(-2, -2)
        fill_rect.width = round(fill_rect.width * max(0, self.dragon_hp) / self.MAX_HP)
        if fill_rect.width:
            pygame.draw.rect(self.screen, (198, 64, 50), fill_rect, border_radius=4)

        if self.dragon_shield:
            text = self.font_small.render(
                "KHIÊN",
                True,
                (120, 210, 255)
            )

            self.screen.blit(
                text,
                text.get_rect(
                    center=(
                        cx,
                        image_rect.top - 18
                    )
                )
            )

    def draw_knight(self):
        knight_x = self.BOARD_X + (self.COLS * self.CELL - self.knight_image.get_width()) // 2
        knight_y = self.BOARD_Y + self.ROWS * self.CELL
        self.screen.blit(self.knight_image, (knight_x, knight_y))

    def draw_dragon_fire(self):
        if self.dragon_attack_flash_timer <= 0:
            return

        center_x = self.BOARD_X + self.COLS * self.CELL // 2
        start_y = self.BOARD_Y - int(34 * self.ui_scale)
        end_y = self.BOARD_Y + self.ROWS * self.CELL + int(18 * self.ui_scale)
        wobble = int(9 * math.sin(pygame.time.get_ticks() / 35))
        flame = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        outer_width = max(24, int(42 * self.ui_scale))
        inner_width = max(8, int(15 * self.ui_scale))
        points = [
            (center_x - outer_width // 3, start_y),
            (center_x + outer_width // 3, start_y),
            (center_x + outer_width // 2 + wobble, end_y - 28),
            (center_x + outer_width // 2, end_y),
            (center_x - outer_width // 2, end_y),
            (center_x - outer_width // 2 + wobble, end_y - 28),
        ]
        pygame.draw.polygon(flame, (244, 70, 18, 150), points)
        pygame.draw.line(
            flame,
            (255, 183, 52, 205),
            (center_x, start_y),
            (center_x + wobble // 2, end_y),
            inner_width,
        )
        pygame.draw.circle(
            flame,
            (255, 230, 126, 210),
            (center_x + wobble // 2, end_y - 3),
            max(12, int(22 * self.ui_scale)),
        )
        self.screen.blit(flame, (0, 0))

    def draw_ui(self):
        scale = self.ui_scale
        left_x = self.width - int(385 * scale) - int(24 * scale)
        left_y = int(160 * scale)
        left_width = int(385 * scale)
        left_height = min(int(300 * scale), self.height - left_y - int(20 * scale))
        left_panel = pygame.Rect(left_x, left_y, left_width, left_height)
        pygame.draw.rect(self.screen, (177, 92, 64), left_panel, border_radius=12)
        pygame.draw.rect(self.screen, (239, 139, 118), left_panel, 2, border_radius=12)

        heading = self.font.render("TÌNH HÌNH TRẬN ĐẤU", True, (255, 220, 155))
        self.screen.blit(heading, (left_x + int(18 * scale), left_y + int(16 * scale)))
        attack_threshold = self.DRAGON_ATTACK_MISSES
        damage_table = self.SWORD_DAMAGE if self.sword else self.NO_SWORD_DAMAGE
        mode_lines = [
            "VŨ KHÍ: THÁNH KIẾM" if self.sword else "VŨ KHÍ: KIẾM THƯỜNG",
            "SÁT THƯƠNG: CAO" if self.sword else "SÁT THƯƠNG: THẤP",
            f"RỒNG TẤN CÔNG SAU {attack_threshold} LƯỢT LỠ",
            f"LƯỢT LỠ: {self.failed_turns}/{attack_threshold}",
            "KHIÊN RỒNG: ĐANG BẬT" if self.dragon_shield else "KHIÊN RỒNG: ĐANG TẮT",
            "SÁT THƯƠNG MỖI HÀNG: " + "/".join(str(damage_table.get(i, max(damage_table.values()))) for i in range(1, 5)),
        ]
        if not self.sword:
            mode_lines.append("VẢY RỒNG GIỮ MÁU TRÊN 80")
        line_y = left_y + int(58 * scale)
        line_gap = max(20, int(29 * scale))
        for line in mode_lines:
            text = self.font_small.render(line, True, (248, 239, 222))
            self.screen.blit(text, (left_x + int(18 * scale), line_y))
            line_y += line_gap

        guide_x = left_x
        guide_y = int(455 * scale)
        guide_width = left_width
        guide_height = min(int(225 * scale), self.height - guide_y - int(20 * scale))
        guide = pygame.Rect(guide_x, guide_y, guide_width, guide_height)
        pygame.draw.rect(self.screen, (177, 92, 64), guide, border_radius=12)
        pygame.draw.rect(self.screen, (239, 139, 118), guide, 2, border_radius=12)
        guide_title = self.font.render("CÁCH CHƠI", True, (255, 220, 155))
        self.screen.blit(guide_title, (guide.x + int(18 * scale), guide.y + int(14 * scale)))
        instructions = [
            "Kéo khối sang trái hoặc phải",
            "Thả chuột để đặt khối",
            "Lấp đầy hàng để tấn công",
        ]
        line_y = guide.y + int(48 * scale)
        for line in instructions:
            text = self.font_small.render(line, True, (248, 239, 222))
            self.screen.blit(text, (guide.x + int(18 * scale), line_y))
            line_y += max(19, int(27 * scale))

        message_x = int(24 * scale)
        message_width = min(
            int(500 * scale),
            max(0, self.BOARD_X - message_x - int(20 * scale)),
        )
        message_font = self.font
        message_lines = []
        current_line = ""
        for word in self.message.split():
            candidate = f"{current_line} {word}".strip()
            if current_line and message_font.size(candidate)[0] > message_width - int(24 * scale):
                message_lines.append(current_line)
                current_line = word
            else:
                current_line = candidate
        if current_line:
            message_lines.append(current_line)
        line_height = message_font.get_linesize()
        message_height = max(
            int(60 * scale),
            len(message_lines) * line_height + int(22 * scale),
        )
        message_box = pygame.Rect(
            message_x,
            self.height - message_height - int(16 * scale),
            message_width,
            message_height,
        )
        pygame.draw.rect(self.screen, (61, 19, 5), message_box, border_radius=8)
        pygame.draw.rect(self.screen, (177, 92, 64), message_box, 2, border_radius=8)
        for index, line in enumerate(message_lines):
            message = message_font.render(line, True, (255, 240, 170))
            self.screen.blit(
                message,
                message.get_rect(
                    center=(
                        message_box.centerx,
                        message_box.centery
                        + (index - (len(message_lines) - 1) / 2) * line_height,
                    )
                ),
            )

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            self.screen.blit(overlay, (0, 0))
            title_text = "CHIẾN THẮNG!" if self.win else "THẤT BẠI!"
            title = self.font_big.render(title_text, True, (255, 235, 150))
            self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 30)))
            sub = self.font.render("Nhấn R để chơi lại", True, (235, 225, 205))
            self.screen.blit(sub, sub.get_rect(center=(self.width // 2, self.height // 2 + 25)))
    def reset(self):
        self.game_over = False
        self.win = False

        self.knight_hp = min(
            self.MAX_HP,
            getattr(self.game_state, "health", self.MAX_HP),
        )
        self.dragon_hp = self.MAX_HP

        self.dragon_shield = False
        self.shield_level = None
        self.activated_shield_levels = set()
        self.dragon_defense_done = False
        self.dragon_attack_flash_timer = 0

        self.turn = 0
        self.failed_turns = 0
        self.dragon_attacks_received = 0
        self.rows_cleared_this_attack = 0
        self.message_timer = 0

        self.selected_piece = None
        self.drag_current_col = None
        self.drag_mouse_x = None
        self.drag_start_col = None
        self.drag_offset = 0

        self.animation = None

        self.next_row_preview = []

        self.create_initial_board()

    def draw(self):
        self.screen.fill(
            (248, 235, 212)
        )

        if self.animation is None:
            self.draw_normal_board()

        else:
            kind = self.animation[
                "type"
            ]

            if kind == "move":
                self.draw_move_animation()

            elif kind == "fall":
                self.draw_fall_animation()

            elif kind == "clear":
                self.draw_clear_animation()

            elif kind == "push":
                self.draw_push_animation()

            elif kind == "attack":
                self.draw_attack_animation()

        self.draw_dragon()
        self.draw_knight()
        self.draw_dragon_fire()
        self.draw_ui()
