import pygame

from characters.cat import Cat


pygame.init()

screen = pygame.display.set_mode((1672, 940))
pygame.display.set_caption("Test Cat")

clock = pygame.time.Clock()

cat = Cat(500, 500)

running = True

while running:

    dt = clock.tick(60) / 1000

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            # SPACE: nhổm dậy
            if event.key == pygame.K_SPACE:
                cat.stand_up()

            # RIGHT: bắt đầu đi
            if event.key == pygame.K_RIGHT:
                cat.walk()

    cat.update(dt)

    screen.fill((100, 180, 100))

    cat.draw(screen, (240, 360))

    pygame.display.flip()


pygame.quit()