from socket import *
import sys
import time
import json
import logging
import logs.client_log_config

client_log = logging.getLogger('client_log')

from common.utils import get_message, send_message



def create_presence( account_name = 'guest'):
    presence_msg = {
        "action": "presence",
        "time": time.time(),
        "user": {
            "account_name": account_name,
        }
    }
    client_log.info(f'created presence with user: `{account_name}`')
    return presence_msg


def process_answer(message):
    if 'response' in message:
        if message['response'] == 200:  
            return '200: ok'
        else:
            return f"400: {message['error']}"
    client_log.error('invalid message')
    
    raise ValueError


def main():
    '''Загружаем параметы коммандной строки'''
    # client.py 192.168.57.33 8079
    client_log.info('launch client')

    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        client_log.info('no socket parameters. Using defaults')

        server_address = '127.0.0.1'
        server_port = 7777
    except ValueError:
        client_log.error('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    transport = socket(AF_INET, SOCK_STREAM)
    transport.connect((server_address, server_port))
    client_log.info(f'connecting to the server: {server_address} - {server_port}')
    

    msg_to_server = create_presence()
    send_message(transport, msg_to_server)

    try:
        answer = process_answer(get_message(transport))
        client_log.info(f'message received: {answer}')

    except (ValueError, json.JSONDecodeError):
        client_log.warning('Не удалось декодировать сообщение сервера.')


if __name__ == '__main__':
    main()
        