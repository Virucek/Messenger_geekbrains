import json
from socket import *
import argparse
import time

from include.utils import get_message, send_message
from include.variables import *


def process_incoming_message(message):
    if RESPONSE in message:
        if message[RESPONSE] == RESPONSE_OK:
            return True
        return False
    return ValueError


def create_presence(user_name='Anonimous'):
    msg = {
        ACTION: PRESENCE,
        TIME: time.time(),
        TYPE: 'status',
        USER: {
            ACCOUNT_NAME: user_name,
            STATUS: 'text',
        }
    }
    return msg


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('host', nargs='?', default=DEFAULT_HOST, help='server host ip address')
    parser.add_argument('port', nargs='?', default=DEFAULT_PORT, help='server port')

    args = parser.parse_args()

    with socket(AF_INET, SOCK_STREAM) as client_sock:
        client_sock.connect((args.host, args.port))
        send_message(client_sock, create_presence())
        try:
            answer = get_message(client_sock)
            if process_incoming_message(answer):
                print(f'Сообщение от сервера 200! ОК!')
            else:
                print('Сообщение от сервера не ОК! 400')
        except ValueError:
            print('Ошибка декодирования сообщения от сервера')


if __name__ == '__main__':
    main()
