import Queue, thread, threading, socket, sys, time, random, math, message

refresh_rate = 0.1 #seconds per refresh
running = True
socks = []

def log(location, message):
  print location, message
  pass

###Functions for processing messages from clients and putting the new world state on each output queue
def territory_connected(t_a, t_b):
###Checks to see if two territories are connected
  for c in connection_map[t_a]:
    if c == t_b:
      return True
  else: return False

def battle(a_troops, d_troops):
###Battle algorithum
  a_troops = a_troops
  d_troops = d_troops
  while a_troops > 0 and d_troops > 0:
    num = random.randint(1, 100)
    if num <= 30:
      d_troops -= 2
    if num > 30 and num <= 50:
      a_troops -= 2
    if num > 50:
      a_troops -= 1
      d_troops -=1
    if a_troops < 0:
      a_troops = 0
    if d_troops < 0:
      d_troops = 0
  return a_troops, d_troops

def get_army_totals():
    army_count = {}    
    for territory in territories:
      if territory.owner in army_count:
        c = army_count[territory.owner]
      else: c = 0
      army_count[territory.owner] = c + territory.armies
    return army_count

def process_command(command):
###Evaluates all commands sent to server(["move", source, destination, armies], and ["add_troops"])
  log("process command", command)
  if command[0] == "add_troops":
    log("process_command", "adding troops")
    for territory in territories:
      territory.armies += 2
  elif command[0] == "update_quota":
    army_count = get_army_totals()
    for k in army_count:
      if k in quota:
        q = quota[k]
      else: q = 0
      quota[k] = min(q + 3 + army_count[k] / 50, army_count[k], 100)
    print quota
  elif command[0] == "move": 
    source = territory_reference[command[1]]
    destination = territory_reference[command[2]]
    attacking_troops = command[3]
    if territory_connected(source.name, destination.name):
      if source.owner in quota and quota[source.owner] >= attacking_troops:
        if attacking_troops > source.armies:
          attacking_troops = source.armies
        quota[source.owner] = quota[source.owner] - attacking_troops
        if source.owner == destination.owner:
          source.armies -= attacking_troops
          destination.armies += attacking_troops
        elif source.owner != destination.owner:
          source_troops, destination_troops = battle(attacking_troops, destination.armies)
          source.armies -= attacking_troops - source_troops
          destination.armies = destination_troops
          if destination.armies == 0 and attacking_troops > 0:
            destination.owner = source.owner
            destination.armies = source_troops
            source.armies -= source_troops
      else: print "rejected", quota

def get_commands(input_queue):
###Get list of commands from input queue
  commands = []
  command = input_queue.get()
  commands.append(command)
  size = input_queue.qsize()
  for i in range(size):
    command = input_queue.get()
    commands.append(command)
  return commands  

def process_commands(input_queue):
###Process list of commands
  commands = get_commands(input_queue)
  for command in commands:
    process_command(command)

def get_world_state():
###Adds territory information to a list
  world_state = ['world']
  for territory in territories:
      world_state.append([territory.name, territory.owner, territory.armies])
  return world_state

def send_new_state(queues):
###Puts new state on each output_queue
  state = get_world_state()
  for q in queues:
    q.put(state)
  for q in queues:
    q.put(["quota", quota])
    
###Functions for creating connection to client
def create_listner():
###Creates socket to listen for clients to be added
  # create a socket
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  # associate the socket with a port
  host = ''
  port = int(sys.argv[1])
  s.bind((host, port))
  # accept "call" from client
  s.listen(1)
  return s

def create_connection(s):
###Create a socket to transfer game data
  log("create_connection", "accepting connection")
  sock, add = s.accept()
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  log("create_connection", "accepted connection")
  return sock

class receive_commands(threading.Thread):
  def __init__(self, input_queue, socket):
    threading.Thread.__init__(self)
    self.socket = socket
    self.input_queue = input_queue
  def run(self):
    while True:
      command = message.recv_message(self.socket)
      if command != '':
        log("receive_commands", command)
        command = eval(command)
        self.input_queue.put(command)

class send_commands(threading.Thread):
  def __init__(self, socket, output_queue, ID):
    threading.Thread.__init__(self)
    self.socket = socket
    self.output_queue = output_queue
    self.ID = ID
  def run(self):
    global running
    while True:
      command = self.output_queue.get()
      if command[0] == "quota":
        if self.ID in command[1]:
          command[1] = command[1][self.ID]
        else: command[1] = 0
      log("send_commands", command)
      command = str(command)
      try:
          message.send_message(self.socket, command)
      except Exception as e: 
          #self.socket.close()
          print("#############################",e, "exiting game")
          running = False

def add_client(l, input_queue, client_num):
###Creates socket and recieve and send thread for each client
  log("add_client", "creating connection")
  sock = create_connection(l)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  global socks
  socks.append(sock)
  first_command = str(['ID',client_num])
  message.send_message(sock, first_command)
  log("add_client", "starting receiver")
  t1 = receive_commands(input_queue, sock)
  t1.daemon = True
  t1.start()
  output_queue = Queue.Queue()
  t2 = send_commands(sock, output_queue, client_num)
  t2.daemon = True
  t2.start()
  return output_queue

###Functions for running server
def more_clients(num):
###Logic to decide to wait for more clients  
  return num < int(sys.argv[2])

class new_troops(threading.Thread):
###Replenishes troops after a set amount of time
  def __init__(self, input_queue):
    threading.Thread.__init__(self)
    self.input_queue = input_queue
  def run(self):
    while 1:
      time.sleep(30)
      log("new_troops", "generating command")
      self.input_queue.put(["add_troops"])

class update_quota(threading.Thread):
###Replenishes troops after a set amount of time
  def __init__(self, input_queue):
    threading.Thread.__init__(self)
    self.input_queue = input_queue
  def run(self):
    while 1:
      time.sleep(refresh_rate)
      log("update_quota", "generating command")
      self.input_queue.put(["update_quota"])

def assign_territories(n):
###Randomly assigns territories to each player
  each = math.ceil(len(territories)/n)
  log ("assign_territories", "each should have: " + str(each))
  a = {} 
  for i in range(1,n+1):
   a[i] = 0
  for territory in territories:
    x = random.randint(1, n+0)
    while a[x] >= each:
      x = random.randint(1, n+0)
    territory.owner = x
    log("assign_territories", "assigned " + territory.name + " to " + str(territory.owner) )
    territory.armies = 3
    a[x] = a[x]+1
    log( "assign_territories", a )

def start_game(input_queue, queues):
###Starts send and receive threads for each client
  log("start_game", "starting new_troops thread")
  assign_territories(len(queues))
  t1 = new_troops(input_queue)
  t1.daemon = True
  t1.start()
  t2 = update_quota(input_queue)
  t2.daemon = True
  t2.start()
  send_new_state(queues) 
  while running:
    process_commands(input_queue)
    send_new_state(queues)
  print("TIME TO END!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
  for sock in socks: 
      final_cmd = str(['end',0])
      message.send_message(sock, final_cmd) 
      print("send final cmd ########################")
      sock.close()
  sys.exit()             

###Handles the two jobs of the server: client connection, game maintenance
def do_server():
  l = create_listner()
  ###Output queue for each client
  queues = []
  input_queue = Queue.Queue()
  log( "do_server", "input queue created")
  client = 1
  while more_clients(len(queues)):
    log( "do_server", "adding client")
    queue = add_client(l, input_queue, client)
    queues.append(queue)
    client += 1
  log( "do_server", "starting game")
  start_game(input_queue, queues)

###Main territory class
class territory():
  def __init__(self, name, owner, armies):
    territories.append(self)
    self.name = name
    self.owner = owner
    self.armies = armies
    territory_reference[self.name] = self
    connection_map[self.name] = []

###List of ever territory
territories = []

quota = {}

###Map with territory.name as key and actual instance as value
territory_reference = {}
###Map used to check if two territories are connected
connection_map = {}
###Level confg read in form file
level_info = eval(open("standard_level.py", 'r').read())
###Add territories
for k in level_info['Territories']:
  territory(k, 0, 0)
###Add territory connection information
for pair in level_info['Connections']:
  connection_map[pair[0]].append(pair[1])
  connection_map[pair[1]].append(pair[0])

do_server()





