import unittest
from http.client import BAD_REQUEST
from unittest import TestCase
from xmlrpc.client import SERVER_ERROR

from include.protocol import SERVER_RESPONSE_OK, SERVER_RESPONSE_BAD_REQUEST, SERVER_RESPONSE_SERVER_ERROR
from include.variables import RESPCODE_OK, ACTION, PRESENCE, TIME, TYPE, STATUS, USER, ACCOUNT_NAME, NOT_LOGGED_USER, \
    RESPCODE_BAD_REQ
from server import create_response, process_incoming_message


class TestServer(TestCase):

    def test_create_OK_request(self):
        self.assertEqual(create_response(RESPCODE_OK), SERVER_RESPONSE_OK)

    def test_create_BAD_REQ(self):
        self.assertEqual(create_response(BAD_REQUEST), SERVER_RESPONSE_BAD_REQUEST)

    def test_create_SERVER_ERROR(self):
        self.assertEqual(create_response(SERVER_ERROR), SERVER_RESPONSE_SERVER_ERROR)

    def test_create_SERVER_ERROR_with_msg(self):
        error_alert = 'Test error message!'
        expect_msg = SERVER_RESPONSE_SERVER_ERROR
        expect_msg['error'] = error_alert

        self.assertEqual(create_response(SERVER_ERROR, error_alert), expect_msg)

    def test_proc_inc_msg_ok(self):
        test_msg = {
            ACTION: PRESENCE,
            TIME: '100.10',
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: NOT_LOGGED_USER,
                STATUS: 'Presense status test?'
            }
        }

        self.assertEqual(process_incoming_message(test_msg), RESPCODE_OK)

    def test_proc_inc_msg_no_action(self):
        test_msg = {
            TIME: '100.10',
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: NOT_LOGGED_USER,
                STATUS: 'Presense status test?'
            }
        }

        self.assertEqual(process_incoming_message(test_msg), RESPCODE_BAD_REQ)

    def test_proc_inc_msg_wrong_action(self):
        test_msg = {
            ACTION: 'test',
            TIME: '100.10',
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: NOT_LOGGED_USER,
                STATUS: 'Presense status test?'
            }
        }

        self.assertEqual(process_incoming_message(test_msg), RESPCODE_BAD_REQ)

    def test_proc_inc_msg_no_time(self):
        test_msg = {
            ACTION: PRESENCE,
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: NOT_LOGGED_USER,
                STATUS: 'Presense status test?'
            }
        }

        self.assertEqual(process_incoming_message(test_msg), RESPCODE_BAD_REQ)

    def test_proc_inc_msg_no_type(self):
        test_msg = {
            ACTION: PRESENCE,
            TIME: '100.10',
            USER: {
                ACCOUNT_NAME: NOT_LOGGED_USER,
                STATUS: 'Presense status test?'
            }
        }

        self.assertEqual(process_incoming_message(test_msg), RESPCODE_BAD_REQ)

    def test_proc_inc_msg_no_acc_name(self):
        test_msg = {
            ACTION: PRESENCE,
            TIME: '100.10',
            TYPE: STATUS,
            USER: {
                STATUS: 'Presense status test?'
            }
        }

        self.assertEqual(process_incoming_message(test_msg), RESPCODE_BAD_REQ)

    def test_proc_inc_msg_wrong_acc_name(self):
        test_msg = {
            ACTION: PRESENCE,
            TIME: '100.10',
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: 'not anonymous',
                STATUS: 'Presense status test?'
            }
        }

        self.assertEqual(process_incoming_message(test_msg), RESPCODE_BAD_REQ)

    def test_proc_inc_msg_no_status(self):
        test_msg = {
            ACTION: PRESENCE,
            TIME: '100.10',
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: NOT_LOGGED_USER,
            }
        }

        self.assertEqual(process_incoming_message(test_msg), RESPCODE_BAD_REQ)

    def test_proc_inc_msg_no_user(self):
        test_msg = {
            ACTION: PRESENCE,
            TIME: '100.10',
            TYPE: STATUS,
        }

        self.assertEqual(process_incoming_message(test_msg), RESPCODE_BAD_REQ)

    def test_proc_inc_msg_exceed_field(self):
        test_msg = {
            ACTION: PRESENCE,
            'test': 'test',
            TIME: '100.10',
            TYPE: STATUS,
            USER: {
                ACCOUNT_NAME: NOT_LOGGED_USER,
                STATUS: 'Presense status test?'
            }
        }

        self.assertEqual(process_incoming_message(test_msg), RESPCODE_BAD_REQ)


if __name__ == '__main__':
    unittest.main()
