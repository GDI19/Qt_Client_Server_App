import json
import unittest
import sys
import os
sys.path.append(os.path.join(os.getcwd(), '..'))

from common.utils import get_message, send_message


class TestSocket:
    '''
    Тестовый класс для тестирования отправки и получения,
    при создании требует словарь, который будет прогонятся
    через тестовую функцию
    '''
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_msg = None
        self.received_msg = None

    def send(self, msg_to_send):
        """
        Тестовая функция отправки, корретно  кодирует сообщение,
        так-же сохраняет что должно было отправлено в сокет.
        msg_to_send - то, что отправляем в сокет
        :param message_to_send:
        :return:
        """
        json_test_msg = json.dumps(self.test_dict)
        self.encoded_msg = json_test_msg.encode('utf-8')
        self.received_msg = msg_to_send

    def recv(self, max_len):
        """
        Получаем данные из сокета
        :param max_len:
        :return:
        """
        json_test_msg = json.dumps(self.test_dict)
        return json_test_msg.encode('utf-8')
    

class Tests(unittest.TestCase):
    '''
    Тестовый класс, собственно выполняющий тестирование.
    '''
    test_dict_send = {
        'action': 'presence',
        'time': 111111.111111,
        'user': {
            'account_name': 'test_test'
        }
    }
    test_dict_recv_ok = {'response': 200}
    test_dict_recv_err = {
        'response': 400,
        'error': 'Bad Request'
    }

    def test_send_msg(self):
        """
        Тестируем корректность работы фукции отправки,
        создадим тестовый сокет и проверим корректность отправки словаря
        :return:
        """
        test_sock = TestSocket(self.test_dict_send)
        send_message(test_sock, self.test_dict_send)

        self.assertEqual(test_sock.encoded_msg, test_sock.received_msg)
        # дополнительно, проверим генерацию исключения, при не словаре на входе.
        with self.assertRaises(Exception):
            send_message(test_sock, test_sock)
            

    def test_get_message(self):
        """
        Тест функции приёма сообщения
        :return:
        """
        test_sock_ok = TestSocket(self.test_dict_recv_ok)
        self.assertEqual(get_message(test_sock_ok), self.test_dict_recv_ok)

        test_sock_err = TestSocket(self.test_dict_recv_err)
        self.assertEqual(get_message(test_sock_err), self.test_dict_recv_err)


    
if __name__ == '__main__':
    unittest.main()