""" Серверный скрипт """

import os
import sys

import tabulate
from PyQt5.QtWidgets import QApplication

from server import server_database
from server.add_user import RegisterUser
from include.variables import *
from log_configs.server_log_config import get_logger
from server.server_gui import MainWindow, ConfigWindow, create_model_stat, UserStatWindow
from server.server_main import Server

SERVER_LOGGER = get_logger()


def print_help():
    """Функция вывода списка поддерживаемых в консольном режиме команд. Не поддерживается сейчас"""
    command_dict = [
        (EXIT, 'выход из приложения'),
        (USERS, 'вывести список всех пользователей'),
        (ACTIVE, 'вывести список пользователей онлайн'),
        (HISTORY, 'запросить историю входа пользователей'),
        (HELP, 'запросить справку по командам'),
    ]

    print(tabulate.tabulate(command_dict, headers=['Команда', 'Функция']))


def main():

    # parser = argparse.ArgumentParser()
    # parser.add_argument('-a', action='store', dest='ip', default='', help='host ip of server')
    # parser.add_argument('-p', action='store', dest='port', type=int, default=DEFAULT_PORT,
    #                     help='listening port of server')
    #
    # args = parser.parse_args()

    # server_app = QApplication(sys.argv)

    def server_config(first_launch=False):
        global config_window
        config_window = ConfigWindow(first_launch)
        config_window.db_file.insert(SERVER_DATABASE)
        config_window.port.insert(str(DEFAULT_PORT))
        if first_launch:
            config_window.run_button.clicked.connect(run_server)

    def run_server():
        global config_window
        port = int(config_window.port.text())
        ip = config_window.ip.text()
        db_file = config_window.db_file.text()
        db_path = config_window.db_path.text()
        if db_path:
            database_file = os.path.join(db_path, db_file)
        else:
            database_file = db_file

        database = server_database.ServerStorage(database_file)

        # server = Server(args.ip, args.port, database=database)
        server = Server(ip, port, database=database)
        server.daemon = True
        server.start()

        config_window.close()
        # Создание GUI главного окна:
        global main_window
        main_window = MainWindow(database)

        def show_user_stat():
            global stat_window
            stat_window = UserStatWindow()
            stat_window.user_stat_table.setModel(create_model_stat(database))
            stat_window.user_stat_table.resizeColumnsToContents()
            stat_window.user_stat_table.resizeRowsToContents()

        def show_reg_user():
            global add_user_window
            add_user_window = RegisterUser(database, server)

        main_window.statusBar().showMessage(f'Server is working; port = {port}')
        main_window.configAction.triggered.connect(server_config)
        main_window.statAction.triggered.connect(show_user_stat)
        main_window.addUserAction.triggered.connect(show_reg_user)

        main_window.refresh_button.clicked.connect(main_window.create_active_users_model)

    server_app = QApplication(sys.argv)
    server_config(first_launch=True)
    sys.exit(server_app.exec_())

    # print_help()
    # # Основной цикл сервера:
    # while True:
    #     command = input('Введите комманду: ').lower()
    #     if command == HELP:
    #         print_help()
    #     elif command == EXIT:
    #         break
    #     elif command == USERS:
    #         print(f'Список всех пользователей')
    #         for user in database.users_list():
    #             print(f'{user.id}: {user.name}')
    #     elif command == ACTIVE:
    #         print(f'Список активных пользователей')
    #         for user in database.active_users_list():
    #             print(f'Пользователь {user[0]}, адрес:порт - {user[1]}:{user[2]}, время входа: {user[3]}')
    #     elif command == HISTORY:
    #         name = input('Введите имя пользователя для вывода его истории входа или оставьте строку пустой для вывода '
    #                      'всех: ')
    #         for user in database.login_history(name):
    #             if user[2]:
    #                 print(f'Пользователь: {user[0]}, время входа: {user[1]}, время выхода: {user[2]}. '
    #                       f'Адрес:порт - {user[3]}:{user[4]}')
    #             else:
    #                 print(f'Пользователь: {user[0]}, время входа: {user[1]}. '
    #                       f'Адрес:порт - {user[3]}:{user[4]}')
    #     else:
    #         print(f'Команда не верна, чтобы посмотреть список поддерживаемых команд - введите {HELP}')


if __name__ == '__main__':
    main()
