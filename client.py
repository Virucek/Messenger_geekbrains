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
from metaclasses import ClientVerifier

CLIENT_LOGGER = get_logger()


class ClientSender(threading.Thread, metaclass=ClientVerifier):

    def __init__(self, user_name, client_socket):
        self.user_name = user_name
        self.socket = client_socket
        super(ClientSender, self).__init__()
        CLIENT_LOGGER.debug(f'Отправитель клиент {self.user_name} запущен!')

    @Log()
    def create_message(self):
        time.sleep(0.5)
        user_to = input(
            f'Кому хотите отправить (оставьте пустым, чтобы отправить всем, введите {EXIT_F}, чтобы выйти): ')
        if user_to == EXIT_F:
            return EXIT_F
        message = input(f'Сообщение ({EXIT_F}, чтобы выйти):')
        if message == EXIT_F:
            return EXIT_F
        message_full = protocol.CHAT_MSG_CLIENT.copy()
        message_full[TIME] = time.time()
        message_full[FROM] = self.user_name
        if user_to:
            message_full[TO] = user_to
        message_full[MESSAGE] = message
        CLIENT_LOGGER.debug(f'Сформировано сообщение:\n{message_full}')
        return message_full

    @Log()
    def create_exit_message(self):
        msg = protocol.EXIT_MSG_CLIENT
        msg[TIME] = time.time()
        msg[FROM] = self.user_name
        CLIENT_LOGGER.debug(f'Сформировано EXIT сообщение:\n{msg}')
        return msg

    #@Log() todo: разобраться, как disassembling с Log подружить
    def run(self):
        while True:
            try:
                message = self.create_message()
                if message == EXIT_F:
                    CLIENT_LOGGER.debug('Клиент выходит из чатика')
                    send_message(self.socket, self.create_exit_message())
                    time.sleep(2)
                    break
                send_message(self.socket, message)
            except:
                CLIENT_LOGGER.error(f'соединение с сервером разорвано')
                sys.exit(1)


class ClientReceiver(threading.Thread, metaclass=ClientVerifier):
    
    def __init__(self, user_name, client_socket):
        self.user_name = user_name
        self.socket = client_socket
        super(ClientReceiver, self).__init__()
        CLIENT_LOGGER.debug(f'Получатель клиент {self.user_name} запущен!')
    
    #@Log() todo: разобраться, как disassembling с Log подружить
    def run(self):
        while True:
            try:
                process_incoming_message(get_message(self.socket))
            except Exception as e:
                CLIENT_LOGGER.error(f'Соединение с сервером разорвано@!!!!!!!\n {e}')
                sys.exit(1)


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
def create_presence(user_name=NOT_LOGGED_USER):
    msg = protocol.PRESENCE_MSG_CLIENT
    msg[TIME] = time.time()
    msg[USER][ACCOUNT_NAME] = user_name
    msg[USER][STATUS] = 'Presense status test?'
    CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение:\n{msg}')
    return msg


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('host', nargs='?', default=DEFAULT_HOST, help='server host ip address')
    parser.add_argument('port', nargs='?', default=DEFAULT_PORT, type=int, help='server port')
    parser.add_argument('-u', action='store', dest='user_name', help='mode of work')

    args = parser.parse_args()

    if not args.user_name:
        while True:
            user_name = input(f'Введите имя пользователя: ')
            if user_name:
                break
            else:
                print('Вы не ввели имя пользователя!')
                continue
    else:
        user_name = args.user_name

    print(f'Клиентское окно. Имя клиента - {user_name}')

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

        write_client = ClientSender(user_name, client_sock)
        write_client.daemon = True
        write_client.start()
        read_client = ClientReceiver(user_name, client_sock)
        read_client.daemon = True
        read_client.start()
        while True:
            time.sleep(0.5)
            if write_client.is_alive() and read_client.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
