import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
from library import (territories, input_queue, output_queue, player,
                     load_image, filepath, sprites, info, screen, width,
                     height)
# import thread
import threading
import socket
import sys
import message

FPS = 90
pygame.init()
font = pygame.font.Font(None, 36)
text = font.render("Game over: A player has disconnected", True, (255, 0, 250))
end = False
BLACK = (0,   0,   0)
WHITE = (255, 255, 255)
BLUE = (0,   0, 255)
GREEN = (0, 255,   0)
RED = (255,   0,   0)


def create_connection():  # Establish connection to server
    # create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to server
    host = sys.argv[1]  # server address
    port = int(sys.argv[2])  # server port
    s.connect((host, port))
    return s


class receive_commands(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket

    def run(self):
        while True:
                command = message.recv_message(self.socket)
                if command != '':
                    command = eval(command)
                    input_queue.put(command)


class send_commands(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket

    def run(self):
        while True:
                command = output_queue.get()
                command = str(command)
                message.send_message(self.socket, command)


sock = create_connection()
t1 = receive_commands(sock)
t1.daemon = True
t1.start()
t2 = send_commands(sock)
t2.daemon = True
t2.start()


def update_world(new_state):
    # Update the territories based on command
    for territory in territories:
        for command in new_state[1:len(new_state)]:
            if command[0] == territory.name:
                territory.owner = command[1]
                territory.armies = command[2]
                territory.set_fields()


def process_command():
    size = input_queue.qsize()
    if size > 0:
        for i in range(size):
            command = input_queue.get()
            if command[0] == 'ID':
                player.ID = command[1]
            elif command[0] == 'world':
                update_world(command)
            elif command[0] == 'quota':
                player.quota = command[1]
            elif command[0] == 'end':
                print "#####################received end command##############"
                global end
                end = True


def main(screen):
    # Create background
    bg_image = load_image(filepath + "classic_board.jpg")
    screen.blit(bg_image, (0, 0))
    pygame.display.flip()
    ###
    clock = pygame.time.Clock()
    running = True
    draw_new_selection_box = False
    selection_completed = False
    # Main loop
    while running:
        clock.tick(FPS)
        process_command()
        for event in pygame.event.get():
            buttons = pygame.mouse.get_pressed()
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN \
                    and not pygame.key.get_mods() & pygame.KMOD_SHIFT \
                    and buttons[0]:  # left click without shift
                for t in territories:
                    t.selected = False
                    t.move()
                draw_new_selection_box = True
                leftclick_down_location = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN \
                    and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                # shift right click select toggle
                for t in territories:
                    if t.rect.collidepoint(pygame.mouse.get_pos()):
                        if buttons[2]:
                            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                t.selected = not t.selected
            if event.type == pygame.MOUSEBUTTONUP \
                    and not buttons[0]:
                draw_new_selection_box = False
                selection_completed = True
                leftclick_up_location = pygame.mouse.get_pos()
        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
            # shift left mousebutton drag select
            for t in territories:
                if t.rect.collidepoint(pygame.mouse.get_pos()):
                    buttons = pygame.mouse.get_pressed()
                    if buttons[0]:
                        t.selected = True
                        t.army.color = (255, 255, 255)
                        t.draw_border()
        # use event variables to change variables
        cur_mouse_loc = pygame.mouse.get_pos()
        if draw_new_selection_box:
            selection_box_x = cur_mouse_loc[0] - leftclick_down_location[0]
            selection_box_y = cur_mouse_loc[1] - leftclick_down_location[1]
            selection_box = pygame.Rect((leftclick_down_location),
                                        (selection_box_x, selection_box_y))
            print "selection box:", selection_box_x, selection_box_y
        elif selection_completed:
            completed_selection_box_x = leftclick_up_location[0]\
                                        - leftclick_down_location[0]
            completed_selection_box_y = leftclick_up_location[1]\
                - leftclick_down_location[1]
            completed_selection_box = pygame.Rect((leftclick_down_location),
                                                  (completed_selection_box_x,
                                                  completed_selection_box_y))

        if not end:
            sprites.clear(screen, bg_image)
            time = pygame.time.get_ticks()
            sprites.update(time)
            info.update(time)
            screen.blit(bg_image, (0, 0))
            sprites.draw(screen)
            # draw selection box
            if draw_new_selection_box:
                pygame.draw.rect(screen, GREEN, selection_box, 1)
                for t in territories:
                    if selection_box.colliderect(t.rect):
                        t.selected = True
                    else:
                        t.selected = False
            pygame.display.update()
        else:
            screen.blit(text, ((width-text.get_width())//2,
                        height-text.get_height()))
            pygame.display.flip()


main(screen)
