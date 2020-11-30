""" Серверный главный класс """
import binascii
import hmac
import os
import threading
import time
from select import select
from socket import socket, AF_INET, SOCK_STREAM
import sys

from include import protocol
from include.decorators import log, Log
from include.descriptors import Port, IpAddress
from include.protocol import AUTHENTICATE_REQUIRED_MSG
from include.utils import get_message, send_message
from include.variables import *
from log_configs.server_log_config import get_logger


SERVER_LOGGER = get_logger()


class Server(threading.Thread): #, metaclass=ServerVerifier): - не работает докстринг!!!
    """
    Класс клиента.
    Отвечает за взаимодействие с сервером: отправляет и принимает сообщения от сервера.
    Сохраняет данный в БД, загружает данные из БД
    """
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

    def __init_socket(self):
        """Метод инициализации сокета"""
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
        """Основной цикл работы Сервера"""
        self.__init_socket()
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
        """Обработка сообщения. Отправка его адресату, если адресата нет - отправка всем активным клиентам."""
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
                    except:
                        # todo: При внезапном разрыве соединения, новым клиентам не удается подключиться
                        SERVER_LOGGER.error(f'Клиент отключился')
                        del self.client_names[msg_body[TO]]
                else:
                    # todo: При внезапном разрыве соединения, новым клиентам не удается подключиться и не чистится имя
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
        """Метод создания эхо-сообщения"""
        echo_message = protocol.CHAT_MSG_CLIENT.copy()
        echo_message[TIME] = self.messages[0][1][TIME]
        echo_message[FROM] = self.messages[0][1][FROM]
        echo_message[MESSAGE] = self.messages[0][1][MESSAGE]
        return echo_message

    @log
    def process_incoming_message(self, msg, client=None):
        """Метод обработки входящего сообщения"""
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
                    send_message(client, create_response(RESPCODE_BAD_REQ,
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
        """Метод для предавторизации пользователя"""
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
            if hmac.compare_digest(digest, client_digest):
                SERVER_LOGGER.debug(f'Ответ на {PRESENCE} корректный')
                # self.messages.append(('', create_login_message(msg[USER][ACCOUNT_NAME])))
                self.client_names[name] = client_socket
                cli_ip, cli_port = client_socket.getpeername()
                self.database.user_login(name, cli_ip, cli_port, pubkey)
                return RESPCODE_OK
            else:
                SERVER_LOGGER.error('Пароль не верен')
                response = protocol.SERVER_RESPONSE_BAD_REQUEST
                response[ALERT] = 'Пароль не верен'
                send_message(client_socket, response)
                self.clients.remove(client_socket)
                client_socket.close()
                return
        else:
            SERVER_LOGGER.error('Некорректный запрос на аутентификацию!')
            response = protocol.SERVER_RESPONSE_BAD_REQUEST
            response[ALERT] = 'Некорректный запрос на аутентификацию!'
            send_message(client_socket, response)
            self.clients.remove(client_socket)
            client_socket.close()
            return

@log
def create_response(resp_code, _error=None):
    """Функция создания типового ответа от сервера"""
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
    """Функция создания увдомления, когда пользователь входит в чат (не используется сейчас)"""
    login_msg = protocol.CHAT_MSG_CLIENT.copy()
    print(f'create_login - {protocol.CHAT_MSG_CLIENT.keys()}')
    login_msg[TIME] = time.time()
    login_msg[FROM] = 'system'
    login_msg[MESSAGE] = f'{user_name} врывается на сервер!'
    return login_msg


@log
def create_logout_message(user_name):
    """Функция создания увдомления, когда пользователь выходит из чата (не используется сейчас)"""
    logout_msg = protocol.CHAT_MSG_CLIENT.copy()
    logout_msg[TIME] = time.time()
    logout_msg[FROM] = 'system'
    logout_msg[MESSAGE] = f'{user_name} уходит из чатика!'
    return logout_msg


@log
def create_users_contacts_message(users):
    """Функция по созданию сообщения, в котором возвращаются либо список пользователей, либо контактов"""
    users_contacts_msg = protocol.RESPONSE_USERS_CONTACTS_MSG.copy()
    users_contacts_msg[ALERT] = users
    return users_contacts_msg


@Log()
def create_pubkey_message(pubkey):
    """Функция создания ответа для возвращения публичного ключа клиента"""
    pubkey_msg = protocol.PUBKEY_RESP.copy()
    pubkey_msg[KEY] = pubkey
    return pubkey_msg
