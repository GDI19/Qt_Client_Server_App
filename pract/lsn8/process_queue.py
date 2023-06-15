import multiprocessing

def consumer(input_q):
    while True:
        item = input_q.get()
        # Обработать элемент
        if item is None:
            break
        print(item) # <- Здесь может быть обработка элемента
        # Сообщить о завершении обработки
        # input_q.task_done()
    print("Потребитель завершил работу")


def producer(sequence, output_q):
    for item in sequence:
        output_q.put(item) # Добавить элемент в очередь


if __name__ == '__main__':
    q = multiprocessing.JoinableQueue()
    # Запустить процесс-потребитель
    cons_p = multiprocessing.Process(target=consumer, args=(q, ))
    cons_p.daemon = True
    cons_p.start()
    # cons_p2 = multiprocessing.Process(target=consumer, args=(q, ))
    # cons_p2.daemon = True
    # cons_p2.start()

    # Воспроизвести элементы.
    # sequence — последовательность элементов, которые передаются потребителю.
    # На практике вместо переменной можно использовать генератор
    # или воспроизводить элементы каким-либо другим способом.
    sequence = [1,2,3,4]
    producer(sequence, q)
    # q.join() # Дождаться, пока все элементы не будут обработаны
    q.put(None)
    cons_p.join()