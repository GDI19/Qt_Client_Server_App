import unittest
import sys
import os
sys.path.append(os.path.join(os.getcwd(), '..'))


from server import process_client_message


class TestProcessClientMessage(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_process_ok(self):
        r = process_client_message({"action": "presence","time": "1234456", "user": {"account_name": "guest"}})
        self.assertEqual(r, {'response': 200})


    def test_diff_action(self):
        r = process_client_message({"action": "message","time": "1234456", "user": {"account_name": "guest"}})
        self.assertEqual(r, {'response': 400, 'error': 'Bad Request'})


    def test_no_action(self):
        r = process_client_message({"time": "1234456", "user": {"account_name": "guest"}})
        self.assertEqual(r, {'response': 400, 'error': 'Bad Request'})


    def test_no_time(self):
        r = process_client_message({"action": "presence","time": "1234456", "user": {"account_name": "guest"}})
        self.assertEqual(r, {'response': 400, 'error': 'Bad Request'})


    def test_no_user(self):
        r = process_client_message({"action": "presence","time": "1234456"})
        self.assertEqual(r, {'response': 400, 'error': 'Bad Request'})


    def test_no_time(self):
        r = process_client_message({"action": "presence","time": "1234456", "user": {"account_name": "Dany"}})
        self.assertEqual(r, {'response': 400, 'error': 'Bad Request'})


if __name__ == '__main__':
    unittest.main()