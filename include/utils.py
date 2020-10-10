import json

from include.variables import MAX_PACKAGE_SIZE, ENCODING


def get_message(client_socket):
    encoded_msg = client_socket.recv(MAX_PACKAGE_SIZE)
    if isinstance(encoded_msg, bytes):
        json_msg = encoded_msg.decode(ENCODING)
        msg = json.loads(json_msg)
        if isinstance(msg, dict):
            return msg
        raise ValueError
    raise ValueError


def send_message(socket, message):
    if isinstance(message, dict):
        json_msg = json.dumps(message)
        encoded_msg = json_msg.encode(ENCODING)
        socket.send(encoded_msg)
    else:
        raise ValueError