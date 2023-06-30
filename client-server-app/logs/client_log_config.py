from functools import wraps
import inspect
import logging
import traceback


_format = logging.Formatter("%(levelname)-10s %(asctime)s %(funcName)s %(message)s")

cl_hand = logging.FileHandler('client-server-app/logs/logs/client/client', encoding="utf-8")
cl_hand.setFormatter(_format)

client_log = logging.getLogger('client_log')
client_log.setLevel(logging.DEBUG)
client_log.addHandler(cl_hand)


def log(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        client_log.debug(f'Была вызвана функция {func.__name__} c параметрами {args} , {kwargs}. Вызов из модуля {func.__module__}')
        res = func(*args, **kwargs)
        return res
    return wrap