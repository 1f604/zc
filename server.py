import Queue
import threading
import socket
import sys
import time
import random
import math
import message
import collections
import json
import cProfile as profile

refresh_rate = 0.1  # seconds per refresh
running = True
socks = []
expeditions = []  # ideally want a sorted {time:expedition} dictionary for this


def log(location, message):
    print location, message
    pass


def reachable(a, b, owner):
    # breadth first search to determine if territories a and b are connected
    tovisit = collections.deque([a])
    visited = set()  # these are strings, so you can use a set.
    while tovisit:
        t = tovisit.popleft()
        visited.add(t)
        for n in connection_map[t]:
            if n == b:
                return True
            if n not in visited and n not in tovisit \
                    and territory_reference[n].owner == owner:
                tovisit.append(n)
    return False


# Functions for processing messages from clients
# and putting the new world state on each output queue
def can_move(src, dest):
    # Checks to see if two territories are both under same player control
    if reachable(src.name, dest.name, src.owner):
        return True
    # Checks to see if two territories are connected
    for c in connection_map[src.name]:
        if c == dest.name:
            return True
    return False


def battle(a_owner, d_owner, a_troops, d_troops):
    # Battle algorithm
    if a_troops > d_troops:
        winner = a_owner
    else:
        winner = d_owner
    troops = abs(a_troops - d_troops)
    return winner, troops


def get_army_totals():
        army_count = {}
        for territory in territories:
            if territory.owner in army_count:
                c = army_count[territory.owner]
            else:
                c = 0
            army_count[territory.owner] = c + territory.armies
        return army_count


def process_command(command):
    # Executes all commands sent to server
    # (["move", src, dest, armies], and ["add_troops"])
    # log("process command", command)
    if command[0] == "add_troops":
        log("process_command", "adding troops")
        for territory in territories:
            territory.armies += 2
    elif command[0] == "update_quota":
        army_count = get_army_totals()
        for k in army_count:
            if k in quota:
                q = quota[k]
            else:
                q = 0
            quota[k] = min(q + 3 + army_count[k] / 50, army_count[k], 100)
        # print quota
    elif command[0] == "move":
        # When a move command is issued, create an expedition from src to dest,
        # and check every main loop iteration whether the expedition arrived.
        sources = command[1]
        waypoints = command[2]
        pass_thru = command[4]
        for source in sources:
            attacking_troops = command[3]
            src = territory_reference[source]
            print attacking_troops
            if attacking_troops > src.armies:
                attacking_troops = src.armies
            print attacking_troops, "##"
            if attacking_troops > 0:
                print "creating expedition"
                Expedition(src, waypoints, attacking_troops, src.owner,
                           pass_thru)


def get_commands(input_queue):
    # Get list of commands from input queue
    commands = []
    size = input_queue.qsize()
    command = input_queue.get()
    commands.append(command)
    for i in range(size):
        command = input_queue.get()
        commands.append(command)
    return commands


def process_commands(input_queue):
    # Process list of commands
    commands = get_commands(input_queue)
    for command in commands:
        process_command(command)


def get_world_state():
    # Adds territory information to a list
    world_state = ['world']
    for territory in territories:
            world_state.append([territory.name, territory.owner,
                                territory.armies])
    return world_state


def get_world_expeditions():
    # Adds territory information to a list
    world_expeditions = ['expeditions']
    for exp in expeditions:
            world_expeditions.append([exp.owner, [exp.curr, exp.next] +
                                     list(exp.path), exp.troops,
                                     exp.start_time, exp.arrival_time,
                                     exp.color])
    return world_expeditions


def send_new_state(queues):
    # Puts new state on each output_queue
    state = get_world_state()
    world_expeditions = get_world_expeditions()
    for q in queues:
        q.put(state)
    for q in queues:
        q.put(world_expeditions)


# Functions for creating connection to client
def create_listner():
    # Creates socket to listen for clients to be added
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
    # Create a socket to transfer game data
    log("create_connection", "accepting connection")
    sock, add = s.accept()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    log("create_connection", "accepted connection")
    return sock


def check_cmd_valid(command, ID):
    print "checking received command:", command
    if command[0] == "move":
        for name in command[1]:
            src = territory_reference[name]
            if src.owner != ID:
                print "command not valid"
                return False
        return True
    return False
    print "command not valid"


class receive_commands(threading.Thread):
    def __init__(self, input_queue, socket, ID):
        threading.Thread.__init__(self)
        self.socket = socket
        self.input_queue = input_queue
        self.ID = ID

    def run(self):
        while True:
            command = message.recv_message(self.socket)
            if command != '':
                # log("receive_commands", command)
                command = json.loads(command)
                if check_cmd_valid(command, self.ID):
                    self.input_queue.put(command)
            time.sleep(0.1)


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
                else:
                    command[1] = 0
            # log("send_commands", command)
            command = json.dumps(command)
            try:
                    message.send_message(self.socket, command)
            except Exception as e:
                    # self.socket.close()
                    print("# # # # # # # # # ##", e, "exiting game")
                    running = False


def add_client(l, input_queue, client_num):
    # Creates socket and recieve and send thread for each client
    log("add_client", "creating connection")
    sock = create_connection(l)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    global socks
    socks.append(sock)
    first_command = json.dumps(['ID', client_num])
    message.send_message(sock, first_command)
    log("add_client", "starting receiver")
    t1 = receive_commands(input_queue, sock, client_num)
    t1.daemon = True
    t1.start()
    output_queue = Queue.Queue()
    t2 = send_commands(sock, output_queue, client_num)
    t2.daemon = True
    t2.start()
    return output_queue


# Functions for running server
def more_clients(num):
    # Logic to decide to wait for more clients
    return num < int(sys.argv[2])


class new_troops(threading.Thread):
    # Replenishes troops after a set amount of time
    def __init__(self, input_queue):
        threading.Thread.__init__(self)
        self.input_queue = input_queue

    def run(self):
        while 1:
            time.sleep(30)
            log("new_troops", "generating command")
            self.input_queue.put(["add_troops"])


class update_quota(threading.Thread):
    # Replenishes troops after a set amount of time
    def __init__(self, input_queue):
        threading.Thread.__init__(self)
        self.input_queue = input_queue

    def run(self):
        while 1:
            time.sleep(refresh_rate)
            # log("update_quota", "generating command")
            self.input_queue.put(["update_quota"])


def nearest_visible(owner, src, (x, y)):
    # todo: implement fog of war
    src = territory_reference[src]
    nearest = src
    dist = math.hypot(src.x-x, src.y-y)
    for t in territories:
        newdist = math.hypot(t.x-x, t.y-y)
        if newdist < dist:
            dist = newdist
            nearest = t
    return nearest.name


class Expedition():
    def __init__(self, src, waypoints, troops, src_owner, pass_thru):
        self.last = time.time()
        self.pass_thru = pass_thru
        self.src = src
        self.curr = src.name
        self.waypoints = collections.deque(waypoints)
        self.waypoint = self.waypoints.popleft()
        self.troops = troops
        self.owner = src_owner
        self.src.armies -= troops
        expeditions.append(self)
        self.do_arrived()
        self.start_time = time.time()
        if src_owner == 1:
            self.color = ((250, 0, 0))
        if src_owner == 2:
            self.color = ((0, 250, 0))
        if src_owner == 3:
            self.color = ((0, 0, 250))
        if src_owner == 4:
            self.color = ((250, 0, 250))

    def compute_path(self, dest):
        # todo: implement fog of war
        owned = {t.name for t in territories if t.owner == self.owner}
        if self.pass_thru:
            # allowed = seen[self.owner]  # can go to any seen zone
            allowed = {t.name for t in territories}
        else:
            allowed = {dest} | owned  # can only go thru own zones
            if not reachable(self.curr, dest, self.owner):
                return collections.deque([self.curr])
            # allowed = {t.name for t in territories}
        unvisited = {node: None for node in allowed}  # using None as +inf
        prev = {node: None for node in allowed}
        visited = {}
        current = self.curr
        currentDistance = 0
        unvisited[current] = currentDistance
        while True:  # from https://stackoverflow.com/questions/22897209
            for neighbour, distance in edges[current].items():
                if neighbour not in unvisited:
                    continue
                newDistance = currentDistance + distance
                if unvisited[neighbour] is None or\
                   unvisited[neighbour] > newDistance:
                    unvisited[neighbour] = newDistance
                    prev[neighbour] = current
            visited[current] = currentDistance
            del unvisited[current]
            if not unvisited or current == dest:
                break
            candidates = [node for node in unvisited.items() if node[1]]
            if not candidates:
                break
            current, currentDistance = \
                sorted(candidates, key=lambda x: x[1])[0]
        path = collections.deque()
        u = dest
        while prev[u]:
            path.appendleft(u)
            u = prev[u]
        if not path:
            path = collections.deque([current])
        return path

    def __str__(self):
        return "expedition from " + self.src.name + " to " + self.next +\
                   " with " + str(self.troops) + " troops arriving at " + \
                   str(self.arrival_time) + " owned by " + str(self.owner)

    def go_next(self):
        self.next = self.path.popleft()
        dist = edges[self.curr][self.next]
        self.start_time = time.time()
        self.arrival_time = time.time() + dist * 0.02
        self.exp_battle()

    def exp_battle(self):
        es = [e for e in expeditions if e.curr == self.next
              and e.next == self.curr and e.owner != self.owner]
        for e in es:
            print "fighting:", e, self
            diff = e.troops - self.troops
            if diff == 0:
                expeditions.remove(e)
                expeditions.remove(self)
                print "both removed"
                return
            elif diff > 0:
                expeditions.remove(self)
                e.troops = diff
                print e, "won", self, "removed"
                return
            elif diff < 0:
                expeditions.remove(e)
                self.troops = -diff
                print self, "won", e, "removed"

    def slow_me(self):
        new_dest = nearest_visible(self.owner, self.curr, self.waypoint)
        while self.curr == new_dest:  # go to next waypoint
            if not self.waypoints:  # no more waypoints, end journey
                territory_reference[self.curr].armies\
                                    += self.troops  # deposit armies at end
                expeditions.remove(self)
                return False
            self.waypoint = self.waypoints.popleft()
            new_dest = nearest_visible(self.owner, self.curr, self.waypoint)
        self.path = self.compute_path(new_dest)
        return True

    def do_arrived(self):
        if not self.slow_me():
            return
        # now we have a waypoint whose nearest is not curr node
        if self.path[0] == self.curr:  # unreachable, end journey
            territory_reference[self.curr].armies\
                                += self.troops  # deposit armies at end
            expeditions.remove(self)
            return
        # print self.curr, self.waypoint, new_dest, self.path
        self.go_next()

    def check_arrived(self):
        if time.time() > self.arrival_time:
            diff = time.time() - self.arrival_time
            if diff > 0.3:
                raise Exception('Exceeded arrival time by ' + str(diff)
                                + ' seconds')
            self.curr = self.next
            if territory_reference[self.curr].owner != self.owner:
                self.do_battle()
            if self in expeditions:
                if self.path:  # not yet reached destination
                    self.go_next()
                else:  # arrived at destination
                    self.do_arrived()

    def do_battle(self):
            print "expedition from", self.src.name, "to", \
                  self.next, "arrived at", time.time()
            # do battle, set new army value on destination territory
            dest = territory_reference[self.curr]
            winner, troops = battle(self.owner, dest.owner,
                                    self.troops, dest.armies)
            dest.owner = winner
            if winner == self.owner:
                dest.armies = 0
                self.troops = troops
            else:
                dest.armies = troops
                expeditions.remove(self)


def assign_territories(n):
    # Randomly assigns territories to each player
    each = math.ceil(len(territories)/n)
    log("assign_territories", "each should have: " + str(each))
    a = {}
    for i in range(1, n+1):
        a[i] = 0
    for territory in territories:
        x = random.randint(1, n+0)
        while a[x] >= each:
            x = random.randint(1, n+0)
        territory.owner = x
        log("assign_territories", "assigned " + territory.name + " to " +
            str(territory.owner))
        territory.armies = 3
        a[x] = a[x]+1
        log("assign_territories", a)


def check_timers():
    check_expeditions()


def check_expeditions():
    global expeditions
    for expedition in expeditions:  # this is disgustingly inefficient
        expedition.check_arrived()


def start_game(input_queue, queues):
    # Starts send and receive threads for each client
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
        check_timers()
        send_new_state(queues)
    print("TIME TO END!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    for sock in socks:
        try:
            final_cmd = json.dumps(['end', 0])
            message.send_message(sock, final_cmd)
            print("send final cmd # # # # # # # # ")
            sock.close()
        except:
            pass
    sys.exit()


# Handles the two jobs of the server: client connection, game maintenance
def do_server():
    l = create_listner()
    # Output queue for each client
    queues = []
    input_queue = Queue.Queue()
    log("do_server", "input queue created")
    client = 1
    while more_clients(len(queues)):
        log("do_server", "adding client")
        queue = add_client(l, input_queue, client)
        queues.append(queue)
        client += 1
    log("do_server", "starting game")
    start_game(input_queue, queues)


# Main territory class
class territory():
    def __init__(self, name, owner, armies, x, y):
        territories.append(self)
        self.name = name
        self.owner = owner
        self.armies = armies
        self.x = x
        self.y = y
        territory_reference[self.name] = self
        connection_map[self.name] = []


# List of ever territory
territories = []

quota = {}

# Map with territory.name as key and actual instance as value
territory_reference = {}
# Map used to check if two territories are connected
connection_map = {}
edges = {}
# Level confg read in form file
level_info = eval(open("standard_level.py", 'r').read())
# Add territories
for k in level_info['Territories']:
    pos = level_info['Territories'][k]
    territory(k, 0, 0, pos[0], pos[1])
# Add territory connection information
for pair in level_info['Connections']:
    connection_map[pair[0]].append(pair[1])
    connection_map[pair[1]].append(pair[0])
    src = territory_reference[pair[0]]
    dest = territory_reference[pair[1]]
    dist = math.hypot(src.x-dest.x, src.y-dest.y)
    if pair[0] not in edges:
        edges[pair[0]] = {pair[1]: dist}
    else:
        edges[pair[0]][pair[1]] = dist
    if pair[1] not in edges:
        edges[pair[1]] = {pair[0]: dist}
    else:
        edges[pair[1]][pair[0]] = dist
for key, value in edges.items():
    print key, value

# do_server()


profile.run('do_server()', 'servstats')
