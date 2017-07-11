import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_BACKQUOTE, K_TAB
from library import (territories, input_queue, output_queue, player,
                     load_image, filepath, sprites, info, screen, width,
                     height, selecteds, territory_reference)
# import thread
import colors
import threading
import socket
import sys
import message
import json
import time

FPS = 90
pygame.init()
font = pygame.font.Font(None, 36)
text = font.render("Game over: A player has disconnected", True, (255, 0, 250))
end = False
expeditions = []


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
                command = json.loads(command)
                input_queue.put(command)


class send_commands(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket

    def run(self):
        while True:
                command = output_queue.get()
                data_string = json.dumps(command)
                message.send_message(self.socket, data_string)


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


def update_expeditions(new_state):
    # Update the expeditions based on command
    global expeditions
    expeditions = new_state[1:]
    # print expeditions


def process_command():
    size = input_queue.qsize()
    if size > 0:
        for i in range(size):
            command = input_queue.get()
            if command[0] == 'ID':
                player.ID = command[1]
                player.assign_color()
            elif command[0] == 'world':
                update_world(command)
            elif command[0] == 'expeditions':
                update_expeditions(command)
            elif command[0] == 'end':
                print "#####################received end command##############"
                global end
                end = True


def select(t, own_select):
    if (own_select and t.owner == player.ID) or \
       (not own_select and t.owner != player.ID):
            t.selected = True
            selecteds.add(t)


def deselect(t):
    t.selected = False
    selecteds.discard(t)


def draw_paths():
    for ex in expeditions:
        path = ex[1]
        points = []
        curr = territory_reference[path[0]]
        nxt = territory_reference[path[1]]
        pnt1 = (nxt.x, nxt.y)
        diffx = (nxt.x - curr.x)
        diffy = (nxt.y - curr.y)
        difftime = ex[4] - ex[3]
        diffnow = ex[4] - time.time()
        r = 1 - diffnow / float(difftime)
        startx = r * diffx + curr.x
        starty = r * diffy + curr.y
        pnt0 = (int(startx), int(starty))
        pygame.draw.circle(screen, ex[5], pnt0, 5, 0)
        pygame.draw.line(screen, ex[5], pnt0, pnt1, 1)
        if len(path) > 2:
            for name in path[1:]:
                x = territory_reference[name].x
                y = territory_reference[name].y
                points.append((x, y))
            pygame.draw.lines(screen, ex[5], False, points, 1)


def draw_cross(color, (x, y), width):
    p0 = (x-3, y-3)
    p1 = (x+3, y+3)
    p2 = (x-3, y+3)
    p3 = (x+3, y-3)
    pygame.draw.line(screen, color, p0, p1, width)
    pygame.draw.line(screen, color, p2, p3, width)


def draw_points(waypoints):
    for ex in expeditions:
        for waypoint in ex[6]:
            draw_cross(ex[5], waypoint, 2)
    for waypoint in waypoints:
        draw_cross(colors.WHITE, waypoint, 2)


def main(screen):
    # Create background
    bg_image = load_image(filepath + "classic_board.jpg")
    screen.blit(bg_image, (0, 0))
    pygame.display.flip()
    ###
    clock = pygame.time.Clock()
    running = True
    draw_new_selection_box = False
    own_select = True
    pass_thru = False
    setting_waypoints = False
    waypoints = []
    # Main loop
    while running:
        clock.tick(FPS)
        process_command()
        for event in pygame.event.get():
            buttons = pygame.mouse.get_pressed()
            keys = pygame.key.get_pressed()
            mods = pygame.key.get_mods()
            shift = mods & pygame.KMOD_SHIFT
            ctrl = mods & pygame.KMOD_CTRL
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if ctrl:
                    setting_waypoints = True
                    print setting_waypoints
            if event.type == pygame.KEYUP:
                if not ctrl:
                    setting_waypoints = False
                    print setting_waypoints
                    if waypoints:
                        for s in selecteds:
                            s.move(waypoints, pass_thru)
                    waypoints = []
            if event.type == pygame.MOUSEBUTTONDOWN \
                    and not shift and buttons[0]:
                    # left click without shift, start box
                draw_new_selection_box = True
                leftclick_down_location = pygame.mouse.get_pos()

            if keys[K_BACKQUOTE] and ctrl:
                own_select = not own_select
                print "territory select inverted"

            if keys[K_TAB] and ctrl:
                pass_thru = not pass_thru
                print "pass thru enemy territory inverted"

            if event.type == pygame.MOUSEBUTTONDOWN \
                    and not shift and buttons[2] and not setting_waypoints:
                    # right click without shift, move armies
                waypoints = [pygame.mouse.get_pos()]
                # move armies from selected zones ot target
                for s in selecteds:
                    s.move(waypoints, pass_thru)
                waypoints = []

            if event.type == pygame.MOUSEBUTTONDOWN \
                    and not shift and buttons[2] and setting_waypoints:
                    # right click without shift, move armies
                waypoints.append(pygame.mouse.get_pos())

            if event.type == pygame.MOUSEBUTTONUP \
                    and not buttons[0]:
                draw_new_selection_box = False

        if shift:
            # shift left mousebutton drag select
            for t in territories:
                if t.rect.collidepoint(pygame.mouse.get_pos()):
                    buttons = pygame.mouse.get_pressed()
                    if buttons[0]:
                        select(t, own_select)
                        t.army.color = (255, 255, 255)
                    if buttons[2]:
                        deselect(t)
                        t.army.color = (0, 0, 0)
                    t.set_color()
        # use event variables to change variables
        cur_mouse_loc = pygame.mouse.get_pos()
        if draw_new_selection_box:
            selection_box_x = cur_mouse_loc[0] - leftclick_down_location[0]
            selection_box_y = cur_mouse_loc[1] - leftclick_down_location[1]
            selection_box = pygame.Rect((leftclick_down_location),
                                        (selection_box_x, selection_box_y))

        if not end:
            sprites.clear(screen, bg_image)
            time = pygame.time.get_ticks()
            sprites.update(time)
            info.update(time)
            screen.blit(bg_image, (0, 0))
            draw_paths()
            sprites.draw(screen)
            draw_points(waypoints)
            # draw selection box
            if draw_new_selection_box:
                pygame.draw.rect(screen, colors.GREEN, selection_box, 1)
                selection_box.normalize()
                for t in territories:
                    deselect(t)
                    if selection_box.colliderect(t.rect):
                        select(t, own_select)
            pygame.display.update()
        else:
            screen.blit(text, ((width-text.get_width())//2,
                        height-text.get_height()))
            pygame.display.flip()


main(screen)
