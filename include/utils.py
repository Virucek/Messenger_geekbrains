""" Хранилище вспомогательных общих функций """
import json

from include.decorators import log, Log
from include.variables import MAX_PACKAGE_SIZE, ENCODING


@log
def get_message(client_socket):
    """
    Функция получения сообщения из сокета.
    Декодирует сообщение, десериализирует json, возвращает словарь
    """
    encoded_msg = client_socket.recv(MAX_PACKAGE_SIZE)
    if isinstance(encoded_msg, bytes):
        json_msg = encoded_msg.decode(ENCODING)
        msg = json.loads(json_msg)
        if isinstance(msg, dict):
            return msg
        raise ValueError
    raise ValueError


@Log()
def send_message(socket, message):
    """
    Функция отправки сообщения в сокет, его сериализация в json и кодирование
    :param socket: сокет, куда отправлять сообщение
    :param message: словарь сообщения
    :return: В случае успеха - ничего, иначе - ValueError
    """
    if isinstance(message, dict):
        json_msg = json.dumps(message)
        encoded_msg = json_msg.encode(ENCODING)
        socket.send(encoded_msg)
    else:
        raise ValueError