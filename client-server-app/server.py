import argparse
import configparser
import json
import os
import select
from socket import *
import sys
import threading
import time
import logging
from class_serverdb import ServerStorage
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from sqlalchemy import create_engine
from metaclasses import ServerVerifier
import logs.server_log_config
from logs.server_log_config import log
from common.utils import get_message, send_message
from descriptors import Port

server_log = logging.getLogger('server_log')

DEFAULT_PORT = 7777

# Флаг что был подключён новый пользователь, нужен чтобы не мучать BD
# постоянными запросами на обновление
new_connection = False
conflag_lock = threading.Lock()


@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default='', nargs='?')
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()
    def __init__(self, listen_address, listen_port, database):
        self.address = listen_address
        self.port = listen_port

        #  {username: socket, ...} Словарь имен и соответствующие им сокеты
        self.users = {}

        # [socket, ...] Список подключённых клиентов
        self.clients = []

        # [(username_from, message, username_to), ...] Список сообщений на отправку
        self.messages = []  

        self.database = database

        super().__init__()


    def init_socket(self):
        server_log.debug('Server has been launched...')
        server_log.info(
            f'Запущен сервер: {self.address} порт: {self.port}, '
            f'Если адрес не указан, принимаются соединения с любых адресов.')

        transport = socket(AF_INET, SOCK_STREAM)
        # transport.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        transport.bind((self.address, self.port))
        # transport.listen(5)
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen()


    def run(self):
        self.init_socket()

        while True:
            try:
                client, addr = self.sock.accept()
            except OSError as err:
                pass
            else:
                print("Получен запрос на соединение с %s" % str(addr))
                server_log.info(f'Установлено соедение с ПК {self.address}')
                self.clients.append(client)

            read_lst = [] 
            write_lst = []
            error_lst = []

            try:
                if self.clients:
                    read_lst, write_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if read_lst:
                for client_with_message in read_lst:
                    try:
                        msg_from_client = get_message(client_with_message)
                        server_log.info(f'received message from client: {msg_from_client}')
                        self.process_client_message(msg_from_client, client_with_message)
                    except:
                        server_log.error(f'Клиент {client_with_message} отключился от сервера.')
                        self.clients.remove(client_with_message)
                        
                        for name in self.users:
                            if self.users[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.users[name]
                                break
                
            if self.messages:
                for message in self.messages:
                    recipient = message['send_to']
                    try:
                        self.process_message_to_send(message, recipient, write_lst)
                    except:
                        server_log.info(f'Связь с клиентом с именем {recipient} была потеряна')
                        self.send_msg_failed_notification(message, recipient)
                        self.clients.remove(self.users[recipient])
                        del self.users[recipient]
                self.messages.clear()


            """
            while self.messages and write_lst:
                user_to_send = self.messages[0][2]
                message = {
                        'action': 'message',
                        'send_to': user_to_send,
                        'sender': self.messages[0][0],
                        'time': time.time(),
                        'message_text': self.messages[0][1]
                    }
                del self.messages[0]
                if user_to_send in ['all', 'All', 'ALL']:
                    for waiting_client in write_lst:
                        try:
                            send_message(waiting_client, message)
                        except:
                            server_log.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                            self.clients.remove(waiting_client)
                            

                elif user_to_send in self.users:
                    socket_to_send = self.users[user_to_send]
                    if socket_to_send in write_lst:    
                        try:
                            send_message(socket_to_send, message)
                        except:
                            self.send_msg_failed_notification(message, user_to_send)
                            server_log.info(f'Клиент {socket_to_send.getpeername()} отключился от сервера.')
                            self.users.pop(user_to_send)
                    else:
                        self.send_msg_failed_notification(message, user_to_send)
                        server_log.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                        self.users.pop(user_to_send)

                else:           
                    self.send_msg_failed_notification(message, user_to_send)
        """
            
    
    def process_message_to_send(self, message, recipient, listen_socks):
        if recipient in self.users and self.users[recipient] in listen_socks:
            send_message(self.users[recipient], message)
            server_log.info(f"Отправлено сообщение пользователю {recipient} от пользователя {message['sender']}.")
            return
        elif recipient in self.users and self.users[recipient] not in listen_socks:
            server_log.info(f'Связь с клиентом с именем {recipient} была потеряна')
        else:
            server_log.error(
                f'Пользователь {recipient} не зарегистрирован на сервере, отправка сообщения невозможна.')

        self.send_msg_failed_notification(message, recipient)



    def process_client_message(self, message, client):
        """
        Receive message from client, check it.
        :param message: dict
        :return: response (dict)
        """
        global new_connection
        if 'time' in message and 'action' in message:
            if message['action'] == 'exit'  and  'user' in message and 'account_name' in message['user']:
                self.database.user_logout(message['user']['account_name'])
                self.clients.remove(client)
                client.close()
                del self.users[message['user']['account_name']]
                with conflag_lock:
                    new_connection = True
                return
            
            elif message['action'] == 'presence'  and  'user' in message and 'account_name' in message['user']:
                new_user_in = message['user']['account_name']
                if new_user_in not in self.users:
                    self.users[new_user_in] = client
                    client_ip, client_port = client.getpeername()
                    self.database.user_login(new_user_in, client_ip, client_port)
                    send_message(client, {'response': 200})
                    with conflag_lock:
                        new_connection = True
                else:
                    send_message(client, {'response': 400, 'error': f'Пользователь с таким именем: {new_user_in} уже подключен.'})
                    self.clients.remove(client)
                    client.close()
                return
            
            elif message['action'] == 'message' and 'message_text' in message and 'send_to' in message \
                and 'sender' in message and self.users[message['sender']] == client:
                self.messages.append(message)
                self.database.process_message(message['sender'], message['send_to'])
                return
            
            elif message['action'] == 'get_contacts' and 'user' in message and \
                self.users[message['user']] == client:
                response = {'response': 202, 'data_list':None}
                response['data_list'] = self.database.get_contacts(message['user'])
                send_message(client, response)
                return

            elif message['action'] == 'add' and 'account_name' in message and 'user' in message \
                and self.users[message['user']] == client:
                self.database.add_contact(message['user'], message['account_name'])
                send_message(client, {'response': 200})
                return
            
            elif message['action'] == 'remove' and 'account_name' in message and 'user' in message \
                and self.users[message['user']] == client:
                self.database.remove_contact(message['user'], message['account_name'])
                send_message(client, {'response': 200})

            elif  message['action'] == 'get_users' and 'account_name' in message \
                and self.names[message['account_name']] == client:
                response = {'response': 202, 'data_list':None}
                response['data_list'] = [user[0] for user in self.database.users_list()]
                send_message(client, response)
                return

        server_log.critical('Processed msg with noncorrect info')
        send_message(client, {'response': 400, 'error': 'Bad Request'})
        return


    def send_msg_failed_notification(self, message, user_to_send):
        failed_message = {
            'action': 'message',
            'send_to': message['sender'],
            'sender': 'server',
            'time': time.time(),
            'message_text': f'Сообщение для клиента {user_to_send} не отправлено'
        }
        try:
            back_socket = self.users[message['sender']]
            send_message(back_socket, failed_message)
        except:
            self.clients.remove(back_socket)
            del self.users[message['sender']]
            
        server_log.info(f'Сообщение: {message} \n для клиента не отправлено.'
                            f'Такого пользователя {user_to_send} нет.')
        failed_message ={}
        

def print_help():
    print('Поддерживаемые комманды:')
    print('users - список известных пользователей')
    print('connected - список подключенных пользователей')
    print('loghistory - история входов пользователя')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')


def main():
    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    # Загрузка параметров командной строки, если нет параметров, то задаём
    # значения по умоланию.
    listen_address, listen_port = arg_parser(config['SETTINGS']['Listen_Address'], config['SETTINGS']['Default_port'])
    
    database = ServerStorage(os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))
    
    # listen_address, listen_port = arg_parser()
    # database = ServerStorage()

    # Создание экземпляра класса - сервера и его запуск:
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()


    # Создаём графическое окуружение для сервера:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()


    # Инициализируем параметры в окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # Функция обновляющяя список подключённых, проверяет флаг подключения, и
    # если надо обновляет список
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Функция создающяя окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()

if __name__ == '__main__':
    main()