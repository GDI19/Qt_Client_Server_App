from socket import *


s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

while True:
    for i in range(1000):
        msg = f'Запрос на соединение №{i}!'.encode('utf-8')
        s.sendto(msg, ('localhost', 8888))
    s.close()