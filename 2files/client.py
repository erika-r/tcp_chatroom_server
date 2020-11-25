import select,socket,sys,argparse

QUIT = "!quit\n"

#every user is a socket
class Client:
    def __init__(self, socket, name = "new"):
        socket.setblocking(0)
        self.socket = socket
        self.name = name

    #used for select.select
    def fileno(self):
        return self.socket.fileno()


if __name__ == "__main__":
    #read command line arguments
    parser = argparse.ArgumentParser(description="Client Connection")
    parser.add_argument("host", default="0.0.0.0",help="Interface the server listens at")
    parser.add_argument("-p", metavar="PORT", type=int, default=8000,
                        help="TCP port (default 8000)")
    args = parser.parse_args()

    #create connection to server
    server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_connection.connect((args.host, args.p))   #ip address, port
    socket_list = [sys.stdin, server_connection]

    msg_start = ""
    while True:
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
        for sock in read_sockets:
            if sock is server_connection: # incoming message 
                msg = sock.recv(4096)       #if no message received
                if not msg:
                    #shut down for client
                    print("Server down!")
                    sys.exit(2)
                else:
                    if msg == QUIT.encode():
                        sys.stdout.write("See you again!\n")
                        quit()      #quit only for the player
                    else:
                        sys.stdout.write(msg.decode())
                        if "What's your name?" in msg.decode():
                            msg_start = "name: " # identifier for name
                        else:
                            msg_start = ""
                        print(">", end=" ", flush = True)   #move to next line

            else:
                msg = msg_start + sys.stdin.readline()
                server_connection.sendall(msg.encode())     #pass to server to pass to lobby
