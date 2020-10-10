import argparse
from socket import *
from include import variables


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', action='store', dest='ip', default='', help='host ip of server')
    parser.add_argument('-p', action='store', dest='port', type=int, default=variables.DEFAULT_PORT,
                        help='listening port of server')

    args = parser.parse_args()

    with socket(AF_INET, SOCK_STREAM) as server_sock:
        server_sock.bind((args.ip, args.port))
        server_sock.listen(variables.MAX_CONNECTIONS)

        while True:
            client_sock, addr = server_sock.accept()
            with client_sock:
                data = client_sock.recv(variables.MAX_PACKAGE_SIZE)
                print('Сообщение: ', data.decode(variables.ENCODING))
                client_sock.send('test'.encode(variables.ENCODING))


if __name__ == '__main__':
    main()
