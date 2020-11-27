""" Серверный скрипт """
import argparse
import binascii
import hmac
import json
import os
import threading
import time
from select import select
from socket import socket, AF_INET, SOCK_STREAM
import sys

import tabulate
from PyQt5.QtCore import QTimer, QThread
from PyQt5.QtWidgets import QApplication

import server_database
from add_user import RegisterUser
from include import protocol
from include.decorators import log, Log
from include.descriptors import Port, IpAddress
from include.protocol import AUTHENTICATE_REQUIRED_MSG
from include.utils import get_message, send_message
from include.variables import *
from log_configs.server_log_config import get_logger
from metaclasses import ServerVerifier
from server_gui import MainWindow, ConfigWindow, create_model_stat, UserStatWindow

SERVER_LOGGER = get_logger()


class Server(threading.Thread, metaclass=ServerVerifier):
    port = Port()
    ip = IpAddress()

    def __init__(self, listen_ip, listen_port, database, timeout=0.1):
        self.ip = listen_ip
        self.port = listen_port

        self.database = database

        self.timeout = timeout

        self.socket = socket(AF_INET, SOCK_STREAM)

        self.clients = []
        self.messages = []
        self.client_names = {}
        super().__init__()

    def init_socket(self):
        try:
            self.socket.bind((self.ip, self.port))
            self.socket.settimeout(self.timeout)
            self.socket.listen(MAX_CONNECTIONS)
        except OSError as e:
            SERVER_LOGGER.critical(e)
            sys.exit(1)
        else:
            SERVER_LOGGER.info(f'Запущен сервер на порту: {self.port} {self.ip if self.ip else "ANY"}')
            print(f'Запущен сервер на порту: {self.port}!')

    def run(self):
        self.init_socket()
        while True:
            try:
                client_sock, addr = self.socket.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Входящее подключение с адреса: {addr}')
                self.clients.append(client_sock)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []

            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if recv_data_lst:
                for client in recv_data_lst:
                    try:
                        inc_msg = get_message(client)
                        SERVER_LOGGER.debug('Получено сообщение:'
                                            f'{inc_msg}')
                        resp_code = self.process_incoming_message(inc_msg, client)
                        if resp_code is not None:
                            resp_msg = create_response(resp_code)
                            SERVER_LOGGER.info('Отправлен ответ:'
                                               f'{resp_msg}')
                            send_message(client, resp_msg)

                    except ValueError as e:
                        _error = f'Ошибка декодирования сообщения от клиента {e}'
                        SERVER_LOGGER.error(_error)
                        send_message(client, create_response(RESPCODE_SERVER_ERROR, _error))
                    except Exception as e:
                        SERVER_LOGGER.error(f'Клиент {client.getpeername()} отключился! {e}')
                        print(e)
                        self.clients.remove(client)

            if send_data_lst and self.messages:
                for msg in self.messages:
                    try:
                        self.process_message(msg, send_data_lst)
                    except Exception as e:
                        SERVER_LOGGER.info(f'Обработка сообщения прошла неуспешно! {e}')
                self.messages.clear()

    @log
    def process_message(self, msg, conn_socks, add_contact=1):
        msg_body = msg[1]
        if TO in msg_body:
            if msg_body[TO] in self.client_names:
                if self.client_names[msg_body[TO]] in conn_socks:
                    try:
                        send_message(self.client_names[msg_body[TO]], msg_body)
                        SERVER_LOGGER.debug(f'Сообщение {msg_body} было успешно отправлено юзеру {msg_body[TO]}')
                        if msg_body[FROM] != 'system':
                            self.database.process_message(msg_body[FROM], msg_body[TO])
                        if add_contact:
                            self.database.add_user_contact(msg_body[FROM], msg_body[TO])
                            self.database.add_user_contact(msg_body[TO], msg_body[FROM])
                        return
                    except Exception: # todo: При внезапном разрыве соединения, новым клиентам не удается подключиться
                        SERVER_LOGGER.error(f'Клиент отключился')
                        del self.client_names[msg_body[TO]]
                else: # todo: При внезапном разрыве соединения, новым клиентам не удается подключиться и не чистится имя
                    SERVER_LOGGER.error(f'Соединение с {self.client_names[msg_body[TO]].getpeername()} разорвано!')
                    self.clients.remove(self.client_names[msg_body[TO]])
                    self.database.user_logout(msg_body[TO])
                    del self.client_names[msg_body[TO]]
            else:
                SERVER_LOGGER.error(f'пользователь {msg_body[TO]} не зарегистрирован в чате')
                return
        else:
            for name in self.client_names.keys():
                if msg[1][FROM] == name:
                    continue
                msg[1][TO] = name
                self.process_message(msg, conn_socks, add_contact=0)
            return

    @log
    def create_echo_message(self):
        echo_message = protocol.CHAT_MSG_CLIENT.copy()
        echo_message[TIME] = self.messages[0][1][TIME]
        echo_message[FROM] = self.messages[0][1][FROM]
        echo_message[MESSAGE] = self.messages[0][1][MESSAGE]
        return echo_message

    @log
    def process_incoming_message(self, msg, client=None):
        if ACTION in msg:
            if msg[ACTION] == PRESENCE:
                if msg.keys() != protocol.PRESENCE_MSG_CLIENT.keys():
                    SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                    return RESPCODE_BAD_REQ
                if msg[USER].keys() != protocol.PRESENCE_MSG_CLIENT[USER].keys():
                    SERVER_LOGGER.error(f'В запросе неверный объект {USER}!')
                    return RESPCODE_BAD_REQ
                SERVER_LOGGER.debug(f'Сообщение {PRESENCE} корректное. Проверка пользователя')
                return self.preauthorize_user(msg[USER][ACCOUNT_NAME], client, msg[USER][PUBLIC_KEY])

            elif msg[ACTION] == GET_PUBLIC_KEY:
                if msg.keys() != protocol.GET_PUBKEY_REQ_MSG.keys():
                    SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                    return RESPCODE_BAD_REQ
                SERVER_LOGGER.debug(f'Сообщение {GET_PUBLIC_KEY} корректное')
                pubkey = self.database.get_pubkey(msg[USER])
                if pubkey:
                    send_message(client, create_pubkey_message(pubkey))
                else:
                    send_message(client, create_response(RESPCODE_BAD_REQ, \
                                                         f'Публичный ключ для пользователя {msg[USER]} не найден'))
                return

            elif msg[ACTION] == MSG:
                if msg.keys() != protocol.CHAT_MSG_CLIENT.keys():
                    if msg.keys() != protocol.CHAT_USER_MSG_CLIENT.keys():
                        SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                        print(protocol.CHAT_MSG_CLIENT.keys())
                        return RESPCODE_BAD_REQ
                SERVER_LOGGER.debug(f'Сообщение {MSG} корректное')
                self.messages.append((msg[FROM], msg))
                return

            elif msg[ACTION] == GET_USERS:
                if msg.keys() != protocol.GET_USERS_MSG.keys():
                    SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                    return RESPCODE_BAD_REQ
                SERVER_LOGGER.debug(f'Сообщение {GET_USERS} корректное')
                users = self.database.users_list()
                send_message(client, create_users_contacts_message(users))
                return

            elif msg[ACTION] == GET_CONTACTS:
                if msg.keys() != protocol.GET_USER_CONTACTS_MSG.keys():
                    SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                    return RESPCODE_BAD_REQ
                SERVER_LOGGER.debug(f'Сообщение {GET_CONTACTS} корректное')
                contacts = self.database.get_user_contact_list(msg[USER_LOGIN])
                send_message(client, create_users_contacts_message(contacts))
                return

            elif msg[ACTION] == ADD_CONTACT:
                if msg.keys() != protocol.ADD_USER_CONTACT_MSG.keys():
                    SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                    return RESPCODE_BAD_REQ
                self.database.add_user_contact(msg[USER_LOGIN], msg[USER_ID])
                SERVER_LOGGER.debug(f'Сообщение {ADD_CONTACT} корректное')
                return RESPCODE_OK

            elif msg[ACTION] == REMOVE_CONTACT:
                if msg.keys() != protocol.REMOVE_USER_CONTACT_MSG.keys():
                    SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                    return RESPCODE_BAD_REQ
                self.database.remove_user_contact(msg[USER_LOGIN], msg[USER_ID])
                SERVER_LOGGER.debug(f'Сообщение {REMOVE_CONTACT} корректное')
                return RESPCODE_OK

            elif msg[ACTION] == EXIT:
                SERVER_LOGGER.debug(f'Клиент {msg[FROM]} покинул чатик')
                # self.messages.append(('', create_logout_message(msg[FROM])))
                self.database.user_logout(msg[FROM])
                del self.client_names[msg[FROM]]
                return

            else:
                SERVER_LOGGER.error(f'Такое значение {ACTION} {msg[ACTION]} не поддерживается!')
                return RESPCODE_BAD_REQ

        else:
            SERVER_LOGGER.error(f'{ACTION} отсутствует в сообщении')
            return RESPCODE_BAD_REQ

    @Log()
    def preauthorize_user(self, name, client_socket, pubkey):
        if name in self.client_names.keys():
            SERVER_LOGGER.error('Имя пользователя уже занято')
            response = protocol.SERVER_RESPONSE_BAD_REQUEST
            response[ALERT] = 'Имя пользователя уже занято'
            send_message(client_socket, response)
            self.clients.remove(client_socket)
            client_socket.close()
            return

        elif not self.database.check_user(name):
            SERVER_LOGGER.error('Пользователь не зарегистрирован')
            response = protocol.SERVER_RESPONSE_BAD_REQUEST
            response[ALERT] = 'Пользователь не зарегистрирован'
            send_message(client_socket, response)
            self.clients.remove(client_socket)
            client_socket.close()
            return

        message = AUTHENTICATE_REQUIRED_MSG
        rand_msg = binascii.hexlify(os.urandom(64))
        message[DATA] = rand_msg.decode('ascii')
        print(self.database.get_passwd(name))

        hash_pwd = hmac.new(self.database.get_passwd(name), rand_msg, 'MD5')
        print(hash_pwd)
        digest = hash_pwd.digest()
        print(digest)
        send_message(client_socket, message)

        ans = get_message(client_socket)
        client_digest = binascii.a2b_base64(ans[USER][PASSWORD])

        if ACTION in ans and ans[ACTION] == AUTHENTICATE:
            print(1111111111111)
            if hmac.compare_digest(digest, client_digest):
                print(333333333333333)
                SERVER_LOGGER.debug(f'Ответ на {PRESENCE} корректный')
                # self.messages.append(('', create_login_message(msg[USER][ACCOUNT_NAME])))
                self.client_names[name] = client_socket
                cli_ip, cli_port = client_socket.getpeername()
                self.database.user_login(name, cli_ip, cli_port, pubkey)
                return RESPCODE_OK
            else:
                print(22222222222222)
                SERVER_LOGGER.error('Пароль не верен')
                response = protocol.SERVER_RESPONSE_BAD_REQUEST
                response[ALERT] = 'Пароль не верен'
                send_message(client_socket, response)
                self.clients.remove(client_socket)
                client_socket.close()
                return
        else:
            print(444444444444444)
            SERVER_LOGGER.error('Некорректный запрос на аутентификацию!')
            response = protocol.SERVER_RESPONSE_BAD_REQUEST
            response[ALERT] = 'Некорректный запрос на аутентификацию!'
            send_message(client_socket, response)
            self.clients.remove(client_socket)
            client_socket.close()
            return

@log
def create_response(resp_code, _error=None):
    if resp_code == RESPCODE_OK:
        SERVER_LOGGER.debug(f'Сформирован {RESPCODE_OK} ответ')
        return protocol.SERVER_RESPONSE_OK
    elif resp_code == RESPCODE_BAD_REQ:
        SERVER_LOGGER.error(f'Сформирован BAD REQUEST {RESPCODE_BAD_REQ} ответ')
        response = protocol.SERVER_RESPONSE_BAD_REQUEST.copy()
        if _error is not None:
            response[ALERT] = _error
        return response
    else:
        response = protocol.SERVER_RESPONSE_SERVER_ERROR
        SERVER_LOGGER.error(f'Сформирован SERVER ERROR {RESPCODE_SERVER_ERROR} ответ')
        if _error is not None:
            response.update({'error': _error})
        return response


@log
def create_login_message(user_name):
    login_msg = protocol.CHAT_MSG_CLIENT.copy()
    print(f'create_login - {protocol.CHAT_MSG_CLIENT.keys()}')
    login_msg[TIME] = time.time()
    login_msg[FROM] = 'system'
    login_msg[MESSAGE] = f'{user_name} врывается на сервер!'
    return login_msg


@log
def create_logout_message(user_name):
    logout_msg = protocol.CHAT_MSG_CLIENT.copy()
    logout_msg[TIME] = time.time()
    logout_msg[FROM] = 'system'
    logout_msg[MESSAGE] = f'{user_name} уходит из чатика!'
    return logout_msg


@log
def create_users_contacts_message(users):
    users_contacts_msg = protocol.RESPONSE_USERS_CONTACTS_MSG.copy()
    users_contacts_msg[ALERT] = users
    return users_contacts_msg


@Log()
def create_pubkey_message(pubkey):
    pubkey_msg = protocol.PUBKEY_RESP.copy()
    pubkey_msg[KEY] = pubkey
    return pubkey_msg


def print_help():
    command_dict = [
        (EXIT, 'выход из приложения'),
        (USERS, 'вывести список всех пользователей'),
        (ACTIVE, 'вывести список пользователей онлайн'),
        (HISTORY, 'запросить историю входа пользователей'),
        (HELP, 'запросить справку по командам'),
    ]

    print(tabulate.tabulate(command_dict, headers=['Команда', 'Функция']))


def main():

    # parser = argparse.ArgumentParser()
    # parser.add_argument('-a', action='store', dest='ip', default='', help='host ip of server')
    # parser.add_argument('-p', action='store', dest='port', type=int, default=DEFAULT_PORT,
    #                     help='listening port of server')
    #
    # args = parser.parse_args()

    # server_app = QApplication(sys.argv)

    def server_config(first_launch=False):
        global config_window
        config_window = ConfigWindow(first_launch)
        config_window.db_file.insert(SERVER_DATABASE)
        config_window.port.insert(str(DEFAULT_PORT))
        if first_launch:
            config_window.run_button.clicked.connect(run_server)

    def run_server():
        global config_window
        port = int(config_window.port.text())
        ip = config_window.ip.text()
        db_file = config_window.db_file.text()
        db_path = config_window.db_path.text()
        if db_path:
            database_file = os.path.join(db_path, db_file)
        else:
            database_file = db_file

        database = server_database.ServerStorage(database_file)

        # server = Server(args.ip, args.port, database=database)
        server = Server(ip, port, database=database)
        server.daemon = True
        server.start()

        config_window.close()
        # Создание GUI главного окна:
        global main_window
        main_window = MainWindow(database)

        def show_user_stat():
            global stat_window
            stat_window = UserStatWindow()
            stat_window.user_stat_table.setModel(create_model_stat(database))
            stat_window.user_stat_table.resizeColumnsToContents()
            stat_window.user_stat_table.resizeRowsToContents()

        def show_reg_user():
            global add_user_window
            add_user_window = RegisterUser(database, server)

        main_window.statusBar().showMessage(f'Server is working; port = {port}')
        main_window.configAction.triggered.connect(server_config)
        main_window.statAction.triggered.connect(show_user_stat)
        main_window.addUserAction.triggered.connect(show_reg_user)

        main_window.refresh_button.clicked.connect(main_window.create_active_users_model)

    server_app = QApplication(sys.argv)
    server_config(first_launch=True)
    sys.exit(server_app.exec_())

    # print_help()
    # # Основной цикл сервера:
    # while True:
    #     command = input('Введите комманду: ').lower()
    #     if command == HELP:
    #         print_help()
    #     elif command == EXIT:
    #         break
    #     elif command == USERS:
    #         print(f'Список всех пользователей')
    #         for user in database.users_list():
    #             print(f'{user.id}: {user.name}')
    #     elif command == ACTIVE:
    #         print(f'Список активных пользователей')
    #         for user in database.active_users_list():
    #             print(f'Пользователь {user[0]}, адрес:порт - {user[1]}:{user[2]}, время входа: {user[3]}')
    #     elif command == HISTORY:
    #         name = input('Введите имя пользователя для вывода его истории входа или оставьте строку пустой для вывода '
    #                      'всех: ')
    #         for user in database.login_history(name):
    #             if user[2]:
    #                 print(f'Пользователь: {user[0]}, время входа: {user[1]}, время выхода: {user[2]}. '
    #                       f'Адрес:порт - {user[3]}:{user[4]}')
    #             else:
    #                 print(f'Пользователь: {user[0]}, время входа: {user[1]}. '
    #                       f'Адрес:порт - {user[3]}:{user[4]}')
    #     else:
    #         print(f'Команда не верна, чтобы посмотреть список поддерживаемых команд - введите {HELP}')


if __name__ == '__main__':
    main()
