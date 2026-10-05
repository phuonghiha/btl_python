import pygame

from characters.frog import Frog


pygame.init()

screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Test Frog")

clock = pygame.time.Clock()

frog = Frog(500, 300)

running = True

while running:

    dt = clock.tick(60) / 1000

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_LEFT:
                frog.turn_left()

            if event.key == pygame.K_RIGHT:
                frog.turn_right()

            if event.key == pygame.K_SPACE:
                frog.jump()

            if event.key == pygame.K_a:
                frog.attack()
            if event.key== pygame.K_s:
                frog.idle()

    frog.update(dt)

    screen.fill((100, 180, 100))

    frog.draw(screen,(160,160))

    pygame.display.flip()

pygame.quit()