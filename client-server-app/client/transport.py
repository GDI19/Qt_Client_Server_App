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
  