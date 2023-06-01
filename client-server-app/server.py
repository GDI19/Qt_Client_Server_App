import json
from socket import *
import sys
import time

from common.utils import get_message, send_message

DEFAULT_PORT = 7777


def process_client_message(message):
    """
    Receive message from client, check it.
    :param message: dict
    :return: response (dict)
    """
    if 'action' in message and message['action'] == 'presence' and 'time' in message \
        and 'user' in message and message['user']['account_name'] == 'guest':
        return {'response': 200}    
    else:
        return {'response': 400, 'error': 'Bad Request'}
    


def main():
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT

        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
        
    except IndexError:
        print("После параметра -\'p\' необходимо указать номер порта.")
        sys.exit(1)
    except ValueError:
        print('Номер порта может быть указан только в диапазоне от 1024 до 65535.')
        sys.exit(1)

    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = 'localhost'
    except IndexError:
        print('После параметра \'- a\' необходимо указать адрес, который будет слушать сервер.')
        sys.exit(1)

    transport = socket(AF_INET, SOCK_STREAM)
    # transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    transport.bind((listen_address, listen_port))
    transport.listen(5)

    while True:
        client, addr = transport.accept()
        try:
            msg_form_client = get_message(client)
            print(msg_form_client)
            response = process_client_message(msg_form_client)
            send_message(client, response)
        except (ValueError, json.JSONDecodeError):
            print('Принято некорректное сообщение от клиента.')
            client.close()


if __name__ == '__main__':
    main()