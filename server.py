""" Серверный скрипт """
import argparse
import time
from select import select
from socket import *
import sys

from include import protocol
from include.decorators import log
from include.utils import get_message, send_message
from include.variables import *
from log_configs.server_log_config import get_logger

SERVER_LOGGER = get_logger()


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
def create_echo_message(msg_list):
    print(msg_list)
    echo_message = protocol.CHAT_MSG_CLIENT
    echo_message[TIME] = msg_list[0][1][TIME]
    echo_message[FROM] = msg_list[0][1][FROM]
    echo_message[MESSAGE] = msg_list[0][1][MESSAGE]
    return echo_message


@log
def create_login_message(user_name):
    login_msg = protocol.CHAT_MSG_CLIENT
    login_msg[TIME] = time.time()
    login_msg[FROM] = 'system'
    login_msg[MESSAGE] = f'{user_name} врывается на сервер!'
    return login_msg


@log
def create_logout_message(user_name):
    logout_msg = protocol.CHAT_MSG_CLIENT
    logout_msg[TIME] = time.time()
    logout_msg[FROM] = 'system'
    logout_msg[MESSAGE] = f'{user_name} уходит из чатика!'
    return logout_msg


@log
def process_incoming_message(msg, msg_list=[]):
    if ACTION in msg:
        if msg[ACTION] == PRESENCE:
            if msg.keys() != protocol.PRESENCE_MSG_CLIENT.keys():
                SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                return RESPCODE_BAD_REQ
            if msg[USER].keys() != protocol.PRESENCE_MSG_CLIENT[USER].keys():
                SERVER_LOGGER.error(f'В запросе неверный объект {USER}!')
                return RESPCODE_BAD_REQ
            # if msg[USER][ACCOUNT_NAME] != NOT_LOGGED_USER:
            #     SERVER_LOGGER.error(f'Некорректный пользователь для {PRESENCE} сообщения')
            #     return RESPCODE_BAD_REQ
            SERVER_LOGGER.debug(f'Сообщение {PRESENCE} корректное. Ответ успешный')

            msg_list.append(('', create_login_message(msg[USER][ACCOUNT_NAME])))
            return RESPCODE_OK
        elif msg[ACTION] == MSG:
            if msg.keys() != protocol.CHAT_MSG_CLIENT.keys():
                SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                return RESPCODE_BAD_REQ
            SERVER_LOGGER.debug(f'Сообщение {MSG} корректное')
            msg_list.append((msg[FROM], msg))
            return
        SERVER_LOGGER.error(f'Такое значение {ACTION} {msg[ACTION]} не поддерживается!')
    SERVER_LOGGER.error(f'{ACTION} отсутствует в сообщении')
    return RESPCODE_BAD_REQ


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', action='store', dest='ip', default='', help='host ip of server')
    parser.add_argument('-p', action='store', dest='port', type=int, default=DEFAULT_PORT,
                        help='listening port of server')

    args = parser.parse_args()
    # if args.port < 1024 or args.port > 65535:
    #     SERVER_LOGGER.error('порт должен быть в диапазоне 1024-65535')
    #     sys.exit(1)

    with socket(AF_INET, SOCK_STREAM) as server_sock:
        try:
            server_sock.bind((args.ip, args.port))
            server_sock.settimeout(0.1)
        except OSError as e:
            SERVER_LOGGER.critical(e)
            sys.exit(1)

        clients, messages = [], []

        server_sock.listen(MAX_CONNECTIONS)
        SERVER_LOGGER.info(f'Запущен сервер на порту: {args.port}')
        print(f'Запущен сервер на порту: {args.port}!')

        while True:
            try:
                client_sock, addr = server_sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Входящее подключение с адреса: {addr}')
                clients.append(client_sock)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []

            try:
                if clients:
                    recv_data_lst, send_data_lst, err_lst = select(clients, clients, [], 0)
            except OSError:
                pass

            if recv_data_lst:
                for client in recv_data_lst:
                    try:
                        inc_msg = get_message(client)
                        SERVER_LOGGER.debug('Получено сообщение:'
                                            f'{inc_msg}')
                        resp_code = process_incoming_message(inc_msg, messages)
                        if resp_code is not None:
                            resp_msg = create_response(resp_code)
                            SERVER_LOGGER.info('Отправлен ответ:'
                                               f'{resp_msg}')
                            send_message(client, resp_msg)
                    except ValueError:
                        _error = 'Ошибка декодирования сообщения от клиента'
                        resp_code = RESPCODE_SERVER_ERROR
                        SERVER_LOGGER.error(_error)
                        send_message(client, create_response(resp_code, _error))
                        clients.remove(client)
                    except:
                        SERVER_LOGGER.error(f'Клиент {client.getpeername()} отключился')
                        clients.remove(client)

            if messages and send_data_lst:
                msg = create_echo_message(messages)
                del messages[0]
                for wait_client in send_data_lst:
                    try:
                        send_message(wait_client, msg)
                    except:
                        SERVER_LOGGER.info(f'Клиент {wait_client.getpeername()} отключился от сервера!')
                        clients.remove(wait_client)


if __name__ == '__main__':
    main()
