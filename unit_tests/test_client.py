import unittest
from unittest import TestCase

from client import create_presence, process_incoming_message
from include.variables import TIME, ACTION, PRESENCE, TYPE, STATUS, USER, ACCOUNT_NAME, NOT_LOGGED_USER, RESPONSE, \
    RESPCODE_OK, ALERT, RESPCODE_BAD_REQ, RESPCODE_SERVER_ERROR


class TestClient(TestCase):

    def test_create_presence(self):
        test_msg = create_presence()
        test_msg[TIME] = '100.10'

        expect_msg = {
            ACTION: PRESENCE,
            TIME: '100.10',
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: NOT_LOGGED_USER,
                STATUS: 'Presense status test?'
            }
        }

        self.assertEqual(test_msg, expect_msg)

    def test_proc_OK_resp(self):
        test_msg = {
            RESPONSE: RESPCODE_OK,
            ALERT: 'response OK'
        }

        self.assertEqual(process_incoming_message(test_msg), True)

    def test_proc_BAD_REQ_resp(self):
        test_msg = {
            RESPONSE: RESPCODE_BAD_REQ,
            ALERT: 'response BAD Request'
        }

        self.assertEqual(process_incoming_message(test_msg), False)

    def test_proc_SERVER_ERROR_resp(self):
        test_msg = {
            RESPONSE: RESPCODE_SERVER_ERROR,
            ALERT: 'response INTERNAL SERVER error'
        }

        self.assertEqual(process_incoming_message(test_msg), False)

    def test_proc_VALUE_ERROR(self):
        test_msg = {
            'test': 'test'
        }

        self.assertRaises(ValueError, process_incoming_message, test_msg)


if __name__ == '__main__':
    unittest.main()
