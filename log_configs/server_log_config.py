import inspect
import logging
import logging.handlers
import os
from sys import stderr

from include.variables import LOG_LEVEL

LOGGER_NAME = 'messenger.server'

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
LOG_FILE = os.path.join(LOG_PATH, 'server.log')

STREAM_HANDLER = logging.StreamHandler(stderr)
LOG_HANDLER = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='D', interval=1, encoding='utf8')
LOG_FORMATTER = logging.Formatter('%(asctime)s [%(levelname)-10s] <%(rfilename)s> %(message)s')

STREAM_HANDLER.setFormatter(LOG_FORMATTER)
STREAM_HANDLER.setLevel(logging.ERROR)
LOG_HANDLER.setFormatter(LOG_FORMATTER)


def get_logger(logger_name=LOGGER_NAME):
    """
    Функция для получения логгера. Добавляются необходимые хендлеры, устанавливается уровень логгирования,
    присваивается rfilename и передается в extra в LoggerAdapter,
    чтобы постоянно вручную не передавать rfilename на каждый вызов логгера.
    Возвращает полученный экземпляр класса LoggerAdapter
    """
    logger = logging.getLogger(logger_name)
    logger.addHandler(LOG_HANDLER)
    logger.setLevel(LOG_LEVEL)
    rfilename = inspect.stack()[-1].filename.split('/')[-1]
    extra = dict(rfilename=rfilename)
    return logging.LoggerAdapter(logger, extra=extra)


if __name__ == '__main__':
    logger = get_logger()
    logger.critical('Критикал')
    logger.error('Ошибка')
    logger.debug('Дебаг информация')
    logger.info('Инфо')
