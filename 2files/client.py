import select,socket,sys,argparse

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

    """ take in ip address and port number here as the
    server will handle client and chatroom name"""
    ip_address = input("IP address: ")
    port = int(input("Port no.: "))

    #create connection to server
    """ socket creation is explained in server.py, however in this case we
    do not need to use all thse same functions as it is not the listening socket.
    Instead we use socket.connect to the socket at the given address"""
    server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_connection.connect((ip_address,port))   #ip address, port
    socket_list = [sys.stdin, server_connection]

    """ sends messages to client's interface and passes client's message
    to server to be handled"""
    prefix = ""
    while True:
        #X and Y are not needed
        read_sockets, X, Y = select.select(socket_list, [], [])
        for sock in read_sockets:
            if sock is server_connection: # incoming message 
                msg = sock.recv(4096)       #if no message received
                if not msg:
                    #shut down for client
                    print("Server down!")
                    sys.exit(2)
                else:
                    if msg == "!leave".encode():
                        sys.stdout.write("See you again!\n")
                        quit()      #quit only for the client
                    else:
                        sys.stdout.write(msg.decode())
                        if "What's your name?" in msg.decode():
                            prefix = "name: " # identifier for name
                        else:
                            prefix = ""
                        print(">", end=" ", flush = True)   #move to next line

            else:
                #pass msg to server to handle
                msg = prefix + sys.stdin.readline()
                server_connection.sendall(msg.encode())
