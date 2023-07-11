from threading import Thread
import time

# class ClockThread(Thread):
#     def __init__(self, interval):
#         super().__init__()
#         self.daemon = True
#         self.interval = interval
#     def run(self):
#         for i in range(10):
#             if i < 10:
#                 i=+i
#                 print(f"Текущее время {i}: %s" % time.ctime())
#                 time.sleep(self.interval)

# t = ClockThread(1)
# t.start()
# t.join(3)

import threading

items = 0
produced = threading.Semaphore(1)
consumed = threading.Semaphore(0)



def produce_item():
    items = items + 1
    print('produced item. total:', items)

def consume_item():
    items = items -1
    print('consumed item. total:', items)


def producer():
    while True:
        produced.acquire()
        produce_item()
        time.sleep(1)
        consumed.release()

def consumer():
    while True:
        consumed.acquire()
        consume_item()
        time.sleep(1)
        produced.release()


producer()
print('next')
consumer()