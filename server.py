#references
#https://stackoverflow.com/questions/34984443/using-select-method-for-client-server-chat-in-python

import select,socket,argparse,threading,os
from handler import Lobby,User   #, Room, User

#shuts down server
#uses input from terminal
def shutdown(listening_sock):
    while True:
        IN = input()
        if IN == "!shutdown":
            print("\nServer has been shut down\n")
            os._exit(1) #forces shutdown

def broadcast(listening_sock,lobby,connection_list):
    while True:
        read_users, _, error_sockets = select.select(connection_list, [], [])     #uses user fileno
        
        for user in read_users:

            #accepting connections
            if user is listening_sock: # new connection, user is a socket
                new_socket, add = user.accept()
                new_user = User(new_socket)
                connection_list.append(new_user)
                lobby.welcome(new_user)

            #pass message to the handler
            else:
                msg = user.socket.recv(4096)      #4096 == max amount of data to be received
                if msg:
                    msg = msg.decode().lower()
                    lobby.handle_msg(user, msg)
                else:
                    user.socket.close()
                    connection_list.remove(user)


#read input from command line
parser = argparse.ArgumentParser(description='Chatroom Server')
parser.add_argument('host', default="0.0.0.0",help='Interface the server listens at')
parser.add_argument('-p', metavar='PORT', type=int, default=8000,
                    help='TCP port (default 1060)')
args = parser.parse_args()      #command line arguments

#create listening socket
listening_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listening_sock.setblocking(0)
listening_sock.bind((args.host,args.p))
listening_sock.listen(10)
print("Server started on {}:{}".format(args.host,args.p))
print("To shut down server, use the command '!shutdown'\n")

#create lobby for new connections
lobby = Lobby()
connection_list = [listening_sock]

#start threads
broadcast_thread = threading.Thread(target=broadcast,args=[listening_sock,lobby,connection_list]).start()
shutdown_thread = threading.Thread(target=shutdown,args=[listening_sock]).start()
