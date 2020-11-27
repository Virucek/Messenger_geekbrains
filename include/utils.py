""" Хранилище вспомогательных общих функций """
import json

from include.decorators import log, Log
from include.variables import MAX_PACKAGE_SIZE, ENCODING


@log
def get_message(client_socket):
    encoded_msg = client_socket.recv(MAX_PACKAGE_SIZE)
    print(encoded_msg)
    if isinstance(encoded_msg, bytes):
        json_msg = encoded_msg.decode(ENCODING)
        print(json_msg)
        msg = json.loads(json_msg)
        print(msg)
        if isinstance(msg, dict):
            return msg
        raise ValueError
    raise ValueError


@Log()
def send_message(socket, message):
    if isinstance(message, dict):
        json_msg = json.dumps(message)
        encoded_msg = json_msg.encode(ENCODING)
        socket.send(encoded_msg)
    else:
        raise ValueError