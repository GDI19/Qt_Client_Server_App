import logging

server_log = logging.getLogger('server_log')


class Port():
    def __set__(self, instance, value):
        if not 1024 < value < 65535:
            server_log.critical(
                f'Попытка запуска сервера с указанием неподходящего порта '
                f'{value}. Допустимы адреса с 1024 до 65535.')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        # owner - <class '__main__.Server'>
        # name - port
        self.name = name
            