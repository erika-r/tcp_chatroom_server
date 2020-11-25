#reference
#https://stackoverflow.com/questions/34984443/using-select-method-for-client-server-chat-in-python

import select,socket,argparse,threading,os
from client import Client

QUIT = "!quit\n"

instructions = b"Instructions:\n"\
    + b"!rooms to list all rooms\n"\
    + b"!online to show online users\n" \
    + b"!join [room_name] to join/create/switch to a room\n" \
    + b"!instructions to show instructions\n" \
    + b"!quit to quit\n"

class Server:
    def __init__(self,listening_socket,connection_list):
        self.listening_socket = listening_socket
        self.connection_list = connection_list
        self.rooms = {} # {room_name: Room}
        self.client_rooms = {} # {client name: room name}
        print("Server started on {}:{}".format(args.host,args.p))
        print("To shut down server, use the command '!shutdown'\n")        

    def broadcast(self):
        while True:
            #X and Y are not needed
            read_clients, X, Y = select.select(self.connection_list, [], [])     #uses client fileno
            
            for client in read_clients:
                #accepting connections
                if client is self.listening_socket: # new connection, client is a socket
                    new_socket, add = client.accept()
                    new_client = Client(new_socket)
                    self.connection_list.append(new_client)
                    # self.welcome(new_client)
                    new_client.socket.sendall(b"Welcome!\nWhat's your name?\n")

                #pass message to the handler
                else:
                    msg = client.socket.recv(4096)      #4096 == max amount of data to be received
                    if msg:
                        msg = msg.decode().lower()
                        self.handle_msg(client, msg)
                    else:
                        client.socket.close()
                        self.connection_list.remove(client)

    #uses message prefixes to decide how to handle messages
    def handle_msg(self, client, msg):
        print(client.name + " says: " + msg)
        
        if "name:" in msg:
            name = msg.split()[1]
            client.name = name
            print("{} has joined!\n".format(client.name))
            client.socket.sendall(instructions)         #show instructions

        elif "!join" in msg:
            self.join(client,msg)

        elif "!rooms" in msg:
            self.show_rooms(client) 
        
        elif "!online" in msg:
            self.show_active(client) 

        elif "!instructions" in msg:
            client.socket.sendall(instructions)
        
        elif "!quit" in msg:
            # exit_msg = "{} has left :(\n".format(client.name)
            client.socket.sendall(QUIT.encode())        #send to client file
            self.remove_client(client)

        #else broadcast client's message
        else:
            # check if in a room first
            if client.name in self.client_rooms:
                self.rooms[self.client_rooms[client.name]].broadcast(client, msg.encode())
            else:
                msg = "You are currently not in any room! \n" \
                    + "Use !list to see available rooms \n" \
                    + "Or !join [room_name] to create/join a room\n"
                client.socket.sendall(msg.encode())

    def show_rooms(self, client):
        #if there are no rooms
        if len(self.rooms) == 0:
            msg = "There are currently no rooms, create your own!\n" \
                + "You can also use !join [room_name] to create a room.\n"
            client.socket.sendall(msg.encode())
        #else display all rooms and how many clients in each
        else:
            msg = "All rooms:\n"
            msg += "".join([(room + ": " + str(len(self.rooms[room].clients)) + " client(s)\n") for room in self.rooms])
            client.socket.sendall(msg.encode())
    
    #show all online users
    def show_active(self,client):
        clients = [c for c in self.connection_list if c != self.listening_socket]
        msg = "({}) user(s) online\n".format(len(clients))
        if len(clients) > 0:
            msg += "".join(["{}\n".format(c.name) for c in clients])
        client.socket.sendall(msg.encode())

    def join(self,client,msg):
        switch = True   #flag to decide whether user can switch or not
        if len(msg.split()) < 2:
            client.socket.sendall(b"No room chosen, try again!\n")
        else:
            room_name = msg.split()[1]
            if client.name in self.client_rooms:    #check if room exists
                if self.client_rooms[client.name] == room_name:     #check if client is already in the room
                    client.socket.sendall(b"You are already in room " + room_name.encode() + b"\n")
                    switch = False
                else:                   # switch to new room and remove from old room
                    room = self.client_rooms[client.name]
                    self.rooms[room].remove_client(client)
            
            if switch:
                #create new room
                if room_name not in self.rooms:
                    new_room = Room(room_name)
                    self.rooms[room_name] = new_room
                
                #add client to room
                self.rooms[room_name].clients.append(client)
                self.rooms[room_name].welcome(client)
                self.client_rooms[client.name] = room_name
    
    def remove_client(self, client):
        if client.name in self.client_rooms:
            self.rooms[self.client_rooms[client.name]].remove_client(client) 
            del self.client_rooms[client.name]
            exit_msg = "{} has left the room\n".format(client.name)
            client.socket.sendall(exit_msg.encode())

    #shuts down server
    #uses input from terminal
    def shutdown(self):
        while True:
            IN = input()
            if IN == "!shutdown":
                print("\nServer has been shut down\n")
                os._exit(1) #forces shutdown

class Room:
    def __init__(self, name):
        self.clients = [] # a list of sockets
        self.name = name

    def welcome(self, from_client):
        msg = "Hi {}, welcome to {}!\n".format(from_client.name,self.name)
        [client.socket.sendall(msg.encode()) for client in self.clients]
    
    def broadcast(self, from_client, msg):
        msg = from_client.name.encode() + b":" + msg
        [client.socket.sendall(msg) for client in self.clients]

    def remove_client(self, client):
        self.clients.remove(client)
        leave_msg = b"left the room\n"
        self.broadcast(client, leave_msg)       #sends message from client
        print("{} has left the server!".format(client.name))


if __name__ == "__main__":
    #read input from command line
    parser = argparse.ArgumentParser(description='Chatroom Server')
    parser.add_argument('host', default="0.0.0.0",help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=8000,
                        help='TCP port (default 1060)')
    args = parser.parse_args()      #command line arguments

    #create listening socket
    listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listening_socket.setblocking(0)
    listening_socket.bind((args.host,args.p))
    listening_socket.listen(10)

    #create Server
    connection_list = [listening_socket]
    server = Server(listening_socket,connection_list)

    #start threads
    #threads are used so server can be shutdown whenever
    broadcast_thread = threading.Thread(target=Server.broadcast,args=[server]).start()
    shutdown_thread = threading.Thread(target=Server.shutdown,args=[server]).start()
