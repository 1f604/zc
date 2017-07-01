[Based on Real Time Risk](https://github.com/davidMcneil/Real-Time-Risk)

![Alt text](screenshot.jpg)

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

*Note: Must have python and pygame installed*

## Windows

- open command prompt
- "cd directory"

Run server

- "cd windows-exe\server"
- Run "server.exe arg1 arg2"
  - arg1=port number, perferably choose number greater than 5000
  - arg2=number of clients(players), number between 1 and 4
- ex.) "server.exe 5555 1" this starts a game on port 5555 with 3 players

Connect clients to server

- "cd windows-exe\client"
- Run "client.exe arg1 arg2"
  - arg1 = IP address of  host computer server
  - arg2 = port number, choosen by server
- ex:) "client.exe 127.0.0.1 5555" connects to local-host on port 5555


*Note: Game only starts after all clients have connected*


# Game Play
- Right click to select contry to move armies from
- Left click to move armies into adjacent country
- Number keys change quantity of armies moved

*Note: The game quickly digresses into manical clicking*
