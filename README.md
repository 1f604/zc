Based on [Real Time Risk by davidMcneil](https://github.com/davidMcneil/Real-Time-Risk)

![Alt text](screenshot.png)

*Note: Must have python and pygame installed*

# To Start Game:

- unzip directory into desired location, this path is hence called directory

## Linux

- open terminal
- "cd directory"

Start a server:

- run "python server.py arg1 arg2"
  - arg1 = port number
  - arg2 = number of players 1-4
- ex.) "python server.py 5555 3" starts game on port 5555 with 3 players

Start specified number of clients one for each player:

- run "python client.py arg1 arg2"
  - arg1 = port number same as server
  - arg2 = host machines IP address
- ex.) "python client.py 127.0.0.1 5555" connects to local-host on port 5555

*Note: Game only starts after all clients have connected*

# Game Play
- Left click to select country to move armies from
- Right click to move armies into target country
- Left click and drag for selection box (only selects own countries by default)
- Shift-left click and drag for freeform selection
- Shift-right click and drag for freeform deselection
- Ctrl-backquote (the \` symbol) to switch between own-territory select and enemy territory select modes
- Ctrl-tab to switch between pass-through enemy territory mode and pass-through own territory modes
- (deprecated) Number keys change quantity of armies moved

# IMPORTANT
- Server receive thread runs once every 0.1 seconds which means if you click too quickly then the clicks (move commands) simply won't be registered by the server. 

*Note: The game quickly digresses into maniacal clicking*
