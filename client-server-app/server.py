import json
from socket import *
import sys
import time
import logging
import logs.server_log_config
from logs.server_log_config import log


server_log = logging.getLogger('server_log')


from common.utils import get_message, send_message

DEFAULT_PORT = 7777

@log
def process_client_message(message):
    """
    Receive message from client, check it.
    :param message: dict
    :return: response (dict)
    """
    if 'action' in message and message['action'] == 'presence' and 'time' in message \
        and 'user' in message and message['user']['account_name'] == 'guest':
        server_log.debug('Processed msg with correct info')
        return {'response': 200}    
    else:
        server_log.critical('Processed msg with noncorrect info')
        return {'response': 400, 'error': 'Bad Request'}
    


def main():
    server_log.debug('Server has been launched...')

    try:
        server_log.debug('Trying to parse parameters -p')

        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT

        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
        
    except IndexError:
        server_log.info("После параметра -\'p\' необходимо указать номер порта.")
        
        server_log.warning('There is no parameter -p')
        
        sys.exit(1)
    except ValueError:
        server_log.info('Номер порта может быть указан только в диапазоне от 1024 до 65535.')
        server_log.error('Not correct -p')
        sys.exit(1)

    try:
        server_log.debug('Trying to parse parameter -a')

        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = 'localhost'
    except IndexError:
        server_log.info('После параметра \'- a\' необходимо указать адрес, который будет слушать сервер.')
        server_log.debug('There is no parameter -a')
        sys.exit(1)

    transport = socket(AF_INET, SOCK_STREAM)
    # transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    transport.bind((listen_address, listen_port))
    server_log.debug(f'using socket {listen_address} - {listen_port}')

    transport.listen(5)

    while True:
        client, addr = transport.accept()
        try:
            msg_form_client = get_message(client)
            server_log.info(f'received message from client: {msg_form_client}')
            response = process_client_message(msg_form_client)
            send_message(client, response)
        except (ValueError, json.JSONDecodeError):
            server_log.error('Not correct message from client')
            
            client.close()


if __name__ == '__main__':
    main()