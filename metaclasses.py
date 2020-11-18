import dis

from log_configs import server_log_config, client_log_config

SERVER_LOGGER = server_log_config.get_logger()
CLIENT_LOGGER = client_log_config.get_logger()


def check_allowed(allowed_list, checked_list, _logger):
    verify_errors = 0
    for allow_el in allowed_list:
        if allow_el not in checked_list:
            verify_errors += 1
            _logger.error(f'{allow_el} отсутствует в классе!')
    return verify_errors


def check_disallowed(dis_list, checked_list, name, _logger):
    verify_errors = 0
    for el in checked_list:
        if el in dis_list:
            _logger.error(f'{el} не допускается в {name} классе!')
            verify_errors += 1
    return verify_errors


class ServerVerifier(type):

    def __init__(cls, name, bases, dct):

        global_names = []

        verify_errors = 0

        dis_methods = [
            'connect'
        ]

        allowed_attrs = [
            'AF_INET',
            'SOCK_STREAM'
        ]

        for func in dct:
            try:
                dis_instr = dis.get_instructions(dct[func])
            except TypeError:
                pass
            else:
                for i in dis_instr:
                    # Т.к. AF_INET и SOCK_STREAM агружены глобально, а не как аттрибуты, ищем их в LOAD_GLOBAL
                    if i.opname == 'LOAD_GLOBAL':
                        global_names.append(i.argval)
        global_names = set(global_names)

        verify_errors += check_disallowed(dis_methods, global_names, name, SERVER_LOGGER)
        verify_errors += check_allowed(allowed_attrs, global_names, SERVER_LOGGER)

        if verify_errors:
            raise TypeError('Класс сервера не прошел валидацию!')

        super().__init__(name, bases, dct)


class ClientVerifier(type):

    def __init__(cls, name, bases, dct):

        global_names = []

        verify_errors = 0

        dis_methods = [
            'accept',
            'listen',
            'socket',
        ]

        # allowed_methods = [
        #     'send_message',
        #     'get_message'
        # ]

        for func in dct:
            try:
                dis_instr = dis.get_instructions(dct[func])
            except TypeError:
                pass
            else:
                for i in dis_instr:
                    if i.opname == 'LOAD_GLOBAL':
                        global_names.append(i.argval)
        global_names = set(global_names)
        print(global_names)
        verify_errors += check_disallowed(dis_methods, global_names, name, CLIENT_LOGGER)

        if 'send_message' not in global_names and 'get_message' not in global_names:
            CLIENT_LOGGER.error(f'send_message и get_message отсутствуют в {name} классе!'
                                'Некорректная реализация работы с сокетом!')
            verify_errors += 1

        if verify_errors:
            raise TypeError('Класс сервера не прошел валидацию!')

        super().__init__(name, bases, dct)
