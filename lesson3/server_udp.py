from socket import *

s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

s.bind(('localhost', 8888))

while True:
    msg = s.recv(128).decode('utf-8')
    print(msg)
    