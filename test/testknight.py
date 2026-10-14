
import pygame
from characters.knight import Knight

pygame.init()

screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Test Knight Animation")

clock = pygame.time.Clock()
knight = Knight(500, 300)

running = True
caps_lock_on = False

font = pygame.font.SysFont(None, 26)

while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                knight.move_to(*event.pos)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_CAPSLOCK:
                caps_lock_on = not caps_lock_on
                knight.is_running = caps_lock_on

                print(
                    "Chế độ chạy: BẬT"
                    if caps_lock_on
                    else "Chế độ chạy: TẮT"
                )

            elif event.key == pygame.K_SPACE:
                # Space: kiểm thử animation tấn công
                knight.attack()

    # Cập nhật nhân vật
    knight.update(dt)

    # Vẽ màn hình
    screen.fill((190, 220, 190))

    knight.draw(screen, (128, 128))

    instructions = [
        "Left click: Move",
        "Caps Lock: Toggle Run",
        "Space: Attack animation",
        f"Mode: {'RUN' if caps_lock_on else 'WALK'}",
    ]

    for i, line in enumerate(instructions):
        text = font.render(line, True, (20, 40, 20))
        screen.blit(text, (20, 20 + i * 30))

    pygame.display.flip()

pygame.quit()
