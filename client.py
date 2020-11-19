""" Клиентский скрипт """
import sys
import threading
from socket import *
import argparse
import time

from client_database import ClientStorage
from include import protocol
from include.decorators import Log
from include.utils import get_message, send_message
from include.variables import *
from log_configs.client_log_config import get_logger
from metaclasses import ClientVerifier

CLIENT_LOGGER = get_logger()


class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class ClientSender(threading.Thread, metaclass=ClientVerifier):

    def __init__(self, user_name, client_socket, database):
        self.user_name = user_name
        self.socket = client_socket
        self.database = database
        super(ClientSender, self).__init__()
        CLIENT_LOGGER.debug(f'Отправитель клиент {self.user_name} запущен!')

    @Log()
    def create_message(self):
        time.sleep(0.5)
        user_to = input(
            f'Кому хотите отправить ({HELP_F} для команд): ')
        if user_to in CLIENT_COMMANDS:
            return user_to
        message = input(f'Сообщение ({HELP_F} для команд):')
        if message in CLIENT_COMMANDS:
            return message
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

    @Log()
    def create_add_contact_msg(self, user_contact):
        msg = protocol.ADD_USER_CONTACT_MSG.copy()
        msg[USER_ID] = user_contact
        msg[TIME] = time.time()
        msg[USER_LOGIN] = self.user_name
        CLIENT_LOGGER.debug(f'Сформировано {ADD_CONTACT} сообщение:\n{msg}')
        return msg

    @Log()
    def create_remove_contact_msg(self, user_contact):
        msg = protocol.REMOVE_USER_CONTACT_MSG.copy()
        msg[USER_ID] = user_contact
        msg[TIME] = time.time()
        msg[USER_LOGIN] = self.user_name
        CLIENT_LOGGER.debug(f'Сформировано {REMOVE_CONTACT} сообщение:\n{msg}')
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
                elif message == HELP_F:
                    show_help()
                    continue
                elif message == ADD_CONTACT_F:
                    user_contact = input("Введите имя пользователя для добавления в список контактов: ")
                    message = self.create_add_contact_msg(user_contact)
                    self.database.add_contact(user_contact)
                elif message == REMOVE_CONTACT_F:
                    user_contact = input("Введите имя пользователя, кого хотите удалить из контактов: ")
                    message = self.create_remove_contact_msg(user_contact)
                    self.database.remove_contact(user_contact)
                elif message == GET_CONTACTS_F:
                    print([contact for contact in self.database.get_contacts()])
                    continue
                elif message == GET_USERS_F:
                    print([contact for contact in self.database.get_known_users()])
                    continue
                # elif message == REFRESH_F: todo: реализовать обноввление списка пользователей по требованию
                #     load_database(self.socket, self.database, self.user_name)
                #     print("База контактов и пользователей успешно обновлена!")
                #     CLIENT_LOGGER.debug("База контактов и пользователей успешно обновлена!")
                #     continue
                else:
                    if TO in message:
                        self.database.save_outgoing_message(message[TO], message[MESSAGE])
                send_message(self.socket, message)
            except:
                CLIENT_LOGGER.error(f'соединение с сервером разорвано')
                sys.exit(1)


class ClientReceiver(threading.Thread, metaclass=ClientVerifier):
    
    def __init__(self, user_name, client_socket, database):
        self.user_name = user_name
        self.socket = client_socket
        self.database = database
        super(ClientReceiver, self).__init__()
        CLIENT_LOGGER.debug(f'Получатель клиент {self.user_name} запущен!')
    
    #@Log() todo: разобраться, как disassembling с Log подружить
    def run(self):
        while True:
            try:
                process_incoming_message(get_message(self.socket), self.database)
            except Exception as e:
                CLIENT_LOGGER.error(f'Соединение с сервером разорвано@!!!!!!!\n {e}')
                sys.exit(1)


@Log()
def process_incoming_message(message, database=None):
    if RESPONSE in message:
        if message[RESPONSE] == RESPCODE_OK:
            CLIENT_LOGGER.debug(f'Полученный ответ от сервера: {message[RESPONSE]}')
            return True
        elif message[RESPONSE] == RESPCODE_ACCEPTED:
            CLIENT_LOGGER.debug(f'Полученный ответ от сервера: {message[RESPONSE]}')
            if ALERT in message:
                CLIENT_LOGGER.debug(f'Получен корректный ответ от сервера: {message[RESPONSE]}')
                return True
        CLIENT_LOGGER.debug('Сервер ответил ошибкой')
        if ALERT in message:
            CLIENT_LOGGER.debug(message[ALERT])
            print(message[ALERT])
        raise ServerError(f'Некорректный ответ от сервера:\n{message}')
    elif ACTION in message:
        if message[ACTION] == MSG and MESSAGE in message:
            if database:
                database.save_incoming_message(message[FROM], message[MESSAGE])
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


@Log()
def get_contacts_msg(user_name=NOT_LOGGED_USER):
    msg = protocol.GET_USER_CONTACTS_MSG
    msg[TIME] = time.time()
    msg[USER_LOGIN] = user_name
    CLIENT_LOGGER.debug(f'Сформировано {GET_CONTACTS} сообщение:\n{msg}')
    return msg


@Log()
def get_users_msg(user_name=NOT_LOGGED_USER):
    msg = protocol.GET_USERS_MSG
    msg[TIME] = time.time()
    msg[USER_LOGIN] = user_name
    CLIENT_LOGGER.debug(f'Сформировано {GET_USERS} сообщение:\n{msg}')
    return msg


def show_help():
    print(f'Чтобы отправить сообщение всем пользователям - поле получателя оставьте пустым\n'
          f'Чтобы добавить пользователя в список контактов - введите {ADD_CONTACT_F}\n'
          f'Чтобы убрать пользователя из списка контактов - введите {REMOVE_CONTACT_F}\n'
          f'Чтобы вывести список контактов - введите {GET_CONTACTS_F}\n'
          f'Чтобы вывести список всех известных пользователей - введите {GET_USERS_F}\n'
          f'Чтобы выйти из чата - введите {EXIT_F}')


@Log()
def get_response_safe(client_socket):
    try:
        answer = get_message(client_socket)
        CLIENT_LOGGER.info(f'Получено сообщение от сервера: {answer}')
        process_incoming_message(answer)
        return answer
    except ServerError as err:
        CLIENT_LOGGER.error(err)
    except ValueError:
        CLIENT_LOGGER.error('Ошибка декодирования сообщения от сервера')
    return False


def load_database(client_socket, database, user_name):
    send_message(client_socket, get_users_msg(user_name))
    CLIENT_LOGGER.info(f'Отправлено get_users сообщение')
    answer = get_response_safe(client_socket)
    if answer is not False:
        database.load_known_users(answer[ALERT])

    send_message(client_socket, get_contacts_msg(user_name))
    CLIENT_LOGGER.info(f'Отправлено get_contacts сообщение')
    answer = get_response_safe(client_socket)
    if answer is not False:
        for contact in answer[ALERT]:
            database.add_contact(contact)


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
        CLIENT_LOGGER.info(f'Отправлено presence сообщение')
        if get_response_safe(client_sock) is not False:
            get_response_safe(client_sock)
            db_url = f'sqlite:///client_{user_name}.db3'
            database = ClientStorage(db_url)
            load_database(client_sock, database, user_name)

            write_client = ClientSender(user_name, client_sock, database)
            write_client.daemon = True
            write_client.start()
            read_client = ClientReceiver(user_name, client_sock, database)
            read_client.daemon = True
            read_client.start()
            while True:
                time.sleep(0.5)
                if write_client.is_alive() and read_client.is_alive():
                    continue
                break


if __name__ == '__main__':
    main()
