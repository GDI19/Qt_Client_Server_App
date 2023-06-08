import argparse
from socket import *
import sys
import time
import json
import logging
import logs.client_log_config
from logs.client_log_config import log
from datetime import datetime

client_log = logging.getLogger('client_log')

from common.utils import get_message, send_message

DEFAULT_PORT =7777


@log
def create_presence( account_name = 'guest'):
    presence_msg = {
        "action": "presence",
        "time": time.time(),
        "account_name": account_name,
    }
    client_log.info(f'created presence with user: `{account_name}`')
    return presence_msg

@log
def process_answer(message):
    if 'response' in message:
        if message['response'] == 200:  
            return '200: ok'
        else:
            return f"400: {message['error']}"
        
    elif 'action' in message and message['action'] == 'message' and 'sender' in message and 'message_text' in message and 'time' in message:
        msg_time = datetime.fromtimestamp(message['time']).replace(second=0, microsecond=0)
        sender = message['sender']
        msg = message['message_text']
        return f'{msg_time} - {sender}: {msg}'
    
    client_log.error('Invalid message')
    raise ValueError


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default='localhost', nargs='?')
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-m', '--mode', default='listen', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.a
    server_port = namespace.p
    client_mode = namespace.mode

    if not 1023 < server_port < 65536:
        client_log.critical(f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    if client_mode not in ('listen', 'send'):
        client_log.critical(f'Указан недопустимый режим работы {client_mode}, '
                        f'допустимые режимы: listen , send')
        sys.exit(1)

    return server_address, server_port, client_mode


def create_message(text_for_msg, account_name='guest'):
    return {
        'action': 'message',
        'account_name': account_name,
        'time': time.time(),
        'message_text': text_for_msg
    }


def main():
    client_log.info('Launch client...')

    server_address, server_port, client_mode = arg_parser()

    transport = socket(AF_INET, SOCK_STREAM)
    transport.connect((server_address, server_port))
    
    client_log.info(f'Connecting to the server: {server_address} - {server_port} in mode: {client_mode}')

    try:
        msg_to_server = create_presence()
        send_message(transport, msg_to_server)

        answer = process_answer(get_message(transport))
        client_log.info(f'message from server received: {answer}')
        print('Connection to the server:', answer)
    except (ValueError, json.JSONDecodeError):
        client_log.warning('Не удалось декодировать сообщение сервера.')


    while True:
        if client_mode == 'send':
            text_for_msg = input('Enter your message. To exit type `exit`.\n')
            if text_for_msg == 'exit':
                transport.close()
                client_log.info('Завершение работы по команде пользователя.')
                print('Спасибо за использование нашего сервиса!')
                break
            else:
                try:
                    msg_to_send = create_message(text_for_msg)
                    send_message(transport, msg_to_send)
                except error as er:
                    #client_log.error(f'Smthg went wrong while sending message. Error: {er}')
                    client_log.error(f'Соединение с сервером {server_address} было потеряно.')
                    sys.exit(1)

        elif client_mode == 'listen':
            try:
                answer = process_answer(get_message(transport))
                print(answer)
            except error as er:
                client_log.error(f'Соединение с сервером {server_address} было потеряно.')
                sys.exit(1)
    


if __name__ == '__main__':
    main()
        