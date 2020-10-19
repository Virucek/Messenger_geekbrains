""" Серверный скрипт """
import argparse
from socket import *
import sys

from include import protocol
from include.utils import get_message, send_message
from include.variables import *
import logging
import log_configs.server_log_config

SERVER_LOGGER = logging.getLogger('messenger.server')


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


def process_incoming_message(msg):
    if ACTION in msg:
        if msg[ACTION] == PRESENCE:
            if msg.keys() != protocol.PRESENCE_MSG_CLIENT.keys():
                SERVER_LOGGER.error('В запросе присутствуют лишние поля или отсутствуют нужные!')
                return RESPCODE_BAD_REQ
            if msg[USER].keys() != protocol.PRESENCE_MSG_CLIENT[USER].keys():
                SERVER_LOGGER.error(f'В запросе неверный объект {USER}!')
                return RESPCODE_BAD_REQ
            if msg[USER][ACCOUNT_NAME] != NOT_LOGGED_USER:
                SERVER_LOGGER.error(f'Некорректный пользователь для {PRESENCE} сообщения')
                return RESPCODE_BAD_REQ
            SERVER_LOGGER.debug(f'Сообщение {PRESENCE} корректное. Ответ успешный')
            return RESPCODE_OK
        SERVER_LOGGER.error(f'Такое значение {ACTION} {msg[ACTION]} не поддерживается!')
    SERVER_LOGGER.error(f'{ACTION} отсутствует в сообщении')
    return RESPCODE_BAD_REQ


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', action='store', dest='ip', default='', help='host ip of server')
    parser.add_argument('-p', action='store', dest='port', type=int, default=DEFAULT_PORT,
                        help='listening port of server')

    args = parser.parse_args()
    if args.port < 1024 or args.port > 65535:
        SERVER_LOGGER.error('порт должен быть в диапазоне 1024-65535')
        sys.exit(1)

    with socket(AF_INET, SOCK_STREAM) as server_sock:
        try:
            server_sock.bind((args.ip, args.port))
            server_sock.listen(MAX_CONNECTIONS)
            SERVER_LOGGER.info(f'Запущен сервер на порту: {args.port}')
        except OSError as e:
            SERVER_LOGGER.critical(e)
            print(e)
            sys.exit(1)

        while True:
            client_sock, addr = server_sock.accept()
            SERVER_LOGGER.info(f'Входящее подключение с адреса: {addr}')
            with client_sock:
                error = None
                try:
                    inc_msg = get_message(client_sock)
                    SERVER_LOGGER.debug('Получено сообщение:'
                                        f'{inc_msg}')
                    resp_code = process_incoming_message(inc_msg)
                except ValueError:
                    error = 'Ошибка декодирования сообщения от клиента'
                    resp_code = RESPCODE_SERVER_ERROR
                    SERVER_LOGGER.error(error)
                resp_msg = create_response(resp_code, error)
                SERVER_LOGGER.info('Отправлен ответ:'
                                   f'{resp_msg}')
                send_message(client_sock, resp_msg)


if __name__ == '__main__':
    main()
