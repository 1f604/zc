import pygame
import Queue
import os
pygame.init()

# creates screeen#
width = 1000
height = 500
fullscreen = False
screen = pygame.display.set_mode([width, height], fullscreen, 0)
screen.fill((0, 0, 0))

# Sprite groups
sprites = pygame.sprite.LayeredUpdates()
territories = pygame.sprite.Group()

filepath = ""

input_queue = Queue.Queue()
output_queue = Queue.Queue()
owner_color = {
    0: (0, 0, 0),
    1: (250, 0, 0),
    2: (0, 250, 0),
    3: (0, 0, 250),
    4: (250, 0, 250)
}


# Media handeling functions
def load_image(name, colorkey=None):
    fullname = os.path.join(filepath, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print 'Cannot load image:', name
        raise SystemExit(message)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
    image.set_colorkey(colorkey)
    return image


# Game classes and functions
class example(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        pygame.sprite.Sprite.__init__(self)
        sprites.add(self)
        self.x = x
        self.y = y
        self.image = image
        self.image.fill((250, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def update(self, current_time):
        self.rect.center = (self.x, self.y)


class player():
    def __init__(self):
        self.source_country = None
        self.troops = 5
        self.destination_country = None
        self.command = []
        self.ID = None
        self.quota = 0

    def build_command(self):
        self.command = ["move", self.source_country, self.destination_country,
                        self.troops]

    def get_command(self):
        return self.command


class army(pygame.sprite.Sprite):
    def __init__(self, x, y, number):
        pygame.sprite.Sprite.__init__(self)
        sprites.add(self)
        self.x = x
        self.y = y
        self.text = str(number)
        self.default_font = pygame.font.Font(None, 18)
        self.color = (0, 0, 0)
        self.image = self.default_font.render(self.text, True, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.number = number

    def set_troops(self, num):
        self.number = num
        self.text = str(self.number)
        self.default_font = pygame.font.Font(None, 18)
        self.image = self.default_font.render(self.text, True, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def update(self, current_time):
        self.rect.center = (self.x, self.y)
        self.image = self.default_font.render(self.text, True, self.color)


class territory(pygame.sprite.Sprite):
    def __init__(self, name, owner, armies, x, y):
        pygame.sprite.Sprite.__init__(self)
        sprites.add(self)
        territories.add(self)
        self.x = x
        self.y = y
        self.image = pygame.Surface((25, 25))
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.name = name
        self.owner = owner
        self.selected = False
        self.image.fill(owner_color[self.owner])
        self.armies = armies
        self.army = army(self.x, self.y, self.armies)
        sprites.move_to_front(self.army)
        self.update_count = 0

    def move(self):
        # Move armies
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            buttons = pygame.mouse.get_pressed()
            if buttons[0]:
                    player.source_country = self.name
                    for t in territories:
                        t.army.color = (0, 0, 0)
                        t.selected = False  # this might be a bit redundant
                        t.set_color()
                    self.selected = True
                    self.army.color = (255, 255, 255)
                    self.draw_border()
            if buttons[2]:
                    player.destination_country = self.name
                    player.build_command()
                    output_queue.put(player.get_command())

    def draw_border(self):
        rect = self.image.get_rect()
        self.image.fill((255, 255, 255), rect)
        self.image.fill(owner_color[self.owner],
                        rect.inflate(-4, -4))

    def set_color(self):
        if self.selected:
            self.draw_border()
        else:
            self.image.fill(owner_color[self.owner])

    def set_fields(self):
        self.army.set_troops(self.armies)
        self.set_color()

    def update(self, current_time):
        # Build army
        if self.update_count < current_time:
            self.rect.center = (self.x, self.y)
            self.update_time = current_time + 30


class info(pygame.sprite.Sprite):
    def __init__(self, player):
        pygame.sprite.Sprite.__init__(self)
        sprites.add(self)
        self.x = 10
        self.y = 400
        self.player = player
        self.text = self.get_quota()
        self.default_font = pygame.font.Font(None, 24)
        self.color = (255, 255, 255)
        self.image = self.default_font.render(self.text, True, self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x, self.y)
        self.next_update_time = 0

    def get_quota(self):
        quota = str(self.player.quota)
        return "Quota: " + quota

    def update(self, current_time):
        if self.next_update_time <= current_time:
            self.text = self.get_quota()
            self.image = self.default_font.render(self.text, True, self.color)
            self.rect.topleft = self.x, self.y
            self.next_update_time = current_time + 200


class player_stat(pygame.sprite.Sprite):
    def __init__(self, ID, x, y):
        pygame.sprite.Sprite.__init__(self)
        sprites.add(self)
        self.ID = ID
        self.x = x
        self.y = y
        self.text = self.get_stat()
        self.default_font = pygame.font.Font(None, 24)
        if self.ID == 1:
            self.color = ((250, 0, 0))
        if self.ID == 2:
            self.color = ((0, 250, 0))
        if self.ID == 3:
            self.color = ((0, 0, 250))
        if self.ID == 4:
            self.color = ((250, 0, 250))
        self.image = self.default_font.render(self.text, True, self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x, self.y)
        self.next_update_time = 0

    def get_stat(self):
        armies = 0
        ts = 0
        for t in territories:
            if t.owner == self.ID:
                armies += t.armies
        ts += 1
        return "Territories: " + str(ts) + "Armies:" + str(armies)

    def update(self, current_time):
        if self.next_update_time <= current_time:
            self.text = self.get_stat()
            self.image = self.default_font.render(self.text, True, self.color)
            self.rect.topleft = self.x, self.y
            self.next_update_time = current_time + 200


# Instances of game classes
player = player()
info = info(player)
stat1 = player_stat(1, 10, 420)
stat2 = player_stat(2, 10, 440)
stat3 = player_stat(3, 10, 460)
stat4 = player_stat(4, 10, 480)

level_info = eval(open("standard_level.py", 'r').read())
for k in level_info['Territories']:
    pos = level_info['Territories'][k]
    territory(k, 0, 0, pos[0], pos[1])
