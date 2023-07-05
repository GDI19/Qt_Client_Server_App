import argparse
import sys
import logging
from client.client_database import ClientDatabase
from common.errors import *
from common.metaclasses import ClientVerifier
from PyQt5.QtWidgets import QApplication
from logs.client_log_config import log
from common.utils import get_message, send_message
from client.client_database import ClientDatabase
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog

DEFAULT_PORT =7777

client_log = logging.getLogger('client_log')

@log
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


if __name__ == '__main__':
    # Сообщаем о запуске
    # print('Консольный месседжер. Клиентский модуль.')

    # Загружаем параметы коммандной строки
    server_address, server_port, client_name = arg_parser()

    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    client_log.info(f'Запущен клиент с парамертами: адрес сервера: {server_address},'
                    f' порт: {server_port}, имя пользователя: {client_name}')
    
    database = ClientDatabase(client_name)

    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport = ClientTransport(server_address, server_port, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)

    transport.setDaemon(True)
    transport.start()
    
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()