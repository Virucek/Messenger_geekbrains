import json
import sys
from socket import *
import argparse
import time

from include import protocol
from include.utils import get_message, send_message
from include.variables import *


def process_incoming_message(message):
    if RESPONSE in message:
        if message[RESPONSE] == RESPCODE_OK:
            return True
        return False
    return ValueError


def create_presence():
    msg = protocol.PRESENCE_MSG_CLIENT
    msg[TIME] = time.time()
    msg[USER][STATUS] = 'Presense status test?'
    return msg


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('host', nargs='?', default=DEFAULT_HOST, help='server host ip address')
    parser.add_argument('port', nargs='?', default=DEFAULT_PORT, type=int, help='server port')

    args = parser.parse_args()

    with socket(AF_INET, SOCK_STREAM) as client_sock:
        try:
            client_sock.connect((args.host, args.port))
        except OSError as e:
            print(e)
            sys.exit(1)

        send_message(client_sock, create_presence())
        try:
            answer = get_message(client_sock)
            if process_incoming_message(answer):
                print('Сообщение от сервера: 200')
            else:
                print(f'Сообщение от сервера:\n {answer}')
        except ValueError:
            print('Ошибка декодирования сообщения от сервера')


if __name__ == '__main__':
    main()
