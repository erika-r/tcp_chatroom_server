#!/usr/bin/env python3

import threading
import socket
import argparse
import os
import sys
import tkinter as tk

#listens for user input
class Send(threading.Thread):
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock    #connected socket object
        self.name = name    #client username

    #listens for client input from command line and sends to server 
    def run(self):
        while True:
            print('{}: '.format(self.name), end='')
            sys.stdout.flush()      #force flush the buffer
            message = sys.stdin.readline()[:-1]

            # Type 'QUIT' to leave the chatroom
            if message == 'QUIT':
                self.sock.sendall('Server: {} has left the chat.'.format(self.name).encode('ascii'))
                break
            
            # Send message to server for broadcasting
            else:
                self.sock.sendall('{}: {}'.format(self.name, message).encode('ascii'))
        
        #close socket and quit
        print('\nQuitting...')
        self.sock.close()
        os._exit(0)

#listens for messages from server
class Receive(threading.Thread):
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock    #connected socket object
        self.name = name    #client username
        self.messages = None    #tk.Listbox object, contains all messages displayed on gui

    #either receives data from server and displays it on the gui
    #or closes when server/client socket has closed
    def run(self):
        while True:
            message = self.sock.recv(1024).decode('ascii')

            if message:

                if self.messages:
                    self.messages.insert(tk.END, message)
                    print('hi')
                    print('\r{}\n{}: '.format(message, self.name), end = '')
                
                else:
                    # Thread has started, but client GUI is not yet ready
                    print('\r{}\n{}: '.format(message, self.name), end = '')
            
            else:
                # Server has closed the socket, exit the program
                print('\nOh no, we have lost connection to the server!')
                print('\nQuitting...')
                self.sock.close()
                os._exit(0)

#manages client-server connections and gui
class Client:
    def __init__(self, host, port):
        self.host = host        #IP address of server's listening socket
        self.port = port        #port number of server's listening socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #conencted socket object 
        self.name = None        #client username
        self.messages = None    #tk.Listbox containing all messages displayed on gui
    
    #establishes client-server connection
    def start(self):
        print('Trying to connect to {}:{}...'.format(self.host, self.port))
        self.sock.connect((self.host, self.port))
        print('Successfully connected to {}:{}'.format(self.host, self.port))
        
        print()
        #takes in client username
        self.name = input('Your name: ')

        print()
        print('Welcome, {}! Getting ready to send and receive messages...'.format(self.name))

        # Create send and receive threads
        send = Send(self.sock, self.name)
        receive = Receive(self.sock, self.name)

        # Start send and receive threads
        send.start()
        receive.start()

        #notify all other clients
        self.sock.sendall('Server: {} has joined the chat. Say hi!'.format(self.name).encode('ascii'))
        print("\rAll set! Leave the chatroom anytime by typing 'QUIT'\n")
        print('{}: '.format(self.name), end = '')

        return receive  #receiving thread object

    #sends text input from the gui
    #text_input = tk.Entry object for user text input
    def send(self, text_input):
        message = text_input.get()
        text_input.delete(0, tk.END)
        self.messages.insert(tk.END, '{}: {}'.format(self.name, message))

        # Type 'QUIT' to leave the chatroom
        if message == 'QUIT':
            self.sock.sendall('Server: {} has left the chat.'.format(self.name).encode('ascii'))
            
            print('\nQuitting...')
            self.sock.close()
            os._exit(0)
        
        # Send message to server for broadcasting
        else:
            self.sock.sendall('{}: {}'.format(self.name, message).encode('ascii'))

#Initializes and runs the GUI application.
def main(host, port):
    client = Client(host, port)
    receive = client.start()

    window = tk.Tk()
    window.title('Chatroom')

    frm_messages = tk.Frame(master=window)
    scrollbar = tk.Scrollbar(master=frm_messages)
    messages = tk.Listbox(
        master=frm_messages, 
        yscrollcommand=scrollbar.set
    )
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
    messages.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    client.messages = messages
    receive.messages = messages

    frm_messages.grid(row=0, column=0, columnspan=2, sticky="nsew")

    frm_entry = tk.Frame(master=window)
    text_input = tk.Entry(master=frm_entry)
    text_input.pack(fill=tk.BOTH, expand=True)
    text_input.bind("<Return>", lambda x: client.send(text_input))
    text_input.insert(0, "Your message here.")

    btn_send = tk.Button(
        master=window,
        text='Send',
        command=lambda: client.send(text_input)
    )

    frm_entry.grid(row=1, column=0, padx=10, sticky="ew")
    btn_send.grid(row=1, column=1, pady=10, sticky="ew")

    window.rowconfigure(0, minsize=500, weight=1)
    window.rowconfigure(1, minsize=50, weight=0)
    window.columnconfigure(0, minsize=500, weight=1)
    window.columnconfigure(1, minsize=200, weight=0)

    window.mainloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chatroom Server')
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
    args = parser.parse_args()

    main(args.host, args.p)