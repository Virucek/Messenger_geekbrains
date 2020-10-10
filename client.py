import json
from socket import *
import argparse
import time
from include.variables import *


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
        msg_out = json.dumps(create_presence())
        client_sock.send(msg_out.encode(ENCODING))
        try:
            answer = client_sock.recv(MAX_PACKAGE_SIZE)
            print(answer)
        except Exception:
            pass


if __name__ == '__main__':
    main()
