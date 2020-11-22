
import select, socket, sys
from handler import Lobby, Room, Player
import handler
import argparse
import threading

READ_BUFFER = 4096

def broadcast(listen_sock,lobby,connection_list):
    while True:
        # uses Player.fileno()
        read_players, write_players, error_sockets = select.select(connection_list, [], [])
        
        for player in read_players:
            if player is listen_sock: # new connection, player is a socket
                new_socket, add = player.accept()
                new_player = Player(new_socket)
                connection_list.append(new_player)
                lobby.welcome(new_player)

            else: # new message
                msg = player.socket.recv(READ_BUFFER)
                if msg:
                    msg = msg.decode().lower()
                    lobby.handle_msg(player, msg)
                else:
                    player.socket.close()
                    connection_list.remove(player)
        
        for sock in error_sockets: # close error sockets
            sock.close()
            connection_list.remove(sock)
        

#read input from command line
parser = argparse.ArgumentParser(description='Chatroom Server')
parser.add_argument('host', default="0.0.0.0",help='Interface the server listens at')
parser.add_argument('-p', metavar='PORT', type=int, default=8000,
                    help='TCP port (default 1060)')
args = parser.parse_args()

listen_sock = handler.create_socket((args.host,args.p))

lobby = Lobby()
connection_list = []
connection_list.append(listen_sock)

broadcast(listen_sock,lobby,connection_list)
# threading.Thread(target=broadcast,args=[listen_sock,lobby,connection_list]).start()

