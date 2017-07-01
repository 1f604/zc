import pygame
from pygame.locals import *
from library import *
import thread, threading, random, socket, sys, message
pygame.init()

def create_connection():
###Establish connection to server
  # create a socket
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # connect to server
  host = sys.argv[1] # server address
  port = int(sys.argv[2]) # server port
  s.connect((host, port))
  return s

class receive_commands(threading.Thread):
  def __init__(self, socket):
    threading.Thread.__init__(self)
    self.socket = socket
  def run(self):
    while True:
        try:
          command = message.recv_message(self.socket)
          if command != '':
            command = eval(command)
            input_queue.put(command)
        except:
          thread.interrupt_main()

class send_commands(threading.Thread):
  def __init__(self, socket):
    threading.Thread.__init__(self)
    self.socket = socket
  def run(self):
    while True:
        try:
              command = output_queue.get()
              command = str(command)
              message.send_message(self.socket, command)
        except:
          thread.interrupt_main()
            

sock = create_connection()
t1 = receive_commands(sock)
t1.daemon = True
t1.start()
t2 = send_commands(sock)
t2.daemon = True
t2.start()

def update_world(new_state):
###Update the territories based on command
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
          pygame.quit() 
          sys.exit()
        

def main(screen):
  ###
  #background = pygame.Surface([width, height])
  #background.fill([0, 0, 0]
  ###Create background
  bg_image= load_image(filepath + "classic_board.jpg")
  screen.blit(bg_image, (0, 0))
  pygame.display.flip()
  ###
  clock = pygame.time.Clock()
  running = True  
  ###Main loop
  while running:
    clock.tick(30)
    process_command()
    for event in pygame.event.get():
      if event.type == QUIT:
        pygame.quit() 
        sys.exit()
      if event.type == KEYDOWN:
        if event.key == K_ESCAPE:
          pygame.quit() 
          sys.exit()
#        if event.key == K_F5:
#          fullscreen = pygame.FULLSCREEN
#          screen = pygame.display.set_mode((width, height), fullscreen)
#          bg_image= load_image(filepath + "classic_board.jpg")
#          screen.blit(bg_image, (0, 0))
#          pygame.display.flip()
#        for num in range(1, 10):
#          key = 'K_' + str(num)
#          if event.key == eval(key):
#            player.troops = num
#        if event.key == K_0:
#          player.troops = 10
      if event.type == pygame.MOUSEBUTTONDOWN:
        for territory in territories:
          territory.move()
    sprites.clear(screen, bg_image)
    time = pygame.time.get_ticks()
    sprites.update(time)
    info.update(time)
    rectlist = sprites.draw(screen)
    pygame.display.update(rectlist)

main(screen)
