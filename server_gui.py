import sys

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp, QDialog, QLabel, QLineEdit, QPushButton, \
    QFileDialog, QTableView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        exitAction = QAction('Выход', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(qApp.quit)

        self.configAction = QAction('Настройки', self)

        self.statAction = QAction('Статистика пользователей', self)

        self.toolbar = self.addToolBar('mainBar')
        self.toolbar.addAction(exitAction)
        self.toolbar.addAction(self.configAction)
        self.toolbar.addAction(self.statAction)

        self.setFixedSize(600, 430)

        # Окно со списком подключенных клиентов
        self.active_users_table = QTableView(self)
        self.active_users_table.move(10, 45)
        self.active_users_table.setFixedSize(580, 320)

        self.refresh_button = QPushButton('Обновить список', self)
        self.refresh_button.move(10, 370)
        self.refresh_button.setFixedSize(140, 25)

        self.setWindowTitle('Server')
        self.show()


class ConfigWindow(QDialog):
    def __init__(self, first_launch=False):
        super(ConfigWindow, self).__init__()
        if first_launch:
            self.__init_ui(with_run_btn=True)
        else:
            self.__init_ui()

    def __init_ui(self, with_run_btn=False):
        self.setFixedSize(350, 230)
        self.setWindowTitle('Настройки сервера')

        self.db_path_title = QLabel('Путь к базе данных: ', self)
        self.db_path_title.move(15, 10)
        self.db_path_title.setFixedSize(320, 15)

        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(15, 30)

        self.db_path_button = QPushButton('Обзор', self)
        self.db_path_button.move(275, 28)
        self.db_path_button.setFixedSize(65, 22)

        def open_file_diag_window():
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            self.db_path.clear()
            self.db_path.insert(path)

        self.db_path_button.clicked.connect(open_file_diag_window)

        self.db_file_title = QLabel('Имя файла БД: ', self)
        self.db_file_title.move(15, 70)
        self.db_file_title.setFixedSize(80, 15)

        self.db_file = QLineEdit(self)
        self.db_file.move(160, 68)
        self.db_file.setFixedSize(140, 20)

        self.port_title = QLabel('Порт для прослушивания: ', self)
        self.port_title.move(15, 110)
        self.port_title.setFixedSize(150, 15)

        self.port = QLineEdit(self)
        self.port.move(160, 108)
        self.port.setFixedSize(140, 20)

        self.ip_title = QLabel('IP, с которого принимать\nсоединения: ', self)
        self.ip_title.move(15, 145)
        self.ip_title.setFixedSize(150, 24)

        self.ip = QLineEdit(self)
        self.ip.move(160, 148)
        self.ip.setFixedSize(140, 20)

        if with_run_btn:
            self.run_button = QPushButton('Запустить', self)
            self.run_button.move(160, 190)
            self.run_button.setFixedSize(80, 22)

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 190)
        self.close_button.setFixedSize(80, 22)
        self.close_button.clicked.connect(self.close)

        self.show()


class UserStatWindow(QDialog):
    def __init__(self):
        super(UserStatWindow, self).__init__()
        self.__init_ui()

    def __init_ui(self):
        self.setFixedSize(600, 250)
        self.setWindowTitle('Статистика пользователей')

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(10, 220)
        self.close_button.clicked.connect(self.close)

        self.user_stat_table = QTableView(self)
        self.user_stat_table.move(10, 15)
        self.user_stat_table.setFixedSize(570, 190)

        self.show()


def create_model_gui(database):
    users_list = database.active_users_list()
    list = QStandardItemModel()
    list.setHorizontalHeaderLabels(['Имя пользователя', 'IP адрес', 'Порт', 'Время входа'])
    for user in users_list:
        user_name, ip, port, time = user
        user_name = QStandardItem(user_name)
        user_name.setEditable(False)

        ip = QStandardItem(ip)
        ip.setEditable(False)

        port = QStandardItem(str(port))
        port.setEditable(False)

        time = QStandardItem(str(time))
        time.setEditable(False)
        list.appendRow([user_name, ip, port, time])
    return list


def create_model_stat(database):
    res_list = database.get_user_stats()
    list = QStandardItemModel()
    list.setHorizontalHeaderLabels(['Имя пользователя', 'Последний вход', 'Сообщений отправлено', 'Сообщений получено'])
    for record in res_list:
        user_name, last_login, sent, accepted = record
        user_name = QStandardItem(user_name)
        user_name.setEditable(False)

        last_login = QStandardItem(str(last_login))
        last_login.setEditable(False)

        sent = QStandardItem(str(sent))
        sent.setEditable(False)

        accepted = QStandardItem(str(accepted))
        accepted.setEditable(False)
        list.appendRow([user_name, last_login, sent, accepted])
    return list


if __name__ == '__main__':
    app = QApplication(sys.argv)
    config_window = ConfigWindow()
    app.exec_()