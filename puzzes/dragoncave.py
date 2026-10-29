import pygame
import random
import math


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

    COLORS = [
        (235, 95, 95),
        (95, 165, 235),
        (105, 205, 125),
        (225, 185, 80),
        (180, 115, 225),
        (80, 205, 195),
    ]

    def __init__(self, width=1400, height=900):
        pygame.init()

        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Dragon Cave - Wooden Block Battle")

        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("arial", 34, bold=True)
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("arial", 18)

        self.running = True
        self.game_over = False
        self.win = False

        self.knight_hp = self.MAX_HP
        self.dragon_hp = self.MAX_HP

        self.dragon_shield = False
        self.shield_level = None
        self.dragon_defense_done = False

        self.sword = True

        self.turn = 0
        self.dragon_attack_every = 3

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
        if color is None:
            color = random.choice(self.COLORS)

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

        for row in range(self.ROWS - 3, self.ROWS):
            count = random.randint(2, 4)

            cols = random.sample(
                range(self.COLS),
                count
            )

            for col in cols:
                piece = self.new_piece(
                    1,
                    row,
                    col
                )

                self.place_piece(piece)

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
        if self.turn <= 2:
            return 1

        if self.turn <= 5:
            return random.choices(
                [1, 2],
                weights=[75, 25],
                k=1
            )[0]

        if self.turn <= 8:
            return random.choices(
                [1, 2, 3],
                weights=[60, 32, 8],
                k=1
            )[0]

        return random.choices(
            [1, 2, 3, 4],
            weights=[55, 32, 10, 3],
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
                "color": random.choice(self.COLORS),
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
                    "Các khối đã chạm đỉnh! THUA",
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
        source
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

    def player_move_finished(self):
        self.rebuild_piece_cells()

        self.apply_gravity()

        if self.check_top():
            return

        rows = self.get_full_rows()

        if rows:
            self.start_clear_animation(
                rows,
                "player"
            )

            return

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
            self.start_clear_animation(
                rows,
                "player"
            )

            return

        if (
            self.turn > 0
            and self.turn % self.dragon_attack_every == 0
        ):
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
        damage = 10 if self.sword else 5

        if self.dragon_shield:
            self.start_message(
                "Khiên rồng chặn đòn tấn công!",
                1200
            )

            return

        old_hp = self.dragon_hp

        self.dragon_hp = max(
            0,
            self.dragon_hp - damage
        )

        self.check_shield_activation(
            old_hp
        )

        if self.dragon_hp <= 0:
            self.win = True
            self.game_over = True

            self.start_message(
                "RỒNG BỊ ĐÁNH BẠI!",
                4000
            )

        else:
            self.start_message(
                f"Hiệp sĩ gây {damage} sát thương!",
                900
            )

    def check_shield_activation(
        self,
        old_hp
    ):
        shield_levels = [
            70,
            50,
            15,
            5
        ]

        for level in shield_levels:
            if old_hp > level >= self.dragon_hp:
                if self.shield_level != level:
                    self.dragon_shield = True
                    self.shield_level = level

                    self.start_message(
                        f"Rồng chạm mốc {level}% HP - KHIÊN ĐƯỢC KÍCH HOẠT!",
                        1600
                    )

                    return

    def dragon_attack_result(self):
        if self.dragon_defense_done:
            return

        self.dragon_defense_done = True

        if self.sword:
            if self.dragon_shield:
                self.dragon_shield = False
                self.shield_level = None

                self.start_message(
                    "Phòng thủ thành công! Khiên rồng bị phá!",
                    1400
                )

            else:
                self.start_message(
                    "Phòng thủ thành công! Không mất HP.",
                    1100
                )

        else:
            self.knight_hp = max(
                0,
                self.knight_hp - 20
            )

            self.start_message(
                "Không có Holy Sword: rồng gây 20 sát thương!",
                1400
            )

            if self.knight_hp <= 0:
                self.game_over = True
                self.win = False

                self.start_message(
                    "HIỆP SĨ ĐÃ THẤT BẠI!",
                    3000
                )

    def finish_clear_animation(self):
        rows = self.animation["rows"]
        source = self.animation["source"]

        self.clear_rows(rows)

        self.add_blocks_until_three_rows()

        self.animation = None

        self.start_attack_animation(
            rows,
            source
        )

    def finish_attack_animation(self):
        source = self.animation["source"]

        self.animation = None

        if self.game_over:
            return

        if source == "player":
            self.player_attack()

            if self.game_over:
                return

            self.finish_player_turn()

        else:
            self.dragon_attack_result()

            if self.game_over:
                return

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

        pos = self.find_dragon_attack_position()

        if pos is None:
            self.game_over = True
            self.win = False

            self.start_message(
                "Rồng đã lấp đầy bàn! THUA",
                3000
            )

            return

        row, col, length = pos

        piece = self.new_piece(
            length,
            row,
            col,
            (185, 75, 95)
        )

        self.place_piece(piece)

        self.rebuild_piece_cells()

        old_positions = {
            p["id"]: list(p["cells"])
            for p in self.get_pieces()
        }

        new_positions = self.calculate_gravity_result()

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

        moved = False

        for pid in old_positions:
            if old_positions[pid] != new_positions.get(
                pid,
                old_positions[pid]
            ):
                moved = True
                break

        self.start_message(
            "Rồng tấn công: thêm khối vào bàn!",
            1100
        )

        if moved:
            self.start_fall_animation(
                old_positions,
                new_positions,
                "dragon"
            )

        else:
            rows = self.get_full_rows()

            if rows:
                self.start_clear_animation(
                    rows,
                    "dragon"
                )

            else:
                self.finish_dragon_attack()

    def finish_dragon_attack(self):
        if self.check_top():
            return

        rows = self.get_full_rows()

        if rows:
            self.start_clear_animation(
                rows,
                "dragon"
            )

            return

        self.dragon_attack_result()

        if self.game_over:
            return

        self.start_message(
            "Đến lượt bạn",
            900
        )

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

        if self.can_place(
            row,
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
        if self.message_timer > 0:
            self.message_timer -= dt

            if self.message_timer < 0:
                self.message_timer = 0

        self.update_animation(dt)

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
                40,
                30,
                25,
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
                    245,
                    130,
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
            (35, 28, 24),
            board_rect,
            border_radius=12
        )

        pygame.draw.rect(
            self.screen,
            (110, 80, 55),
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
                    (55, 45, 38),
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
        for r, c in cells:
            rect = pygame.Rect(
                self.BOARD_X
                + int(c * self.CELL),
                self.BOARD_Y
                + int(r * self.CELL),
                self.CELL,
                self.CELL
            )

            self.draw_block(
                rect,
                piece["color"],
                selected,
                alpha
            )

    def draw_dragging_piece(self):
        if self.selected_piece is None:
            return

        if self.drag_mouse_x is None:
            return

        piece = self.selected_piece

        row = piece["cells"][0][0]

        x = (
            self.drag_mouse_x
            - self.drag_offset
        )

        min_x = self.BOARD_X

        max_x = (
            self.BOARD_X
            + self.COLS * self.CELL
            - piece["length"] * self.CELL
        )

        x = max(
            min_x,
            min(max_x, x)
        )

        y = (
            self.BOARD_Y
            + row * self.CELL
        )

        for i in range(
            piece["length"]
        ):
            rect = pygame.Rect(
                int(
                    x
                    + i * self.CELL
                ),
                y,
                self.CELL,
                self.CELL
            )

            self.draw_block(
                rect,
                piece["color"],
                True
            )

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

        for i in range(
            piece["length"]
        ):
            rect = pygame.Rect(
                self.BOARD_X
                + int(
                    (
                        current_col
                        + i
                    )
                    * self.CELL
                ),
                self.BOARD_Y
                + row * self.CELL,
                self.CELL,
                self.CELL
            )

            self.draw_block(
                rect,
                piece["color"],
                True
            )

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

            for i in range(
                len(old_cells)
            ):
                old_r, old_c = old_cells[i]
                new_r, new_c = new_cells[i]

                r = (
                    old_r
                    + (
                        new_r
                        - old_r
                    ) * t
                )

                c = (
                    old_c
                    + (
                        new_c
                        - old_c
                    ) * t
                )

                rect = pygame.Rect(
                    self.BOARD_X
                    + int(
                        c
                        * self.CELL
                    ),
                    self.BOARD_Y
                    + int(
                        r
                        * self.CELL
                    ),
                    self.CELL,
                    self.CELL
                )

                self.draw_block(
                    rect,
                    p["color"]
                )

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

        drawn = set()

        for r in range(self.ROWS):
            for c in range(self.COLS):
                p = old_board[r][c]

                if p is None:
                    continue

                key = (
                    p["id"],
                    r,
                    c
                )

                if key in drawn:
                    continue

                drawn.add(key)

                rect = pygame.Rect(
                    self.BOARD_X
                    + c * self.CELL,
                    self.BOARD_Y
                    + int(
                        (
                            r - t
                        )
                        * self.CELL
                    ),
                    self.CELL,
                    self.CELL
                )

                self.draw_block(
                    rect,
                    p["color"]
                )

        for c in range(self.COLS):
            p = self.board[
                self.ROWS - 1
            ][c]

            if p is None:
                continue

            rect = pygame.Rect(
                self.BOARD_X
                + c * self.CELL,
                self.BOARD_Y
                + int(
                    (
                        self.ROWS
                        - t
                    )
                    * self.CELL
                ),
                self.CELL,
                self.CELL
            )

            self.draw_block(
                rect,
                p["color"]
            )

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

        cy = (
            self.BOARD_Y
            - 65
        )

        pygame.draw.ellipse(
            self.screen,
            (105, 45, 45),
            (
                cx - 72,
                cy - 38,
                144,
                76
            )
        )

        pygame.draw.polygon(
            self.screen,
            (135, 55, 55),
            [
                (
                    cx - 58,
                    cy - 25
                ),
                (
                    cx - 100,
                    cy - 70
                ),
                (
                    cx - 88,
                    cy + 5
                )
            ]
        )

        pygame.draw.polygon(
            self.screen,
            (135, 55, 55),
            [
                (
                    cx + 58,
                    cy - 25
                ),
                (
                    cx + 100,
                    cy - 70
                ),
                (
                    cx + 88,
                    cy + 5
                )
            ]
        )

        pygame.draw.circle(
            self.screen,
            (230, 100, 80),
            (
                cx - 27,
                cy - 5
            ),
            8
        )

        pygame.draw.circle(
            self.screen,
            (230, 100, 80),
            (
                cx + 27,
                cy - 5
            ),
            8
        )

        pygame.draw.circle(
            self.screen,
            (20, 15, 15),
            (
                cx - 27,
                cy - 5
            ),
            3
        )

        pygame.draw.circle(
            self.screen,
            (20, 15, 15),
            (
                cx + 27,
                cy - 5
            ),
            3
        )

        if self.dragon_shield:
            pulse = int(
                5
                * math.sin(
                    pygame.time.get_ticks()
                    / 120
                )
            )

            pygame.draw.ellipse(
                self.screen,
                (80, 180, 255),
                (
                    cx - 93 - pulse,
                    cy - 59 - pulse,
                    186 + pulse * 2,
                    118 + pulse * 2
                ),
                5
            )

            text = self.font_small.render(
                "SHIELD",
                True,
                (120, 210, 255)
            )

            self.screen.blit(
                text,
                text.get_rect(
                    center=(
                        cx,
                        cy - 75
                    )
                )
            )

    def draw_knight(self):
        cx = (
            self.BOARD_X
            + self.COLS
            * self.CELL
            // 2
        )

        cy = (
            self.BOARD_Y
            + self.ROWS
            * self.CELL
            + 70
        )

        pygame.draw.circle(
            self.screen,
            (150, 165, 185),
            (
                cx,
                cy - 24
            ),
            26
        )

        pygame.draw.rect(
            self.screen,
            (85, 105, 125),
            (
                cx - 38,
                cy,
                76,
                55
            ),
            border_radius=15
        )

        pygame.draw.polygon(
            self.screen,
            (175, 185, 205),
            [
                (
                    cx - 45,
                    cy + 8
                ),
                (
                    cx - 92,
                    cy + 30
                ),
                (
                    cx - 45,
                    cy + 50
                )
            ]
        )

        if self.sword:
            pygame.draw.line(
                self.screen,
                (245, 245, 230),
                (
                    cx + 48,
                    cy + 35
                ),
                (
                    cx + 98,
                    cy - 10
                ),
                7
            )

            pygame.draw.line(
                self.screen,
                (230, 195, 80),
                (
                    cx + 35,
                    cy + 45
                ),
                (
                    cx + 60,
                    cy + 20
                ),
                6
            )

    def draw_hp_bar(
        self,
        x,
        y,
        width,
        hp,
        title
    ):
        pygame.draw.rect(
            self.screen,
            (45, 35, 30),
            (
                x,
                y,
                width,
                30
            ),
            border_radius=8
        )

        fill = int(
            width
            * hp
            / self.MAX_HP
        )

        if hp > 50:
            color = (
                75,
                190,
                90
            )

        elif hp > 20:
            color = (
                225,
                180,
                65
            )

        else:
            color = (
                210,
                70,
                70
            )

        pygame.draw.rect(
            self.screen,
            color,
            (
                x,
                y,
                fill,
                30
            ),
            border_radius=8
        )

        pygame.draw.rect(
            self.screen,
            (220, 220, 220),
            (
                x,
                y,
                width,
                30
            ),
            2,
            border_radius=8
        )

        text = self.font.render(
            f"{title}: {hp}/100",
            True,
            (245, 245, 245)
        )

        self.screen.blit(
            text,
            (
                x,
                y - 30
            )
        )

    def draw_next_row_preview(self):
        x = self.width - 380
        y = 300
        w = 350
        h = 170

        panel = pygame.Rect(
            x,
            y,
            w,
            h
        )

        pygame.draw.rect(
            self.screen,
            (35, 29, 28),
            panel,
            border_radius=14
        )

        pygame.draw.rect(
            self.screen,
            (155, 125, 80),
            panel,
            2,
            border_radius=14
        )

        title = self.font.render(
            "HÀNG TIẾP THEO",
            True,
            (255, 225, 160)
        )

        self.screen.blit(
            title,
            (
                x + 18,
                y + 14
            )
        )

        preview_x = x + 20
        preview_y = y + 65
        cell = 36

        for c in range(self.COLS):
            rect = pygame.Rect(
                preview_x
                + c * cell,
                preview_y,
                cell - 3,
                cell - 3
            )

            pygame.draw.rect(
                self.screen,
                (55, 48, 45),
                rect,
                border_radius=5
            )

        for item in self.next_row_preview:
            for i in range(
                item["length"]
            ):
                c = (
                    item["col"]
                    + i
                )

                rect = pygame.Rect(
                    preview_x
                    + c * cell,
                    preview_y,
                    cell - 3,
                    cell - 3
                )

                pygame.draw.rect(
                    self.screen,
                    item["color"],
                    rect,
                    border_radius=5
                )

                pygame.draw.rect(
                    self.screen,
                    (235, 220, 190),
                    rect,
                    1,
                    border_radius=5
                )

        text = self.font_small.render(
            "Hàng sẽ xuất hiện sau lượt này",
            True,
            (205, 195, 180)
        )

        self.screen.blit(
            text,
            (
                x + 20,
                y + 125
            )
        )

    def draw_ui(self):
        pygame.draw.rect(
            self.screen,
            (27, 22, 20),
            (
                0,
                0,
                self.width,
                105
            )
        )

        title = self.font_big.render(
            "DRAGON CAVE",
            True,
            (255, 225, 155)
        )

        self.screen.blit(
            title,
            title.get_rect(
                center=(
                    self.width // 2,
                    28
                )
            )
        )

        turn_text = self.font.render(
            f"LƯỢT {self.turn}",
            True,
            (235, 220, 190)
        )

        self.screen.blit(
            turn_text,
            turn_text.get_rect(
                center=(
                    self.width // 2,
                    72
                )
            )
        )

        self.draw_hp_bar(
            35,
            65,
            300,
            self.knight_hp,
            "HIỆP SĨ"
        )

        self.draw_hp_bar(
            self.width - 385,
            65,
            350,
            self.dragon_hp,
            "RỒNG"
        )

        left_panel = pygame.Rect(
            25,
            180,
            385,
            560
        )

        pygame.draw.rect(
            self.screen,
            (34, 29, 27),
            left_panel,
            border_radius=14
        )

        pygame.draw.rect(
            self.screen,
            (125, 100, 70),
            left_panel,
            2,
            border_radius=14
        )

        heading = self.font.render(
            "THÔNG TIN TRẬN ĐẤU",
            True,
            (255, 220, 155)
        )

        self.screen.blit(
            heading,
            (
                48,
                205
            )
        )

        sword_text = (
            "ĐANG CẦM"
            if self.sword
            else "KHÔNG CÓ"
        )

        shield_text = (
            "ĐANG BẬT"
            if self.dragon_shield
            else "TẮT"
        )

        lines = [
            f"Holy Sword: {sword_text}",
            f"Khiên rồng: {shield_text}",
            "",
            "Mốc khiên:",
            "70% - 50% - 15% - 5%",
            "",
            "Đánh rồng:",
            "Có kiếm: 10 sát thương",
            "Không kiếm: 5 sát thương",
            "",
            "Rồng tấn công mỗi 3 lượt",
            "Có kiếm: phòng thủ",
            "Có khiên: phá khiên rồng",
            "Không kiếm: mất 20 HP",
            "",
            "H: bật/tắt Holy Sword",
            "R: chơi lại",
        ]

        y = 250

        for line in lines:
            color = (
                220,
                210,
                190
            )

            if (
                line.startswith(
                    "Holy Sword"
                )
                and self.sword
            ):
                color = (
                    255,
                    225,
                    100
                )

            if (
                line.startswith(
                    "Khiên"
                )
                and self.dragon_shield
            ):
                color = (
                    120,
                    210,
                    255
                )

            text = self.font_small.render(
                line,
                True,
                color
            )

            self.screen.blit(
                text,
                (
                    48,
                    y
                )
            )

            y += 28

        self.draw_next_row_preview()

        guide = pygame.Rect(
            self.width - 380,
            500,
            350,
            240
        )

        pygame.draw.rect(
            self.screen,
            (34, 29, 27),
            guide,
            border_radius=14
        )

        pygame.draw.rect(
            self.screen,
            (125, 100, 70),
            guide,
            2,
            border_radius=14
        )

        title = self.font.render(
            "CÁCH CHƠI",
            True,
            (255, 220, 155)
        )

        self.screen.blit(
            title,
            (
                guide.x + 20,
                guide.y + 18
            )
        )

        lines = [
            "Giữ chuột vào một khối",
            "Kéo trái/phải để di chuyển",
            "Khối sẽ đi theo chuột",
            "Thả chuột để đặt khối",
            "Khối tự rơi xuống",
            "Đầy hàng → tấn công rồng",
        ]

        y = guide.y + 58

        for line in lines:
            text = self.font_small.render(
                line,
                True,
                (215, 205, 185)
            )

            self.screen.blit(
                text,
                (
                    guide.x + 20,
                    y
                )
            )

            y += 28

        message_box = pygame.Rect(
            self.BOARD_X - 25,
            self.BOARD_Y
            + self.ROWS
            * self.CELL
            + 105,
            530,
            55
        )

        pygame.draw.rect(
            self.screen,
            (38, 30, 25),
            message_box,
            border_radius=10
        )

        pygame.draw.rect(
            self.screen,
            (155, 125, 80),
            message_box,
            2,
            border_radius=10
        )

        message = self.font_small.render(
            self.message,
            True,
            (255, 240, 170)
        )

        self.screen.blit(
            message,
            message.get_rect(
                center=message_box.center
            )
        )

        if self.game_over:
            overlay = pygame.Surface(
                (
                    self.width,
                    self.height
                ),
                pygame.SRCALPHA
            )

            overlay.fill(
                (
                    0,
                    0,
                    0,
                    175
                )
            )

            self.screen.blit(
                overlay,
                (
                    0,
                    0
                )
            )

            if self.win:
                text = "CHIẾN THẮNG!"
            else:
                text = "GAME OVER"

            title = self.font_big.render(
                text,
                True,
                (255, 235, 150)
            )

            self.screen.blit(
                title,
                title.get_rect(
                    center=(
                        self.width // 2,
                        self.height // 2 - 30
                    )
                )
            )

            sub = self.font.render(
                "Nhấn R để chơi lại",
                True,
                (235, 225, 205)
            )

            self.screen.blit(
                sub,
                sub.get_rect(
                    center=(
                        self.width // 2,
                        self.height // 2 + 25
                    )
                )
            )

    def reset(self):
        self.game_over = False
        self.win = False

        self.knight_hp = self.MAX_HP
        self.dragon_hp = self.MAX_HP

        self.dragon_shield = False
        self.shield_level = None
        self.dragon_defense_done = False

        self.turn = 0

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
            (22, 18, 17)
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
        self.draw_ui()

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset()

                    elif (
                        event.key == pygame.K_h
                        and not self.game_over
                    ):
                        self.sword = not self.sword

                        if self.sword:
                            text = "Holy Sword: BẬT"
                        else:
                            text = "Holy Sword: TẮT"

                        self.start_message(
                            text,
                            900
                        )

                elif (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):
                    self.mouse_down(
                        event.pos
                    )

                elif (
                    event.type
                    == pygame.MOUSEMOTION
                ):
                    self.mouse_motion(
                        event.pos
                    )

                elif (
                    event.type
                    == pygame.MOUSEBUTTONUP
                    and event.button == 1
                ):
                    self.mouse_up()

            self.update(dt)

            self.draw()

        pygame.quit()


if __name__ == "__main__":
    DragonBlockGame().run()
