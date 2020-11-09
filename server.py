""" Серверный скрипт """
import argparse
import time
from select import select
from socket import socket, AF_INET, SOCK_STREAM
import sys

from include import protocol
from include.decorators import log
from include.descriptors import Port, IpAddress
from include.utils import get_message, send_message
from include.variables import *
from log_configs.server_log_config import get_logger
from metaclasses import ServerVerifier

SERVER_LOGGER = get_logger()


class Server(metaclass=ServerVerifier):
    port = Port()
    ip = IpAddress()

    def __init__(self, listen_ip, listen_port, timeout=0.1):
        self.ip = listen_ip
        self.port = listen_port
        self.timeout = timeout

        self.socket = socket(AF_INET, SOCK_STREAM)

        self.clients = []
        self.messages = []
        self.client_names = {}

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

    def main_run(self):
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
                    except ValueError:
                        _error = 'Ошибка декодирования сообщения от клиента'
                        SERVER_LOGGER.error(_error)
                        send_message(client, create_response(RESPCODE_SERVER_ERROR, _error))
                    except:
                        SERVER_LOGGER.error(f'Клиент {client.getpeername()} отключился')
                        self.clients.remove(client)

            if send_data_lst and self.messages:
                for msg in self.messages:
                    try:
                        self.process_message(msg, send_data_lst)
                    except Exception as e:
                        SERVER_LOGGER.info(f'Обработка сообщения прошла неуспешно! {e}')
                self.messages.clear()

    @log
    def process_message(self, msg, conn_socks):
        msg_body = msg[1]
        if TO in msg_body:
            if msg_body[TO] in self.client_names:
                if self.client_names[msg_body[TO]] in conn_socks:
                    try:
                        send_message(self.client_names[msg_body[TO]], msg_body)
                        SERVER_LOGGER.debug(f'Сообщение {msg_body} было успешно отправлено юзеру {msg_body[TO]}')
                        return
                    except Exception:
                        SERVER_LOGGER.error(f'Клиент отключился')
                        del self.client_names[msg_body[TO]]
                else:
                    SERVER_LOGGER.error(f'Соединение с {self.client_names[msg_body[TO]].getpeername()} разорвано!')
                    self.clients.remove(self.client_names[msg_body[TO]])
                    del self.client_names[msg_body[TO]]
            else:
                SERVER_LOGGER.error(f'пользователь {msg_body[TO]} не зарегистрирован в чате')
                return
        else:
            for name in self.client_names.keys():
                if msg[1][FROM] == name:
                    continue
                msg[1][TO] = name
                self.process_message(msg, conn_socks)
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

                if msg[USER][ACCOUNT_NAME] in self.client_names.keys():
                    SERVER_LOGGER.error('Имя пользователя уже занято')
                    response = protocol.SERVER_RESPONSE_BAD_REQUEST
                    response[ALERT] = 'Имя пользователя уже занято'
                    send_message(client, response)
                    self.clients.remove(client)
                    client.close()
                    return
                SERVER_LOGGER.debug(f'Ответ на {PRESENCE} корректный')
                self.messages.append(('', create_login_message(msg[USER][ACCOUNT_NAME])))
                self.client_names[msg[USER][ACCOUNT_NAME]] = client
                return RESPCODE_OK
            elif msg[ACTION] == MSG:
                if msg.keys() != protocol.CHAT_MSG_CLIENT.keys():
                    if msg.keys() != protocol.CHAT_USER_MSG_CLIENT.keys():
                        SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                        print(protocol.CHAT_MSG_CLIENT.keys())
                        return RESPCODE_BAD_REQ
                SERVER_LOGGER.debug(f'Сообщение {MSG} корректное')
                self.messages.append((msg[FROM], msg))
                return
            elif msg[ACTION] == EXIT:
                SERVER_LOGGER.debug(f'Клиент {msg[FROM]} покинул чатик')
                self.messages.append(('', create_logout_message(msg[FROM])))
                del self.client_names[msg[FROM]]
                return
            SERVER_LOGGER.error(f'Такое значение {ACTION} {msg[ACTION]} не поддерживается!')
            return RESPCODE_BAD_REQ
        SERVER_LOGGER.error(f'{ACTION} отсутствует в сообщении')
        return RESPCODE_BAD_REQ


@log
def create_response(resp_code, _error=None):
    if resp_code == RESPCODE_OK:
        SERVER_LOGGER.debug(f'Сформирован {RESPCODE_OK} ответ')
        return protocol.SERVER_RESPONSE_OK
    elif resp_code == RESPCODE_BAD_REQ:
        SERVER_LOGGER.error(f'Сформирован BAD REQUEST {RESPCODE_BAD_REQ} ответ')
        return protocol.SERVER_RESPONSE_BAD_REQUEST
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', action='store', dest='ip', default='', help='host ip of server')
    parser.add_argument('-p', action='store', dest='port', type=int, default=DEFAULT_PORT,
                        help='listening port of server')

    args = parser.parse_args()

    server = Server(args.ip, args.port)
    server.main_run()


if __name__ == '__main__':
    main()
