import argparse
import os
import sys
import logging
from client.client_database import ClientDatabase
from common.errors import *
from common.metaclasses import ClientVerifier
from PyQt5.QtWidgets import QApplication, QMessageBox
from logs.client_log_config import log
from common.utils import get_message, send_message
from client.client_database import ClientDatabase
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from Cryptodome.PublicKey import RSA

DEFAULT_PORT =7777

client_log = logging.getLogger('client_log')

@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default='localhost', nargs='?')
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-pass', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.a
    server_port = namespace.p
    client_name = namespace.name
    client_passwd = namespace.password

    if not 1023 < server_port < 65536:
        client_log.critical(f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    return server_address, server_port, client_name, client_passwd


if __name__ == '__main__':
    # Сообщаем о запуске
    # print('Консольный месседжер. Клиентский модуль.')

    # Загружаем параметы коммандной строки
    server_address, server_port, client_name, client_passwd = arg_parser()

    client_app = QApplication(sys.argv)
        
    start_dialog = UserNameDialog()
    if not client_name or not client_passwd:
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            client_log.debug(f'Using USERNAME = {client_name}, PASSWD = {client_passwd}.')
        else:
            exit(0)

    client_log.info(f'Запущен клиент с парамертами: адрес сервера: {server_address},'
                    f' порт: {server_port}, имя пользователя: {client_name}')
    

    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key_file:
            key_file.write(keys.export_key())
    else:
        with open(key_file, 'rb') as k_f:
            keys = RSA.import_key(k_f.read())

    client_log.debug("Keys sucsessfully loaded.")

    database = ClientDatabase(client_name)

    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport = ClientTransport(
            server_address, 
            server_port, 
            database, 
            client_name,
            client_passwd,
            keys)
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        exit(1)

    transport.setDaemon(True)
    transport.start()

    del start_dialog
    
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()