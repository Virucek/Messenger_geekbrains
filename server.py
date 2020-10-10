import argparse
import json
from socket import *
import sys

from include.msg_formats import PRESENCE_MSG_CLIENT
from include.utils import get_message
from include.variables import *


def process_incoming_message(msg):
    for key in msg.keys():
        if key not in PRESENCE_MSG_CLIENT:
            return {RESPONSE: RESPONSE_BAD_REQUEST}
    if msg[ACTION] != PRESENCE:
        return {RESPONSE: RESPONSE_BAD_REQUEST}
    if msg[USER][ACCOUNT_NAME] != 'Anonimous':
        return {RESPONSE: RESPONSE_BAD_REQUEST}
    return {RESPONSE: RESPONSE_OK}


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', action='store', dest='ip', default='', help='host ip of server')
    parser.add_argument('-p', action='store', dest='port', type=int, default=DEFAULT_PORT,
                        help='listening port of server')

    args = parser.parse_args()
    # if args.port < 1023 or args.port > 65535:
    #     raise ValueError

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
                inc_msg = get_message(client_sock)
                print('Сообщение: ', inc_msg)
                resp = process_incoming_message(inc_msg)
                client_sock.send(json.dumps(resp).encode(ENCODING))


if __name__ == '__main__':
    main()
