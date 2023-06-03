import logging
import logging.handlers
import sys


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


