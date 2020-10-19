import logging
import os

from include.variables import LOG_LEVEL

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
LOG_FILE = os.path.join(LOG_PATH, 'client.log')

LOG_HANDLER = logging.FileHandler(LOG_FILE, encoding='utf-8')
LOG_FORMATTER = logging.Formatter('%(asctime)s [%(levelname)-10s] <%(filename)s> %(message)s')
LOG_HANDLER.setFormatter(LOG_FORMATTER)
logger = logging.getLogger('messenger.client')
logger.addHandler(LOG_HANDLER)
logger.setLevel(LOG_LEVEL)

if __name__ == '__main__':
    logger.debug('Отладка')
    logger.info('Инфо')
    logger.error('Ошибка')
    logger.critical('Критикал')
