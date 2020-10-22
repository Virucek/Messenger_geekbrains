""" Клиентский скрипт """
import sys
from socket import *
import argparse
import time

from include import protocol
from include.decorators import Log
from include.utils import get_message, send_message
from include.variables import *
from log_configs.client_log_config import get_logger

CLIENT_LOGGER = get_logger()


@Log()
def process_incoming_message(message):
    if RESPONSE in message:
        if message[RESPONSE] == RESPCODE_OK:
            CLIENT_LOGGER.debug('Полученное сообщение ОК')
            return True
        CLIENT_LOGGER.debug('Сервер ответил ошибкой')
        return False
    raise ValueError


@Log()
def create_presence():
    msg = protocol.PRESENCE_MSG_CLIENT
    msg[TIME] = time.time()
    msg[USER][STATUS] = 'Presense status test?'
    CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение:\n{msg}')
    return msg


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('host', nargs='?', default=DEFAULT_HOST, help='server host ip address')
    parser.add_argument('port', nargs='?', default=DEFAULT_PORT, type=int, help='server port')

    args = parser.parse_args()

    with socket(AF_INET, SOCK_STREAM) as client_sock:
        try:
            client_sock.connect((args.host, args.port))
            CLIENT_LOGGER.info(f'Исходящее подключение к серверу: {args.host}:{args.port}')
        except OSError as e:
            CLIENT_LOGGER.critical(e)
            sys.exit(1)

        send_message(client_sock, create_presence())
        CLIENT_LOGGER.info(f'Отправлено сообщение')
        try:
            answer = get_message(client_sock)
            CLIENT_LOGGER.info(f'Получено сообщение от сервера: {answer}')
            process_incoming_message(answer)
        except ValueError:
            CLIENT_LOGGER.error('Ошибка декодирования сообщения от сервера')


if __name__ == '__main__':
    main()
