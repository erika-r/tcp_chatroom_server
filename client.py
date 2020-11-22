import select, socket, sys
import handler     #string to quit
import argparse

READ_BUFFER = 4096


parser = argparse.ArgumentParser(description="Client Connection")
parser.add_argument("host", default="0.0.0.0",help="Interface the server listens at")
parser.add_argument("-p", metavar="PORT", type=int, default=8000,
                    help="TCP port (default 8000)")
args = parser.parse_args()

server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_connection.connect((args.host, args.p))   #ip address, port

print("Connected to server\n")

socket_list = [sys.stdin, server_connection]

msg_prefix = ""
while True:
    read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
    for s in read_sockets:
        if s is server_connection: # incoming message 
            msg = s.recv(READ_BUFFER)       #if no message
            if not msg:
                print("Server down!")
                sys.exit(2)
            else:
                if msg == handler.QUIT.encode():
                    sys.stdout.write("Bye!\n")
                    quit()
                    # sys.exit(2)
                else:
                    sys.stdout.write(msg.decode())
                    if "Please tell us your name" in msg.decode():
                        msg_prefix = "name: " # identifier for name
                    else:
                        msg_prefix = ""
                    print(">", end=" ", flush = True)   #move to next line

        else:
            msg = msg_prefix + sys.stdin.readline()
            server_connection.sendall(msg.encode())