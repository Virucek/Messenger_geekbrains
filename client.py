""" Клиентский скрипт """
import sys
import threading
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
        if ALERT in message:
            CLIENT_LOGGER.debug(message[ALERT])
            print(message[ALERT])
        return False
    elif ACTION in message:
        if message[ACTION] == MSG and MESSAGE in message:
            print(f'\n{message[FROM]} > {message[MESSAGE]}')
            return True
    raise ValueError


@Log()
def create_message(user_name):
    time.sleep(0.5)
    user_to = input(f'Кому хотите отправить (оставьте пустым, чтобы отправить всем, введите {EXIT_F}, чтобы выйти): ')
    if user_to == EXIT_F:
        return EXIT_F
    message = input(f'Сообщение ({EXIT_F}, чтобы выйти):')
    if message == EXIT_F:
        return EXIT_F
    message_full = protocol.CHAT_MSG_CLIENT.copy()
    message_full[TIME] = time.time()
    message_full[FROM] = user_name
    if user_to:
        message_full[TO] = user_to
    message_full[MESSAGE] = message
    CLIENT_LOGGER.debug(f'Сформировано сообщение:\n{message_full}')
    return message_full


@Log()
def create_exit_message(user_name):
    msg = protocol.EXIT_MSG_CLIENT
    msg[TIME] = time.time()
    msg[FROM] = user_name
    CLIENT_LOGGER.debug(f'Сформировано EXIT сообщение:\n{msg}')
    return msg


@Log()
def create_presence(user_name):
    msg = protocol.PRESENCE_MSG_CLIENT
    msg[TIME] = time.time()
    msg[USER][ACCOUNT_NAME] = user_name
    msg[USER][STATUS] = 'Presense status test?'
    CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение:\n{msg}')
    return msg


@Log()
def write_to_socket(client_sock, user_name):
    while True:
        try:
            message = create_message(user_name)
            if message == EXIT_F:
                CLIENT_LOGGER.debug('Клиент выходит из чатика')
                send_message(client_sock, create_exit_message(user_name))
                time.sleep(2)
                break
            send_message(client_sock, message)
        except:
            CLIENT_LOGGER.error(f'соединение с сервером разорвано')
            sys.exit(1)


@Log()
def read_from_socket(client_sock):
    while True:
        try:
            process_incoming_message(get_message(client_sock))
        except Exception as e:
            CLIENT_LOGGER.error(f'Соединение с сервером разорвано@!!!!!!!\n {e}')
            sys.exit(1)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('host', nargs='?', default=DEFAULT_HOST, help='server host ip address')
    parser.add_argument('port', nargs='?', default=DEFAULT_PORT, type=int, help='server port')
    parser.add_argument('-u', action='store', dest='user_name', help='mode of work')

    args = parser.parse_args()

    if not args.user_name:
        user_name = input(f'Введите имя пользователя:')
    else:
        user_name = args.user_name

    with socket(AF_INET, SOCK_STREAM) as client_sock:
        try:
            client_sock.connect((args.host, args.port))
            CLIENT_LOGGER.info(f'Исходящее подключение к серверу: {args.host}:{args.port}')
        except OSError as e:
            CLIENT_LOGGER.critical(e)
            sys.exit(1)

        send_message(client_sock, create_presence(user_name))
        CLIENT_LOGGER.info(f'Отправлено сообщение')
        try:
            answer = get_message(client_sock)
            CLIENT_LOGGER.info(f'Получено сообщение от сервера: {answer}')
            process_incoming_message(answer)
        except ValueError:
            CLIENT_LOGGER.error('Ошибка декодирования сообщения от сервера')

        write_thread = threading.Thread(target=write_to_socket, args=(client_sock, user_name), daemon=True)
        write_thread.start()
        read_thread = threading.Thread(target=read_from_socket, args=(client_sock,), daemon=True)
        read_thread.start()

        while True:
            time.sleep(0.5)
            if write_thread.is_alive() and read_thread.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
