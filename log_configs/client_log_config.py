import inspect
import logging
import os

from include.variables import LOG_LEVEL

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
LOG_FILE = os.path.join(LOG_PATH, 'client.log')
LOGGER_NAME = 'messenger.client'
LOG_HANDLER = logging.FileHandler(LOG_FILE, encoding='utf-8')
LOG_FORMATTER = logging.Formatter('%(asctime)s [%(levelname)-10s] <%(rfilename)s> %(message)s')
LOG_HANDLER.setFormatter(LOG_FORMATTER)


def get_logger(logger_name=LOGGER_NAME):
    logger = logging.getLogger(logger_name)
    logger.addHandler(LOG_HANDLER)
    logger.setLevel(LOG_LEVEL)
    rfilename = inspect.stack()[-1].filename.split('/')[-1]
    extra = dict(rfilename=rfilename)
    return logging.LoggerAdapter(logger, extra=extra)


if __name__ == '__main__':
    logger = get_logger()
    logger.debug('Отладка')
    logger.info('Инфо')
    logger.error('Ошибка')
    logger.critical('Критикал')
