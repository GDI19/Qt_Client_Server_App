from functools import wraps
import logging
import logging.handlers
import sys
import traceback


format = logging.Formatter('%(levelname)-10s %(asctime)s %(funcName)s %(message)s')

crit_hand = logging.StreamHandler(sys.stderr)
crit_hand.setLevel(logging.CRITICAL)
crit_hand.setFormatter(format)

app_log_hand = logging.handlers.TimedRotatingFileHandler('logs/logs/server/server', when='M', interval=1, encoding='utf-8')
#app_log_hand.setLevel(logging.DEBUG)
app_log_hand.setFormatter(format)

server_log = logging.getLogger('server_log')
server_log.setLevel(logging.DEBUG)

server_log.addHandler(crit_hand)
server_log.addHandler(app_log_hand)


def log(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        server_log.info(f'Before function call: {func.__name__} with parameters {args} & {kwargs}.')
        res = func(*args, **kwargs)
        server_log.info(f'After function call: {func.__name__}.' 
                        f' Вызов из модуля {func.__module__}.'
                        f' Вызов из функции {traceback.format_stack()[0].strip().split()[-1]}.')
        return res
    return wrap