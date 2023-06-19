import argparse
from collections.abc import Callable, Iterable, Mapping
from socket import *
import sys
import time
import json
import logging
from typing import Any

from metaclasses import ClientVerifier
import logs.client_log_config
from logs.client_log_config import log
from datetime import datetime
import threading
from common.utils import get_message, send_message

client_log = logging.getLogger('client_log')

DEFAULT_PORT =7777


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.user_name = account_name
        self.sock = sock
        super().__init__()


    def create_exit_message(self):
        exit_message = {
            "action": "exit",
            "time": time.time(),
            "user":{
                "account_name": self.user_name}
        }
        return exit_message
    

    def create_message(self):
        send_to = input('Введите имя пользователя для кого сообщение! -`all` для всех\n')
        text_for_msg = input('Введите сообщение:\n')
    
        msg_to_send ={
            'action': 'message',
            'user':{
                'account_name': self.user_name},
            'send_to': send_to,
            'time': time.time(),
            'message_text': text_for_msg
        }

        try:
            send_message(self.sock, msg_to_send)
            client_log.info(f'Отправлено сообщение для пользователя {send_to}')
        except:
            client_log.critical('Потеряно соединение с сервером.')
            exit(1)


    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: \n')
            if command == 'message': # in ['message', 'Message', 'MESSAGE']:
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':# ['exit', 'EXIT', 'Exit']:
                try:
                    exit_message = self.create_exit_message()
                    send_message(self.sock, exit_message)
                except:
                    pass
                print('Спасибо, за работу! До скорой встречи')
                client_log.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')


    def print_help(self):
        print('-'*15, 'Поддерживаемые команды:', '-'*15)
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')
        print('-'*30)


class ClientListener(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.user_name = account_name
        self.sock = sock
        super().__init__()

    def run(self) -> None:
        while True:
            try:
                message = get_message(self.sock)
                client_log.info(f'message from server received: {message}')       
                
                if 'action' in message and message['action'] == 'message' and 'sender' in message and 'message_text' in message and 'time' in message:
                    msg_time = datetime.fromtimestamp(message['time']).replace(second=0, microsecond=0)
                    sender = message['sender']
                    msg = message['message_text']
                    print('-'*15, 'Reseived Message' ,'-'*15)
                    print(f'{msg_time} - {sender}: {msg}')
                    print('-'*30)
                
                else:
                    client_log.error(f'Получено некорректное сообщение с сервера: {message}')
                   # raise ValueError
            except:
                client_log.critical(f'Потеряно соединение с сервером.')
                break
    

@log
def create_presence( account_name):
    presence_msg = {
        "action": "presence",
        "time": time.time(),
        'user':{
            "account_name": account_name}
    }
    client_log.info(f'created presence with user: `{account_name}`')
    return presence_msg


#@log
def process_response_answer(transport):
    message = get_message(transport)
    if 'response' in message:
        if message['response'] == 200:  
            return '200: ok'
        else:
            return f"400: {message['error']}"


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default='localhost', nargs='?')
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.a
    server_port = namespace.p
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        client_log.critical(f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    return server_address, server_port, client_name


def main():
    client_log.info('Launch client...')

    server_address, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')
    
    client_log.info(f'Connecting to the server: {server_address} - {server_port} user: {client_name}')

    try:
        transport = socket(AF_INET, SOCK_STREAM)
        transport.connect((server_address, server_port))

        presence_to_server = create_presence(account_name=client_name)
        send_message(transport, presence_to_server)

        answer = process_response_answer(transport)
        client_log.info(f'message from server received: {answer}')
        print(f'Username: {client_name}. Connection to the server:', answer)
    except (ValueError, json.JSONDecodeError):
        client_log.warning('Не удалось декодировать сообщение сервера.')
    
    else:
        mod_receiver = ClientListener(client_name, transport)
        mod_receiver.daemon = True
        mod_receiver.start()

        mod_sendeer = ClientSender(client_name, transport)
        mod_sendeer.daemon = True
        mod_sendeer.start()
    
        while True:
            if mod_receiver.is_alive() and mod_sendeer.is_alive():
                time.sleep(2)
                continue
            else:
                break


if __name__ == '__main__':
    main()
        