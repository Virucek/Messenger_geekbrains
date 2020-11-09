from ipaddress import ip_address

from log_configs.server_log_config import get_logger

SERVER_LOGGER = get_logger()


class Port:

    def __set__(self, instance, value):
        if 1024 > value or value > 65535:
            SERVER_LOGGER.error(f'Некорректный порт для прослушивания! - {value} не в [1024; 65535]')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class IpAddress:

    def __set__(self, instance, value):
        if value:
            try:
                _value = ip_address(value)
            except:
                SERVER_LOGGER.error(f'Некорректный формат ip адреса {value}! Поддерживается только IPv4')
                exit(1)

        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name