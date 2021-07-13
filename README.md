# TCP Chatroom Server

This project was made to demonstrate networking concepts and socket programming.
[Here](https://drive.google.com/file/d/1Kw9ouPg0Mrp3ifSGvVmJlctfk-Ga1asC/view?usp=sharing) is a demo.

To run the server, use the command
```
python server.py <ip address> <port> 
```
for example
```
python server.py 127.0.0.1 8000
```

To join the server, use the command
```
python client.py
```

This project was created in 4 parts
- constructing a working server which can receive text messages
- creating a client object which can connect to the server
- creating a two way chat, when 2 different clients connect to the server they will be able to see each other's messages
- extending the server capabilities to different chat rooms, users are able to make, join, and switch between chat rooms
