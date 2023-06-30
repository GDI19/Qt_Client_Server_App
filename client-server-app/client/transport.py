import socket
import sys
import time
import logging
import json
import threading
from PyQt5.QtCore import pyqtSignal, QObject

sys.path.append('../')
from common.utils import *
from common.errors import ServerError

client_log = logging.getLogger('client_log')

DEFAULT_PORT =7777
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject): # metaclass=ClientVerifier
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()
    
    def __init__(self, ip_address, port, database, username):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        
        self.database = database        
        self.username = username
        self.transport = None
        self.connection_init(ip_address, port)

        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                client_log.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            client_log.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            client_log.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
            # Флаг продолжения работы транспорта.
        self.running = True

    def connection_init(self, ip, port):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Таймаут для освобождения сокета.
        self.transport.settimeout(5)

        connected = False
        for i in range(5):
            client_log.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            client_log.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        client_log.debug('Установлено соединение с сервером')

        # Посылаем серверу приветственное сообщение и получаем ответ.
        try:
            with socket_lock:
                send_message(self.transport, self.create_presence())
                self.process_server_answer(get_message(self.transport))
        except (OSError, json.JSONDecodeError):
            client_log.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')

        # Раз всё хорошо, сообщение о установке соединения.
        client_log.info('Соединение с сервером успешно установлено.')


    def create_presence(self):
        presence_msg = {
            "action": "presence",
            "time": time.time(),
            'user':{
                "account_name": self.username}
        }
        client_log.info(f'created presence with user: `{self.username}`')
        return presence_msg
    

    def process_server_answer(self, message):
        client_log.debug(f'Разбор приветственного сообщения от сервера: {message}')
        if 'response' in message:
            if message['response'] == 200:  
                return '200: ok'
            elif message['response'] == 400:
                raise ServerError(f"400 : {message['error']}")
            else:
                client_log.debug(f"Принят неизвестный код подтверждения {message['response']}")

        elif 'action' in message and message['action'] == 'message' and 'sender' in message and 'message_text' in message and 'time' in message:
            self.database.save_message(message['sender'], 'in', message['message_text'])    
            self.new_message.emit(message['sender'])
            
            client_log.info(f'Получено сообщение от пользователя {message["sender"]}')
        else:
            client_log.error(f'Получено некорректное сообщение с сервера: {message}')


    def contacts_list_update(self):
        client_log.debug(f'Запрос контакт листа для пользователся {self.username}')
        req = {
            'action': 'get_contacts',
            'time': time.time(),
            'user': self.username
        }
        client_log.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        client_log.debug(f'Получен ответ {ans}')
        if 'response' in ans and ans['response']==202:
            for contact in ans['data_list']:
                self.database.add_contact(contact)
        else:
            client_log.error('Не удалось обновить список контактов.')

    
    # Функция списка известных пользователей
    def user_list_update(self):
        client_log.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            'action': 'get_users',
            'time': time.time(),
            'account_name': self.username
        }
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if 'response' in ans and ans['response'] == 202:
            self.database.add_users(ans['data_list']) 
        else:
            client_log.error('Не удалось обновить список известных пользователей.')


    # Функция добавления пользователя в контакт лист
    def add_contact(self, contact):
        client_log.debug(f'Создание контакта {contact}')
        req = {
            'action': 'add',
            'time': time.time(),
            'user': self.username,
            'account_name': contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_answer(get_message(self.transport))


    # Функция удаления пользователя из контакт листа
    def remove_contact(self, contact):
        client_log.debug(f'Удаление контакта {contact}')
        req = {
            'action': 'remove',
            'time': time.time(),
            'user': self.username,
            'account_name': contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_answer(get_message(self.transport))


    def transport_shutdown(self):
        self.running = False
        exit_message = {
            "action": "exit",
            "time": time.time(),
            "user":{
                "account_name": self.username}
        }
        with socket_lock:
            try:
                send_message(self.transport, exit_message)
            except OSError:
                pass
        client_log.debug('Транспорт завершает работу.')
        time.sleep(0.5)


    def send_message(self, send_to, text_for_msg):
        msg_to_send ={
            'action': 'message',
            'send_to': send_to,
            'sender': self.username,
            'time': time.time(),
            'message_text': text_for_msg
        }
        # Необходимо дождаться освобождения сокета для отправки сообщения
        with socket_lock:
            send_message(self.transport, msg_to_send)
            self.process_server_answer(get_message(self.transport))
            client_log.info(f'Отправлено сообщение для пользователя {send_to}')    


    def run(self):
        client_log.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        client_log.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    client_log.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    client_log.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_answer(message)
                finally:
                    self.transport.settimeout(5)
    

"""
    def print_history(self):
        ask = input('Показат1ь входящие сообщения - in, исходящие - out, все - просто Enter:')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.user_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.user_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    client_log.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.user_name, edit)                    
                    except:
                        client_log.error('Не удалось отправить информацию на сервер.')
    

# Функция инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера.
def database_load(sock, database, username):
    # Загружаем список известных пользователей
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        client_log.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)




    # Загружаем список контактов
try:
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Таймаут 1 секунда, необходим для освобождения сокета.
    transport.settimeout(1)
    contacts_list = contacts_list_request(sock, username)
except ServerError:
    client_log.error('Ошибка запроса списка контактов.')
else:
    for contact in contacts_list:
        database.add_contact(contact)

    transport.connect((server_address, server_port))
    send_message(transport, create_presence(client_name))
    answer = process_response_answer(get_message(transport))
    
    client_log.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
    print(f'Установлено соединение с сервером.')

except json.JSONDecodeError:
    client_log.error('Не удалось декодировать полученную Json строку.')
    exit(1)
except ServerError as error:
    client_log.error(f'При установке соединения сервер вернул ошибку: {error.text}')
    exit(1)
except ReqFieldMissingError as missing_error:
    client_log.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
    exit(1)
except (ConnectionRefusedError, ConnectionError):
    client_log.critical(f'Не удалось подключиться к серверу {server_address}:{server_port},' 
                        f'конечный компьютер отверг запрос на подключение.')
    exit(1)
else:

    # Инициализация БД
    database = ClientDatabase(client_name)
    database_load(transport, database, client_name)

    module_sender = ClientSender(client_name, transport, database)
    module_sender.daemon = True
    module_sender.start()
    client_log.debug('Запущены процессы')

    
    module_receiver = ClientListener(client_name, transport, database)
    module_receiver.daemon = True
    module_receiver.start()

    while True:
        time.sleep(1)
        if module_receiver.is_alive() and module_sender.is_alive():
            continue
        break


"""