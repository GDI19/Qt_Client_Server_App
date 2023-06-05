from functools import wraps
import logging
import traceback


_format = logging.Formatter("%(levelname)-10s %(asctime)s %(funcName)s %(message)s")

cl_hand = logging.FileHandler('logs/logs/client/client', encoding="utf-8")
cl_hand.setFormatter(_format)

client_log = logging.getLogger('client_log')
client_log.setLevel(logging.DEBUG)
client_log.addHandler(cl_hand)


def log(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        client_log.info(f'Before function call: {func.__name__} with parameters {args} & {kwargs}.')
        res = func(*args, **kwargs)
        client_log.info(f'After function call: {func.__name__}.' 
                        f' Вызов из модуля {func.__module__}.'
                        f' Вызов из функции {traceback.format_stack()[0].strip().split()[-1]}.')
        return res
    return wrap