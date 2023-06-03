import logging


_format = logging.Formatter("%(levelname)-10s %(asctime)s %(funcName)s %(message)s")

cl_hand = logging.FileHandler('logs/logs/client/client', encoding="utf-8")
cl_hand.setFormatter(_format)

client_log = logging.getLogger('client_log')
client_log.setLevel(logging.DEBUG)
client_log.addHandler(cl_hand)
