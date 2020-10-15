import json
import unittest
from unittest import TestCase

from include.protocol import PRESENCE_MSG_CLIENT, SERVER_RESPONSE_OK, SERVER_RESPONSE_BAD_REQUEST, \
    SERVER_RESPONSE_SERVER_ERROR
from include.utils import send_message, get_message
from include.variables import ENCODING, TIME, USER, STATUS


class TestSocket:

    def __init__(self, socket_dict):
        self.socket_dict = socket_dict
        self.encoded_msg, self.received_msg = None, None

    def send(self, message):
        json_msg = json.dumps(self.socket_dict)
        self.encoded_msg = json_msg.encode(ENCODING)
        self.received_msg = message

    def recv(self, _):
        json_msg = json.dumps(self.socket_dict)
        enc_msg = json_msg.encode(ENCODING)
        return enc_msg


class TestUtils(TestCase):

    test_msg_send = PRESENCE_MSG_CLIENT
    test_msg_send[TIME] = 15000.233
    test_msg_send[USER][STATUS] = 'Test socket test ! 123#'

    test_incorrect_msg_send = 'test'

    test_ok_msg_get = SERVER_RESPONSE_OK
    test_bad_req_msg_get = SERVER_RESPONSE_BAD_REQUEST
    test_server_err_msg_get = SERVER_RESPONSE_SERVER_ERROR

    def test_send_ok_message(self):
        test_socket = TestSocket(self.test_msg_send)
        send_message(test_socket, self.test_msg_send)

        self.assertEqual(test_socket.encoded_msg, test_socket.received_msg)

    def test_send_incorrect_message(self):
        test_socket = TestSocket(self.test_msg_send)
        send_message(test_socket, self.test_msg_send)

        self.assertRaises(ValueError, send_message, test_socket, self.test_incorrect_msg_send)

    def test_get_ok_message(self):
        test_socket = TestSocket(self.test_ok_msg_get)
        self.assertEqual(get_message(test_socket), self.test_ok_msg_get)

    def test_get_bad_req_message(self):
        test_socket = TestSocket(self.test_bad_req_msg_get)
        self.assertEqual(get_message(test_socket), self.test_bad_req_msg_get)

    def test_get_server_error_message(self):
        test_socket = TestSocket(self.test_server_err_msg_get)
        self.assertEqual(get_message(test_socket), self.test_server_err_msg_get)


if __name__ == '__main__':
    unittest.main()
