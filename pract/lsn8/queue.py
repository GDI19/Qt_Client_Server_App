from threading import Thread
from queue import Queue


class WorkerThread(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_queue = Queue()
    
    def send(self, item):
        self.input_queue.put(item)
    
    def close(self):
        self.input_queue.put(None)
        self.input_queue.join()
    
    def run(self):
        while True:
            item = self.input_queue.get()
            if item is None:
                break
            # Обработать элемент (вместо print могут быть полезные операции)
            print(item)
            self.input_queue.task_done()
            # Конец. Сообщить, что сигнальная метка была принята, и выйти
        self.input_queue.task_done()

# Пример использования
w = WorkerThread()
w.start()
# Отправить элемент на обработку (с помощью очереди)
w.send("hello")
w.send("world")
w.close()