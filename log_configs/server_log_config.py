
import logging
import logging.handlers
import os
from sys import stderr

from include.variables import LOG_LEVEL


LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
LOG_FILE = os.path.join(LOG_PATH, 'server.log')

STREAM_HANDLER = logging.StreamHandler(stderr)
LOG_HANDLER = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='D', interval=1, encoding='utf8')
LOG_FORMATTER = logging.Formatter('%(asctime)s [%(levelname)-10s] <%(filename)s> %(message)s')

STREAM_HANDLER.setFormatter(LOG_FORMATTER)
STREAM_HANDLER.setLevel(logging.ERROR)
LOG_HANDLER.setFormatter(LOG_FORMATTER)

logger = logging.getLogger('messenger.server')
logger.addHandler(LOG_HANDLER)
logger.setLevel(LOG_LEVEL)

if __name__ == '__main__':
    logger.critical('Критикал')
    logger.error('Ошибка')
    logger.debug('Дебаг информация')
    logger.info('Инфо')
