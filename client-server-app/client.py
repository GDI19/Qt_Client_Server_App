import argparse
from collections.abc import Callable, Iterable, Mapping
import os
from socket import *
import sys
import time
import json
import logging
import configparser
from typing import Any
from client_database import ClientDatabase
from class_serverdb import ServerStorage
from common.errors import *
from metaclasses import ClientVerifier
import logs.client_log_config
from logs.client_log_config import log
from datetime import datetime
import threading
from common.utils import get_message, send_message



client_log = logging.getLogger('client_log')

DEFAULT_PORT =7777

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.user_name = account_name
        self.sock = sock
        self.database = database
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
        send_to = input('Введите имя пользователя для кого сообщение!\n')
        text_for_msg = input('Введите сообщение:\n')

        with database_lock:
            if not self.database.check_user(send_to):
                client_log.error(f'Попытка отправить сообщение незарегистрированому получателю: {send_to}')
                return
    
        msg_to_send ={
            'action': 'message',
            'send_to': send_to,
            'sender': self.user_name,
            'time': time.time(),
            'message_text': text_for_msg
        }
         # Сохраняем сообщения для истории
        with database_lock:
            self.database.save_message(self.user_name, send_to, msg_to_send)

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            try:
                send_message(self.sock, msg_to_send)
                client_log.info(f'Отправлено сообщение для пользователя {send_to}')
            except OSError as err:
                if err.errno:
                    client_log.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    client_log.error('Не удалось передать сообщение. Таймаут соединения')


    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду:')
            if command == 'message': # in ['message', 'Message', 'MESSAGE']:
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':# ['exit', 'EXIT', 'Exit']:
                with sock_lock:
                    try:
                        exit_message = self.create_exit_message()
                        send_message(self.sock, exit_message)
                    except:
                        pass
                    print('Спасибо, за работу! До скорой встречи')
                    client_log.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            elif command == 'contacts':
                with database_lock:
                    contact_list = self.database.get_contacts()
                for contact in contact_list:
                    print(contact)
            elif command == 'edit':
                self.edit_contacts()
            elif command == 'history':
                self.print_history()

            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')


    def print_help(self):
        print('-'*15, 'Поддерживаемые команды:', '-'*15)
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')
        print('-'*30)

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter:')
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

                    
class ClientListener(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.user_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self) -> None:
        while True:
            # Без задержки, второй поток может долго ждать освобождения сокета
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)
                    client_log.info(f'message from server received: {message}')       
                # Принято некорректное сообщение
                except IncorrectDataRecivedError:
                    client_log.error(f'Не удалось декодировать полученное сообщение.')
                # Вышел таймаут соединения если errno = None, иначе обрыв соединения.
                except OSError as err:
                    if err.errno:
                        client_log.critical(f'Потеряно соединение с сервером.')
                        break
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    client_log.critical(f'Потеряно соединение с сервером.')
                    break
                # Если пакет корретно получен выводим в консоль и записываем в базу.

                else:
                    if 'action' in message and message['action'] == 'message' and 'sender' in message and 'message_text' in message and 'time' in message:
                        msg_time = datetime.fromtimestamp(message['time']).replace(second=0, microsecond=0)
                        sender = message['sender']
                        msg = message['message_text']
                        print('-'*15, 'Reseived Message' ,'-'*15)
                        print(f'{msg_time} - {sender}: {msg}')
                        print('-'*30)

                        with database_lock:
                            try:
                                self.database.save_message(sender, self.user_name, msg)
                            except:
                                client_log.error('Ошибка взаимодействия с базой данных')
                        client_log.info(f'Получено сообщение от пользователя {sender:\n} {msg}')
                    else:
                        client_log.error(f'Получено некорректное сообщение с сервера: {message}')
                    
        

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


def contacts_list_request(sock, name):
    client_log.debug(f'Запрос контакт листа для пользователся {name}')
    req = {
        'action': 'get_contacts',
        'time': time.time(),
        'user': name
    }
    client_log.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    client_log.debug(f'Получен ответ {ans}')
    if 'response' in ans and ans['response']:
        return ans['data_list']
    else:
        raise ServerError
    

# Функция добавления пользователя в контакт лист
def add_contact(sock, username, contact):
    client_log.debug(f'Создание контакта {contact}')
    req = {
        'action': 'add',
        'time': time.time(),
        'user': username,
        'account_name': contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if 'response' in ans and ans['resoonse'] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


# Функция запроса списка известных пользователей
def user_list_request(sock, username):
    client_log.debug(f'Запрос списка известных пользователей {username}')
    req = {
        'action': 'get_users',
        'time': time.time(),
        'account_name': username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 202:
        return ans['data_list']
    else:
        raise ServerError


# Функция удаления пользователя из контакт листа
def remove_contact(sock, username, contact):
    client_log.debug(f'Создание контакта {contact}')
    req = {
        'action': 'remove',
        'time': time.time(),
        'user': username,
        'account_name': contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


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
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        client_log.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)



def main():
    # Сообщаем о запуске
    print('Консольный месседжер. Клиентский модуль.')

    # Загружаем параметы коммандной строки
    server_address, server_port, client_name = arg_parser()

    # Если имя пользователя не было задано, необходимо запросить пользователя.
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    client_log.info(f'Запущен клиент с парамертами: адрес сервера: {server_address} ,' 
                    f'порт: {server_port}, имя пользователя: {client_name}')

    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Таймаут 1 секунда, необходим для освобождения сокета.
        transport.settimeout(1)

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


if __name__ == '__main__':
    main()
        