
import select,socket,argparse,threading,os
from client import Client

#all commands 
instructions = "Instructions:\n"\
    + "!rooms to list all rooms\n"\
    + "!online to show online users\n" \
    + "!join [room_name] to join/create/switch to a room\n" \
    + "!instructions.encode() to show instructions.encode()\n" \
    + "!leave to leave current room and/or to exit the server\n"

class Server:
    def __init__(self,listening_socket,client_connections):
        self.listening_socket = listening_socket
        self.client_connections = client_connections        #all clients sockets
        self.rooms = {}                                     # {room_name: Room}, links room_name to Room object
        self.client_rooms = {}                              # {client name: room name}
        print("Server started on {}:{}".format(args.host,args.p))
        print("To shut down server, use the command !shutdown\n")        

    #names of all clients
    @property
    def client_names(self):
        return [client.name for client in client_connections if client != self.listening_socket]

    """ broadcast accepts new clients,
    passes incoming messages to be handled,
    and removes clients who have left the server"""
    def broadcast(self):
        while True:
            #X and Y are not needed
            read_clients, X, Y = select.select(self.client_connections, [], [])     #uses client fileno
            
            """try and except are used as the server seems to limit
                requests for a certain given time"""
            try:
                for client in read_clients:
                    #accepting new connections
                    if client is self.listening_socket:
                        new_socket, add = client.accept()       #accept new connection
                        new_client = Client(new_socket)         #create new client
                        self.client_connections.append(new_client)      #add client to connections
                        # self.greet(new_client)
                        new_client.socket.sendall(b"Hello!\nWhat's your name?\n")     #get client name

                    else:
                        msg = client.socket.recv(4096)      #4096 == max amount of data to be received
                        if msg:
                        #pass message to be handled
                            msg = msg.decode().lower()
                            self.handle_msg(client, msg)
                        else:
                        #remove client 
                            client.socket.close()
                            self.client_connections.remove(client)
            except:
                pass

    """ handle_msg uses message prefixes to decide how to handle messages,
    executes commands, and passes message to appropriate Room object 
    to be broadcasted"""
    def handle_msg(self, client, msg):
        print(client.name + " says: " + msg)
        
        #command executions
        if "name:" in msg:
            name = msg.split()[1]
            client.name = name
            print("{} has joined!\n".format(client.name))
            client.socket.sendall(instructions.encode())         #show instructions

        elif "!join" in msg:
            self.join(client,msg)

        elif "!rooms" in msg:
            self.show_rooms(client) 
        
        elif "!online" in msg:
            self.show_active(client) 

        elif "!instructions" in msg:
            client.socket.sendall(instructions.encode())
        
        elif "!leave" in msg:
            # exit_msg = "{} has left :(\n".format(client.name)
            client.socket.sendall("!leave".encode())        #send to client file
            self.remove_client(client)

        #else send to room to broadcast client's message
        else:
            #verify that client is in a room
            if client.name in self.client_rooms:
                self.rooms[self.client_rooms[client.name]].broadcast(client, msg.encode())
            else:
            #notify client they must be in room to chat
                msg = "You are currently not in any room! \n" \
                    + "Use !rooms to see available rooms \n" \
                    + "Or !join [room_name] to create/join a room\n"
                client.socket.sendall(msg.encode())

    """ show_rooms is a function executed when the client enters the command !rooms.
    It shows the client all available rooms"""
    def show_rooms(self, client):
        #if there are no rooms
        if len(self.rooms) == 0:
            msg = "There are currently no rooms, create your own!\n" \
                + "You can also use !join [room_name] to create a room.\n"
            client.socket.sendall(msg.encode())
        #else display all rooms and how many clients in each
        else:
            msg = "All rooms:\n"
            msg += "".join([(room + ": " + str(len(self.rooms[room].clients)) + " user(s)\n") for room in self.rooms])
            client.socket.sendall(msg.encode())
    
    """ show_active is a function executed when the client enters the command !online.
    It shows the client all online users"""
    def show_active(self,client):
        msg = "({}) user(s) online\n".format(len(self.client_names))
        if len(self.client_names) > 0:
            msg += "".join(["{}\n".format(c) for c in self.client_names])
        client.socket.sendall(msg.encode())

    """ join is a function executed when the client enters the command !join [room_name].
    It allows the client to join/create/switch rooms"""
    def join(self,client,msg):
        if len(msg.split()) < 2:
            client.socket.sendall(b"No room chosen, try again!\n")
        else:
            switch = True   #flag to decide whether client can switch or not
            room_name = msg.split()[1]
            
            if client.name in self.client_rooms:
                #if client is already in the room
                if self.client_rooms[client.name] == room_name:
                    client.socket.sendall(b"You are already in room " + room_name.encode() + b"\n")
                    switch = False
                
                #if client is not already in the room
                #remove client from current room so they can switch to new room
                else:                   
                    room = self.client_rooms[client.name]
                    self.rooms[room].remove_client(client)
            
            if switch:
                #if room does not exist, create new room
                if room_name not in self.rooms:
                    new_room = Room(room_name)
                    self.rooms[room_name] = new_room
                
                #add client to room
                self.rooms[room_name].clients.append(client)
                self.rooms[room_name].greet(client)
                self.client_rooms[client.name] = room_name

    """ remove_client is a function executed when the client enters the command !leave.
    It deletes the client and removes them from the server connection list"""    
    def remove_client(self, client):
        if client.name in self.client_rooms:
            self.rooms[self.client_rooms[client.name]].remove_client(client) 
            del self.client_rooms[client.name]
            exit_msg = "\n{} has left the room\n".format(client.name)
            client.socket.sendall(exit_msg.encode())

    """ shutdown is a function run as a thread to allow the server to be shut down at
    any time. It uses input from the terminal"""
    def shutdown(self):
        while True:
            IN = input()
            if IN == "!shutdown":
                print("\nServer has been shut down\n")
                os._exit(1) #forces shutdown

#Room objects make sure message is only relayed to clients in the same Room
class Room:
    def __init__(self, name):
        self.clients = [] # a list of sockets
        self.name = name    #name of room

    """greet welcomes new clients and notifies all other clients"""
    def greet(self, from_client):
        msg = "Hi {}, welcome to {}!\n".format(from_client.name,self.name)
        [client.socket.sendall(msg.encode()) for client in self.clients]
    
    """ broadcast makes the client's message appear on all other clients' side"""
    def broadcast(self, from_client, msg):
        msg = from_client.name.encode() + b":" + msg
        [client.socket.sendall(msg) for client in self.clients]

    """ remove_client removes client from room and notifies other clients that client has left"""
    def remove_client(self, client):
        self.clients.remove(client)
        leave_msg = b"left the room\n"
        self.broadcast(client, leave_msg)       #sends message from client
        print("\n{} has left the room".format(client.name))


if __name__ == "__main__":
    #read input from command line
    parser = argparse.ArgumentParser(description='Chatroom Server')
    parser.add_argument('host', default="0.0.0.0",help='Interface the server listens at')
    parser.add_argument('p', metavar='PORT', type=int, default=8000,
                        help='TCP port (default 1060)')
    args = parser.parse_args()      #command line arguments

    """ CREATING THE LISTENING SOCKET
    socket.socket creates socket object, AF_INET specifies that it is part of the ipv4 address family,
        SOCK_STREAM specifies that it is a TCP socket
    socket.setsockopt sets the level at which the socket is working at,
        in this case it is SOL_SOCKET, the actual socket layer. It also sets the option SO_REUSEADDR
        which allows the socket.bind function to reuse local addresses, 1 is the buffer value
    socket.setblocking(0) sets socket to non-blocking mode, this allows it to not have to wait
    for the buffer to be full
    socket.bind binds socket to the given ip address and port
    socket.listen sets the max amount of connections the socket can have, this can be changed
    to allow more or less connections
    """
    listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listening_socket.setblocking(0)
    listening_socket.bind((args.host,args.p))
    listening_socket.listen(10)

    #create Server
    client_connections = [listening_socket]
    server = Server(listening_socket,client_connections)

    """   threads are used so server can run simultaneously with the shutdown function.
        This gives the host the possiblity of shutting down the server at any time """
    broadcast_thread = threading.Thread(target=Server.broadcast,args=[server]).start()
    shutdown_thread = threading.Thread(target=Server.shutdown,args=[server]).start()
