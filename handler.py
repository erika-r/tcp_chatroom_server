import socket

QUIT = "!quit\n"

instructions = b"Instructions:\n"\
    + b"!list to list all rooms\n"\
    + b"!join [room_name] to join/create/switch to a room\n" \
    + b"!instructions to show instructions\n" \
    + b"!quit to quit\n"


#every user is a socket
class User:
    def __init__(self, socket, name = "new"):
        socket.setblocking(0)
        self.socket = socket
        self.name = name

    #used for select.select
    def fileno(self):
        return self.socket.fileno()

class Lobby:
    def __init__(self):
        self.rooms = {} # {room_name: Room}
        self.user_rooms = {} # {user name: room name}

    def welcome(self, user):
        user.socket.sendall(b"Welcome!\nWhat's your name?\n")

    def show_rooms(self, user):
        #if there are no rooms
        if len(self.rooms) == 0:
            msg = "There are currently no active rooms, create your own!\n" \
                + "You can also use !join [room_name] to create a room.\n"
            user.socket.sendall(msg.encode())
        #else display all rooms and how many users in each
        else:
            msg = "All rooms:\n"
            msg += "".join([(room + ": " + str(len(self.rooms[room].users)) + " user(s)\n") for room in self.rooms])
            user.socket.sendall(msg.encode())
    
    def join(self,user,msg):
        same_room = False
        if len(msg.split()) < 2:
            user.socket.sendall(b"No room chosen, try again!\n")
        else:
            room_name = msg.split()[1]
            if user.name in self.user_rooms:    #check if room exists
                if self.user_rooms[user.name] == room_name:     #check if user is already in the room
                    user.socket.sendall(b"You are already in room " + room_name.encode() + b"\n")
                    same_room = True
                else:                   # switch to new room and remove from old room
                    old_room = self.user_rooms[user.name]
                    self.rooms[old_room].remove_user(user)
            
            if not same_room:
                #create new room
                if room_name not in self.rooms:
                    new_room = Room(room_name)
                    self.rooms[room_name] = new_room
                
                #add user to room
                self.rooms[room_name].users.append(user)
                self.rooms[room_name].welcome(user)
                self.user_rooms[user.name] = room_name

    #uses message prefixes to decide how to handle messages
    def handle_msg(self, user, msg):
        print(user.name + " says: " + msg)
        
        if "name:" in msg:
            name = msg.split()[1]
            user.name = name
            print("{} has joined!\n".format(user.name))
            user.socket.sendall(instructions)         #show instructions

        elif "!join" in msg:
            self.join(user,msg)

        elif "!list" in msg:
            self.show_rooms(user) 

        elif "!instructions" in msg:
            user.socket.sendall(instructions)
        
        elif "!quit" in msg:
            # exit_msg = "{} has left :(\n".format(user.name)
            user.socket.sendall(QUIT.encode())        #send to client file
            self.remove_user(user)

        #else broadcast client's message
        else:
            # check if in a room first
            if user.name in self.user_rooms:
                self.rooms[self.user_rooms[user.name]].broadcast(user, msg.encode())
            else:
                msg = "You are currently not in any room! \n" \
                    + "Use !list to see available rooms \n" \
                    + "Or !join [room_name] to create/join a room\n"
                user.socket.sendall(msg.encode())
    
    def remove_user(self, user):
        if user.name in self.user_rooms:
            self.rooms[self.user_rooms[user.name]].remove_user(user) 
            del self.user_rooms[user.name]
            exit_msg = "{} has left the room\n".format(user.name)
            user.socket.sendall(exit_msg.encode())

class Room:
    def __init__(self, name):
        self.users = [] # a list of sockets
        self.name = name

    def welcome(self, from_user):
        msg = "Hi {}, welcome to {}!\n".format(from_user.name,self.name)
        [user.socket.sendall(msg.encode()) for user in self.users]
    
    def broadcast(self, from_user, msg):
        msg = from_user.name.encode() + b":" + msg
        [user.socket.sendall(msg) for user in self.users]

    def remove_user(self, user):
        self.users.remove(user)
        leave_msg = b"left the room\n"
        self.broadcast(user, leave_msg)       #sends message from user
        print("{} has left the server!".format(user.name))
