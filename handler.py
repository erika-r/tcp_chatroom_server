
import socket

MAX_CLIENTS = 30
QUIT = "!quit\n"

def create_socket(address):
    host,port = address[0],address[1]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind(address)
    s.listen(MAX_CLIENTS)
    print("Server started on {}:{}\n".format(host,port))
    return s

class Lobby:
    def __init__(self):
        self.rooms = {} # {room_name: Room}
        self.room_player_map = {} # {playerName: roomName}

    def welcome(self, new_player):
        new_player.socket.sendall(b"Welcome!\nPlease tell us your name:\n")

    def show_rooms(self, player):
        if len(self.rooms) == 0:
            msg = "There are currently no active rooms, create your own!\n" \
                + "You can also use !join [room_name] to create a room.\n"
            player.socket.sendall(msg.encode())
        else:
            msg = "All rooms:\n"
            #display all rooms and how many players in each
            for room in self.rooms:
                msg += room + ": " + str(len(self.rooms[room].players)) + " player(s)\n"
            player.socket.sendall(msg.encode())
    
    def join(self,player,msg):
        same_room = False
        if len(msg.split()) < 2:
            player.socket.sendall(b"No room chosen, try again!\n")
        elif len(msg.split()) >= 2: # error check
            room_name = msg.split()[1]
            if player.name in self.room_player_map: # switching?
                if self.room_player_map[player.name] == room_name:
                    player.socket.sendall(b"You are already in room: " + room_name.encode())
                    same_room = True
                else: # switch
                    old_room = self.room_player_map[player.name]
                    self.rooms[old_room].remove_player(player)
            if not same_room:
                if not room_name in self.rooms: # new room:
                    new_room = Room(room_name)
                    self.rooms[room_name] = new_room
                self.rooms[room_name].players.append(player)
                self.rooms[room_name].welcome(player)
                self.room_player_map[player.name] = room_name
        else:
            player.socket.sendall(instructions)


    def handle_msg(self, player, msg):
        instructions = b"Instructions:\n"\
            + b"!list to list all rooms\n"\
            + b"!join [room_name] to join/create/switch to a room\n" \
            + b"!instructions to show instructions\n" \
            + b"!quit to quit\n"

        print(player.name + " says: " + msg)
        if "name:" in msg:
            name = msg.split()[1]
            player.name = name
            print("{} has joined!\n".format(player.name))
            player.socket.sendall(instructions)         #show instructions

        elif "!join" in msg:
            self.join(player,msg)

        elif "!list" in msg:
            self.show_rooms(player) 

        elif "!instructions" in msg:
            player.socket.sendall(instructions)
        
        elif "!quit" in msg:
            # exit_msg = "{} has left :(\n".format(player.name)
            player.socket.sendall(QUIT.encode())        #send to client file
            self.remove_player(player)

        #else broadcast client's message
        else:
            # check if in a room or not first
            if player.name in self.room_player_map:
                self.rooms[self.room_player_map[player.name]].broadcast(player, msg.encode())
            else:
                msg = "You are currently not in any room! \n" \
                    + "Use [!list] to see available rooms \n" \
                    + "Or [!join room_name] to create/join a room\n"
                player.socket.sendall(msg.encode())
    
    def remove_player(self, player):
        if player.name in self.room_player_map:
            self.rooms[self.room_player_map[player.name]].remove_player(player) 
            del self.room_player_map[player.name]
            exit_msg = "{} has left the room\n".format(player.name)
            player.socket.sendall(exit_msg.encode())

    
class Room:
    def __init__(self, name):
        self.players = [] # a list of sockets
        self.name = name

    def welcome(self, from_player):
        msg = "Hi {}, welcome to {}!\n".format(from_player.name,self.name)
        for player in self.players:
            player.socket.sendall(msg.encode())
    
    def broadcast(self, from_player, msg):
        msg = from_player.name.encode() + b":" + msg
        for player in self.players:
            player.socket.sendall(msg)

    def remove_player(self, player):
        self.players.remove(player)
        leave_msg = b"left the room\n"
        self.broadcast(player, leave_msg)

class Player:
    def __init__(self, socket, name = "new"):
        socket.setblocking(0)
        self.socket = socket
        self.name = name

    #used for select.select
    def fileno(self):
        return self.socket.fileno()