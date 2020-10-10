""" Серверный скрипт """
import argparse
from socket import *
import sys

from include import protocol
from include.utils import get_message, send_message
from include.variables import *


def create_response(resp_code, _error=None):
    if resp_code == RESPCODE_OK:
        return protocol.SERVER_RESPONSE_OK
    elif resp_code == RESPCODE_BAD_REQ:
        return protocol.SERVER_RESPONSE_BAD_REQUEST
    else:
        response = protocol.SERVER_RESPONSE_SERVER_ERROR
        if _error is not None:
            response.update({'error': _error})
        return response


def process_incoming_message(msg):
    if msg[ACTION] == PRESENCE:
        if msg.keys() != protocol.PRESENCE_MSG_CLIENT.keys():
            return RESPCODE_BAD_REQ
        if msg[USER][ACCOUNT_NAME] != NOT_LOGGED_USER:
            return RESPCODE_BAD_REQ
        return RESPCODE_OK
    return RESPCODE_BAD_REQ


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', action='store', dest='ip', default='', help='host ip of server')
    parser.add_argument('-p', action='store', dest='port', type=int, default=DEFAULT_PORT,
                        help='listening port of server')

    args = parser.parse_args()
    if args.port < 1024 or args.port > 65535:
        print('порт должен быть в диапазоне 1024-65535')
        sys.exit(1)

    with socket(AF_INET, SOCK_STREAM) as server_sock:
        try:
            server_sock.bind((args.ip, args.port))
            server_sock.listen(MAX_CONNECTIONS)
        except OSError as e:
            print(e)
            sys.exit(1)

        while True:
            client_sock, addr = server_sock.accept()
            with client_sock:
                error = None
                try:
                    inc_msg = get_message(client_sock)
                    print(inc_msg)
                    resp_code = process_incoming_message(inc_msg)
                except ValueError:
                    error = 'Ошибка декодирования сообщения от клиента'
                    resp_code = RESPCODE_SERVER_ERROR
                    print(error)
                resp_msg = create_response(resp_code, error)
                print(resp_msg)
                send_message(client_sock, resp_msg)


if __name__ == '__main__':
    main()
