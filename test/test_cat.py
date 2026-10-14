import pygame

from characters.cat import Cat


pygame.init()

screen = pygame.display.set_mode((1672, 940))
pygame.display.set_caption("Test Cat Animation")

clock = pygame.time.Clock()

# Vị trí ban đầu của mèo
cat = Cat(500, 700)

running = True

while running:

    dt = clock.tick(60) / 1000

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            # SPACE: mèo đứng dậy
            if event.key == pygame.K_SPACE:
                cat.stand_up()

            # RIGHT: mèo bắt đầu đi
            elif event.key == pygame.K_RIGHT:
                cat.walk()

    # Cập nhật animation + vị trí mèo
    cat.update(dt)

    # Nền xanh
    screen.fill((100, 180, 100))

    # Vẽ mèo
    cat.draw(screen, (240, 360))

    pygame.display.flip()


pygame.quit()