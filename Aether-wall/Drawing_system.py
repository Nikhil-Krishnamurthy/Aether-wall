import pygame

#pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True

global font
font = pygame.font.Font(None,20)

def write(text, location, color =("white")):
    screen.blit(font.render(text, True, color), location)

while running:
    #polls for events
    for event in pygame.event.get():
        #runs if the user clicked the x on the window
        if event.type == pygame.QUIT:
            running = False

    #wipes the frame from last frame (according to docs)
    screen.fill("black")

    #render here
    mouse_x, mouse_y = pygame.mouse.get_pos()
    text = str(mouse_x)+":"+str(mouse_y)
    pygame.draw.polygon(screen, "white", [(840, 430), (580,430), (580, 475), (610,560), (680, 650), (680, 720,), (740, 720), (740, 650), (810, 560), (840, 475), (840, 430) ], width=2)

    write(text, (400, 400), "white")
    if(pygame.mouse.get_pressed()[0]):
        pygame.display.toggle_fullscreen()

    #uploads new frame
    pygame.display.flip()

    clock.tick(60)
pygame.quit()