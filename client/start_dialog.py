import binascii
import hashlib
from ipaddress import ip_address

from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, qApp


# Стартовый диалог

class UserNameDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.ok_pressed = False
        self.password_hash = None

        self.setWindowTitle('Приветствие')
        self.setFixedSize(175, 250)

        self.client_name_label = QLabel('Введите имя пользователя:', self)
        self.client_name_label.move(10, 10)
        self.client_name_label.setFixedSize(150, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.password_label = QLabel('Введите пароль:', self)
        self.password_label.move(10, 60)
        self.password_label.setFixedSize(150, 10)

        self.password = QLineEdit(self)
        self.password.setFixedSize(154, 20)
        self.password.move(10, 80)

        self.ip_label = QLabel('Введите адрес сервера:', self)
        self.ip_label.move(10, 110)
        self.ip_label.setFixedSize(150, 15)

        self.ip = QLineEdit(self)
        self.ip.setFixedSize(154, 20)
        self.ip.move(10, 130)

        self.port_label = QLabel('Введите порт сервера:', self)
        self.port_label.move(10, 160)
        self.port_label.setFixedSize(150, 15)

        self.port = QLineEdit(self)
        self.port.setFixedSize(154, 20)
        self.port.move(10, 180)

        self.btn_ok = QPushButton('Начать', self)
        self.btn_ok.move(10, 210)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(90, 210)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    # Обработчик кнопки ОК, если поле вводе не пустое, ставим флаг и завершаем приложение.
    def click(self):
        client_name = self.client_name.text()
        ip = self.ip.text()
        port = self.port.text()
        if client_name and ip and port:
            try:
                ip_address(ip)
            except ValueError as e:
                print(e)
                qApp.exit(1)
            else:
                try:
                    int(port)
                except ValueError:
                    print('Порт должен быть указан числом!')
                    qApp.exit(1)
                else:
                    self.ok_pressed = True
                    passwd_byte = self.password.text().encode('utf-8')
                    salt = client_name.lower().encode('utf-8')
                    self.password_hash = hashlib.pbkdf2_hmac('sha512', passwd_byte, salt, 10000)
                    qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
