""" Клиентский скрипт """
import argparse
import sys
from PyQt5.QtWidgets import QApplication

from include.variables import *
from include.errors import ServerError
from client.client_database import ClientStorage
from client.client_main import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from log_configs.client_log_config import get_logger

CLIENT_LOGGER = get_logger()


def main():
    parser = argparse.ArgumentParser()

    # parser.add_argument('host', nargs='?', default=DEFAULT_HOST, help='server host ip address')
    # parser.add_argument('port', nargs='?', default=DEFAULT_PORT, type=int, help='server port')
    parser.add_argument('-u', action='store', dest='user_name', help='mode of work')

    args = parser.parse_args()
    # Создание клиентского приложения
    client_app = QApplication(sys.argv)

    server_address = DEFAULT_HOST
    server_port = DEFAULT_PORT

    start_dialog = UserNameDialog()
    if args:
        start_dialog.client_name.insert(args.user_name)
    start_dialog.ip.insert(server_address)
    start_dialog.port.insert(str(server_port))
    client_app.exec_()
    # Если пользователь ввёл имя и нажал ОК, то сохранение, удаление окна и работа дальше. Иначе - выход
    if start_dialog.ok_pressed:
        user_name = start_dialog.client_name.text()
        password_hash = start_dialog.password_hash
        del start_dialog
    else:
        exit(0)

    CLIENT_LOGGER.info(
        f'Запущен клиент:\n адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {user_name}')

    # Создание объекта БД
    database = ClientStorage(user_name)

    # Создаём объекта потока
    try:
        client_thread = ClientTransport(user_name, password_hash, server_address, server_port, database)
    except ServerError as error:
        print(error.text)
        exit(1)
    client_thread.setDaemon(True)
    client_thread.start()

    # Создание GUI
    main_window = ClientMainWindow(database, client_thread)
    main_window.make_connection(client_thread)
    main_window.setWindowTitle(f'Мессенджер Alpha Version - пользователь {user_name}')
    client_app.exec_()

    # Закрытие графической оболочки, выход из потока
    client_thread.exit_()
    client_thread.join()


if __name__ == '__main__':
    main()
