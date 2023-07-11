import threading
import logging
import select
from socket import socket, AF_INET, SOCK_STREAM
import json
import hmac
import binascii
import os
from common.descriptors import Port
from common.utils import send_message, get_message
from common.my_decorators import login_required

server_log = logging.getLogger('server_log')

DEFAULT_PORT = 7777

# Флаг что был подключён новый пользователь, нужен чтобы не мучать BD
# постоянными запросами на обновление
new_connection = False
conflag_lock = threading.Lock()


class MessageProcessor(threading.Thread):  # , metaclass=ServerVerifier):
    '''
    Основной класс сервера. Принимает содинения, словари - пакеты
    от клиентов, обрабатывает поступающие сообщения.
    Работает в качестве отдельного потока.
    '''

    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.address = listen_address
        self.port = listen_port

        #  {username: socket, ...} Словарь имен и соответствующие им сокеты
        self.users = {}

        # Сокет, через который будет осуществляться работа
        self.sock = None

        # [socket, ...] Список подключённых клиентов
        self.clients = []

        # Сокеты
        self.listen_sockets = None
        self.error_sockets = None

        # Флаг продолжения работы
        self.running = True

        # [(username_from, message, username_to), ...] Список сообщений на отправку
        self.messages = []

        self.database = database

        super().__init__()

    def init_socket(self):
        server_log.debug('Server has been launched...')
        server_log.info('Запущен сервер: %s порт: %s, \
                        Если адрес не указан, принимаются соединения \
                        с любых адресов.', self.address, self.port)

        transport = socket(AF_INET, SOCK_STREAM)
        # transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        transport.bind((self.address, self.port))
        # transport.listen(5)
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen()

    def run(self):
        """Method run in Server"""
        self.init_socket()

        while True:
            try:
                client, addr = self.sock.accept()
            except OSError:
                pass
            else:
                print("Получен запрос на соединение с %s" % str(addr))
                server_log.info('Установлено соедение с ПК %s', self.address)
                self.clients.append(client)

            read_lst = []
            write_lst = []
            error_lst = []

            try:
                if self.clients:
                    read_lst, write_lst, err_lst = select.select(
                        self.clients, self.clients, [], 0)
            except OSError:
                pass

            if read_lst:
                for client_with_message in read_lst:
                    try:
                        msg_from_client = get_message(client_with_message)
                        server_log.info(
                            'received message from client: %s', msg_from_client)
                        self.process_client_message(
                            msg_from_client, client_with_message)
                    except:
                        server_log.error(
                            'Клиент %s отключился от сервера.', client_with_message)
                        self.clients.remove(client_with_message)

                        for name in self.users.items():
                            if self.users[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.users[name]
                                break
                        with conflag_lock:
                            new_connection = True

            if self.messages:
                for message in self.messages:
                    recipient = message['send_to']
                    try:
                        self.process_message_to_send(
                            message, recipient, write_lst)
                    except:
                        server_log.info(
                            'Связь с клиентом с именем %s была потеряна', recipient)
                        # self.send_msg_failed_notification(message, recipient)
                        self.clients.remove(self.users[recipient])
                        del self.users[recipient]
                        with conflag_lock:
                            new_connection = True
                self.messages.clear()

    def remove_client(self, client):
        '''
        Метод обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы:
        '''
        server_log.info('Клиент %s отключился от сервера.',
                        client.getpeername())
        for name in self.users.items():
            if self.users[name] == client:
                self.database.user_logout(name)
                del self.users[name]
                break
        self.clients.remove(client)
        client.close()

    def process_message_to_send(self, message, recipient, listen_socks):
        if recipient in self.users and self.users[recipient] in listen_socks:
            send_message(self.users[recipient], message)
            server_log.info(
                "Отправлено сообщение пользователю %s от пользователя %s.", recipient, message['sender'])
            return
        elif recipient in self.users and self.users[recipient] not in listen_socks:
            server_log.info(
                'Связь с клиентом с именем %s была потеряна', recipient)
        else:
            server_log.error(
                'Пользователь %s не зарегистрирован на сервере, отправка сообщения невозможна.', recipient)

        # self.send_msg_failed_notification(message, recipient)

    @login_required
    def process_client_message(self, message, client):
        """
        Receive message from client, check it.
        :param message: dict
        :return: response (dict)
        """
        if 'time' in message and 'action' in message:
            if message['action'] == 'exit' and 'user' in message and 'account_name' in message['user']:
                self.remove_client(client)
                return

            elif message['action'] == 'presence' and 'user' in message and 'account_name' in message['user']:
                self.authorize_user(message, client)
                return

            elif message['action'] == 'message' and 'message_text' in message and 'send_to' in message \
                    and 'sender' in message and self.users[message['sender']] == client:
                if message['send_to'] in self.users:
                    self.messages.append(message)
                    self.database.process_message(
                        message['sender'], message['send_to'])
                    send_message(client, {'response': 200})
                else:
                    response = {'response': 400,
                                'error': 'Пользователь не в сети.'}
                    send_message(client, response)
                return

            elif message['action'] == 'get_contacts' and 'user' in message and \
                    self.users[message['user']] == client:
                response = {'response': 202, 'data_list': None}
                response['data_list'] = self.database.get_contacts(
                    message['user'])
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
                return

            elif message['action'] == 'add' and 'account_name' in message and 'user' in message \
                    and self.users[message['user']] == client:
                self.database.add_contact(
                    message['user'], message['account_name'])
                try:
                    send_message(client, {'response': 200})
                except OSError:
                    self.remove_client(client)
                return

            elif message['action'] == 'remove' and 'account_name' in message and 'user' in message \
                    and self.users[message['user']] == client:
                self.database.remove_contact(
                    message['user'], message['account_name'])
                try:
                    send_message(client, {'response': 200})
                except OSError:
                    self.remove_client(client)
                return

            elif message['action'] == 'get_users' and 'account_name' in message \
                    and self.users[message['account_name']] == client:
                response = {'response': 202, 'data_list': None}
                response['data_list'] = [user[0]
                                         for user in self.database.users_list()]
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
                return

                # Если это запрос публичного ключа пользователя
            elif 'action' in message and message['action'] == 'pubkey_need' and 'account_name' in message:
                response = {'response': 511, 'bin': None}
                response['bin'] = self.database.get_pubkey(
                    message['account_name'])
                # может быть, что ключа ещё нет (пользователь никогда не логинился,
                # тогда шлём 400)
                if response['bin']:
                    try:
                        send_message(client, response)
                    except OSError:
                        self.remove_client(client)
                else:
                    response = {'response': 400, 'error': ""}
                    response['error'] = 'Нет публичного ключа для данного пользователя'
                    try:
                        send_message(client, response)
                    except OSError:
                        self.remove_client(client)
                return

        server_log.critical('Processed msg with noncorrect info')
        send_message(client, {'response': 400, 'error': 'Bad Request'})
        return

    def authorize_user(self, message, sock):
        '''Метод реализующий авторизцию пользователей.'''
        # Если имя пользователя уже занято то возвращаем 400
        server_log.debug('Start auth process for %s', message["user"])

        new_user_in = message['user']['account_name']
        if new_user_in in self.users.items():
            try:
                server_log.debug('Username busy, sending response')
                send_message(sock, {
                             'response': 400, 'error': f'Пользователь с таким именем: {new_user_in} уже подключен.'})
            except OSError:
                server_log.debug('OS Error')

            self.clients.remove(sock)
            sock.close()
        elif not self.database.check_user(new_user_in):
            try:
                server_log.debug(
                    'Username is not registered, sending response')
                send_message(sock, {
                             'response': 400, 'error': f'Пользователь с таким именем: {new_user_in} не зарегистрирован'})
            except OSError:
                server_log.debug('OS Error')

            self.clients.remove(sock)
            sock.close()
        else:
            server_log.debug('Correct username, starting passwd check.')
            # Иначе отвечаем 511 и проводим процедуру авторизации
            # Словарь - заготовка
            message_auth = {'response': 511, 'bin': None}

            # Набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))

            # В словарь байты нельзя, декодируем (json.dumps -> TypeError)
            message_auth['bin'] = random_str.decode('ascii')

            # Создаём хэш пароля и связки с рандомной строкой, сохраняем
            # серверную версию ключа
            hash_ = hmac.new(self.database.get_hash(
                new_user_in),  random_str, 'MD5')
            digest = hash_.digest()
            try:
                send_message(sock, message_auth)
                answer = get_message(sock)
            except OSError as err:
                server_log.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return

            client_digest = binascii.a2b_base64(answer['bin'])
            if 'response' in answer and answer['response'] == 511 and hmac.compare_digest(
                    digest, client_digest):
                try:
                    send_message(sock, {'response': 200})
                except OSError:
                    self.remove_client(new_user_in)

                self.users[new_user_in] = sock
                client_ip, client_port = sock.getpeername()
                self.database.user_login(
                    new_user_in,
                    client_ip,
                    client_port,
                    message['user']['pubkey'])
            else:
                response = {'response': 400, 'error': ""}
                response['error'] = 'Неверный пароль.'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        '''Метод реализующий отправки сервисного сообщения 205 клиентам.'''
        for client in self.users.items():
            response_205 = {'response': 205}
            try:
                send_message(self.users[client], response_205)
            except OSError:
                self.remove_client(self.users[client])

    # def send_msg_failed_notification(self, message, user_to_send):
    #     failed_message = {
    #         'action': 'message',
    #         'send_to': message['sender'],
    #         'sender': 'server',
    #         'time': time.time(),
    #         'message_text': f'Сообщение для клиента {user_to_send} не отправлено'
    #     }
    #     try:
    #         if self.users[message['sender']]:
    #             back_socket = self.users[message['sender']]
    #             send_message(back_socket, failed_message)
    #     except:
    #         self.clients.remove(back_socket)
    #         del self.users[message['sender']]

    #     server_log.info(f'Сообщение: {message} \n для клиента не отправлено.'
    #                         f'Такого пользователя {user_to_send} нет.')
    #     failed_message ={}
