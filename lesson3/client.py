from socket import *
import sys
import time
import json

from utils import get_message, send_message


# s = socket(AF_INET, SOCK_STREAM)
# s.connect(('localhost', 8007))


# msg = {
#     "action": "presence",
#     "time": str(time.time()),
#     "user": {
#         "account_name": "C0deMaver1ck",
#         "password": "CorrectHorseBatterStaple"
#     }
# }
# json_msg = json.dumps(msg)

# s.send(json_msg.encode('utf-8'))
# data = s.recv(1024)
# data_decoded = json.loads(data.decode('utf-8'))
# print(data_decoded, 'size:' ,len(data))
# s.close()


def create_presence( account_name = 'guest'):
    presence_msg = {
        "action": "presence",
        "time": time.time(),
        "user": {
            "account_name": account_name,
        }
    }
    return presence_msg


def process_answer(message):
    if 'response' in message:
        if message['response'] == 200:
            return '200: ok'
        else:
            return f"400: {message['error']}"
    raise ValueError


def main():
    '''Загружаем параметы коммандной строки'''
    # client.py 192.168.57.33 8079

    try:
        server_address = sys.argv[1]
        server_port = sys.argv[2]
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = '127.0.0.1'
        server_port = 7777
    except ValueError:
        print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    transport = socket(AF_INET, SOCK_STREAM)
    transport.connect((server_address, server_port))

    msg_to_server = create_presence('user')
    send_message(transport, msg_to_server)

    try:
        answer = process_answer(get_message(transport))
        print(answer)
    except (ValueError, json.JSONDecodeError):
        print('Не удалось декодировать сообщение сервера.')


if __name__ == '__main__':
    main()
        