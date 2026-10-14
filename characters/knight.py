
import math
import pygame

from animation.animation_manager import AnimationManager


class Knight:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

        self.walk_speed = 180
        self.run_speed = 300

        self.direction = "front"
        self.target = None
        self.is_running = False
        self.is_attacking = False

        self.animation = AnimationManager()
        base = "assets/sprites/knight"

        self.animation.load_folder(
            "idle", f"{base}/IDLE",
            fps=6, loop=True
        )

        self.animation.load_folder(
            "front", f"{base}/front",
            fps=6, loop=True
        )
        self.animation.load_folder(
            "back", f"{base}/after",
            fps=6, loop=True
        )

        self.animation.load_folder(
            "walk_left", f"{base}/walk_left",
            fps=8, loop=True
        )
        self.animation.load_folder(
            "walk_right", f"{base}/Walk_right",
            fps=8, loop=True
        )

        self.animation.load_folder(
            "run_left", f"{base}/Run_left",
            fps=12, loop=True
        )
        self.animation.load_folder(
            "run_right", f"{base}/Run_right",
            fps=12, loop=True
        )

        self.animation.load_folder(
            "turn_left", f"{base}/turn_left",
            fps=8, loop=False
        )
        self.animation.load_folder(
            "turn_right", f"{base}/turn_right",
            fps=8, loop=False
        )

        self.animation.load_folder(
            "attack", f"{base}/Attack",
            fps=10, loop=False
        )

        self.animation.play("front")

    def move_to(self, mouse_x, mouse_y):
        if not self.is_attacking:
            self.target = (mouse_x, mouse_y)

    def attack(self):
        if self.is_attacking:
            return

        self.is_attacking = True
        self.target = None
        self.animation.play("attack")

    def _get_movement_animation(self, dx, dy):
        if abs(dx) > abs(dy):
            if dx < 0:
                self.direction = "left"
                return (
                    "run_left" if self.is_running
                    else "walk_left"
                )

            self.direction = "right"
            return (
                "run_right" if self.is_running
                else "walk_right"
            )

        if dy < 0:
            self.direction = "back"
            return "back"

        self.direction = "front"
        return "front"

    def _get_idle_animation(self):
        """Chọn tư thế khi nhân vật dừng lại."""
        if self.direction == "front":
            return "front"
        if self.direction == "back":
            return "back"
        if self.direction == "left":
            return "turn_left"
        return "turn_right"

    def update(self, dt):
        # Đang tấn công: phát animation đến hết.
        if self.is_attacking:
            self.animation.update(dt)

            if self.animation.is_finished():
                self.is_attacking = False
                self.animation.play(self._get_idle_animation())

            return

        # Di chuyển đến vị trí chuột đã chọn.
        if self.target is not None:
            target_x, target_y = self.target
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.hypot(dx, dy)

            if distance <= 4:
                self.x = target_x
                self.y = target_y
                self.target = None
                self.animation.play(self._get_idle_animation())

            else:
                speed = (
                    self.run_speed if self.is_running
                    else self.walk_speed
                )

                step = min(speed * dt, distance)
                self.x += dx / distance * step
                self.y += dy / distance * step

                name = self._get_movement_animation(dx, dy)
                self.animation.play(name)

        self.animation.update(dt)

    def draw(self, screen, size=None):
        frame = self.animation.get_current_frame()

        if frame is None:
            return

        if size is not None:
            frame = pygame.transform.scale(frame, size)

        screen.blit(frame, (int(self.x), int(self.y)))
