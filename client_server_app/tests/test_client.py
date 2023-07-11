import unittest
import sys
import os
sys.path.append(os.path.join(os.getcwd(), '..'))


from client import create_presence, process_answer


class TestCreatePresence(unittest.TestCase):
    def setUp(self) -> None:
        self.test_presence = create_presence()
        self.test_presence['time'] = '12345'

    def tearDown(self) -> None:
        pass

    def test_presence_ok(self):
        self.assertEqual(self.test_presence, {"action": "presence","time": "12345", "user": {"account_name": "guest"}}, 'Ups')


class TestProcessAnswer(unittest.TestCase):
    def test_answer_ok(self):
        answer = process_answer({'response': 200})
        self.assertEqual(answer, '200: ok')

    def test_answer_no_response(self):
        with self.assertRaises(ValueError):
            process_answer({'wrong': 200})

    def test_answer_bad_request(self):
        answer = process_answer({'response': 400, 'error': 'Bad Request'})
        self.assertEqual(answer, '400: Bad Request')
    


if __name__ == '__main__':
    unittest.main()