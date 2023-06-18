import argparse
import json
import select
from socket import *
import sys
import time
import logging
import logs.server_log_config
from logs.server_log_config import log
from common.utils import get_message, send_message
from descriptors import Port

server_log = logging.getLogger('server_log')

DEFAULT_PORT = 7777

@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default='', nargs='?')
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server():
    port = Port()
    def __init__(self, listen_address, listen_port):
        self.address = listen_address
        self.port = listen_port

        #  {username: socket, ...} Словарь имен и соответствующие им сокеты
        self.users = {}

        # [socket, ...] Список подключённых клиентов
        self.clients = []

        # [(username_from, message, username_to), ...] Список сообщений на отправку
        self.messages = []  


    def init_socket(self):
        server_log.debug('Server has been launched...')
        server_log.info(
            f'Запущен сервер: {self.address} порт: {self.port}, '
            f'Если адрес не указан, принимаются соединения с любых адресов.')

        transport = socket(AF_INET, SOCK_STREAM)
        # transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        transport.bind((self.address, self.port))
        # transport.listen(5)
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen()


    def main_loop(self):
        self.init_socket()

        while True:
            try:
                client, addr = self.sock.accept()
            except OSError as err:
                pass
            else:
                print("Получен запрос на соединение с %s" % str(addr))
                server_log.info(f'Установлено соедение с ПК {self.address}')
                self.clients.append(client)

            read_lst = [] 
            write_lst = []
            error_lst = []

            try:
                if self.clients:
                    read_lst, write_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if read_lst:
                for client_with_message in read_lst:
                    try:
                        msg_from_client = get_message(client_with_message)
                        server_log.info(f'received message from client: {msg_from_client}')
                        self.process_client_message(msg_from_client, client_with_message)
                    except:
                        server_log.error(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        self.clients.remove(client_with_message)
                
            """
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except:
                    logger.info(f'Связь с клиентом с именем {message[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()
            """
            while self.messages and write_lst:
                user_to_send = self.messages[0][2]
                message = {
                        'action': 'message',
                        'send_to': user_to_send,
                        'sender': self.messages[0][0],
                        'time': time.time(),
                        'message_text': self.messages[0][1]
                    }
                del self.messages[0]
                if user_to_send in ['all', 'All', 'ALL']:
                    for waiting_client in write_lst:
                        try:
                            send_message(waiting_client, message)
                        except:
                            server_log.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                            self.clients.remove(waiting_client)

                elif user_to_send in self.users:
                    socket_to_send = self.users[user_to_send]
                    if socket_to_send in write_lst:    
                        try:
                            send_message(socket_to_send, message)
                        except:
                            self.send_msg_failed_notification(message, user_to_send)
                            server_log.info(f'Клиент {socket_to_send.getpeername()} отключился от сервера.')
                            self.users.pop(user_to_send)
                    else:
                        self.send_msg_failed_notification(message, user_to_send)
                        server_log.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                        self.users.pop(user_to_send)

                else:           
                    self.send_msg_failed_notification(message, user_to_send)
    
    """
    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            logger.info(f'Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна.')
    """


    def process_client_message(self, message, client):
        """
        Receive message from client, check it.
        :param message: dict
        :return: response (dict)
        """
        if 'time' in message and 'action' in message and  'user' in message and 'account_name' in message['user']:
            server_log.debug('Processed msg with correct info')

            if message['action'] == 'exit':
                self.clients.remove(client)
                client.close()
                del self.users[message['user']['account_name']]
                return
            
            elif message['action'] == 'presence':
                new_user_in = message['user']['account_name']
                if new_user_in not in self.users:
                    send_message(client, {'response': 200})
                    self.users[new_user_in] = client
                else:
                    send_message(client, {'response': 400, 'error': f'Пользователь с таким именем: {new_user_in} уже подключен.'})
                    self.clients.remove(client)
                    client.close()
                return
            
            elif message['action'] == 'message' and 'message_text' in message and 'send_to' in message:
                self.messages.append((message['user']['account_name'], message['message_text'], message['send_to']))
                return
        
        server_log.critical('Processed msg with noncorrect info')
        send_message(client, {'response': 400, 'error': 'Bad Request'})
        return


    def send_msg_failed_notification(self, message, user_to_send):
        failed_message = {
            'action': 'message',
            'send_to': message['sender'],
            'sender': 'server',
            'time': time.time(),
            'message_text': f'Сообщение для клиента {user_to_send} не отправлено'
        }
        try:
            back_socket = self.users[message['sender']]
            send_message(back_socket, failed_message)
        except:
            self.clients.remove(back_socket)
            del self.users[message['sender']]
            
        server_log.info(f'Сообщение: {message} \n для клиента не отправлено.'
                            f'Такого пользователя {user_to_send} нет.')
      

def main():
    listen_address, listen_port = arg_parser()
    
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()