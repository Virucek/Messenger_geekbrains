""" Клиентский скрипт """
import base64
import binascii
import hmac
import json
import os
import sys
import threading
from socket import *
import time

from Cryptodome.Cipher import PKCS1_OAEP
from PyQt5.QtCore import QObject, pyqtSignal
from Cryptodome.PublicKey import RSA

from include import protocol
from include.decorators import Log
from include.utils import get_message, send_message
from include.variables import *
from include.errors import *
from log_configs.client_log_config import get_logger
from metaclasses import ClientVerifier

CLIENT_LOGGER = get_logger()


class ClientTransport(threading.Thread, QObject):
    """
    Класс клиента.
    Отвечает за взаимодействие с сервером: отправляет и принимает сообщения от сервера.
    Сохраняет данный в БД, загружает данные из БД
    """
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, username, password_hash, ip, port, database):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.username = username
        self.database = database

        self.password_hash = password_hash
        self.digest = None

        self.keys = RSA.generate(2048, os.urandom)

        self.decrypter = PKCS1_OAEP.new(self.keys)

        self.__init_connection(ip, port)
        # self.get_response_safe()  # Получаем приветственное сообщение (костыль :)
        self.load_database()
        self.running = True

    @Log()
    def __init_connection(self, ip, port):
        """Метод инициализации подключения к серверу"""
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        try:
            self.client_socket.connect((ip, port))
            CLIENT_LOGGER.info(f'Исходящее подключение к серверу: {ip}:{port}')
        except OSError as e:
            CLIENT_LOGGER.critical(e)
            sys.exit(1)
        else:
            send_message(self.client_socket, self.create_presence())
            CLIENT_LOGGER.info(f'Отправлено presence сообщение')
            answer = self.get_response_safe()
            if not answer:
                exit(1)
            elif RESPONSE in answer and not answer[RESPONSE] == RESPCODE_AUTH_REQUIRED:
                exit(1)
            else:
                send_message(self.client_socket, self.create_authenticate())
                CLIENT_LOGGER.info(f'Отправлено authenticate сообщение')
                time.sleep(3)
                CLIENT_LOGGER.info(f'Прошло 3 секунды...')
                if not self.get_response_safe():
                    exit(1)

    @Log()
    def update_users_list(self):
        """Метод обновления списка пользователей. Отправляет запрос на сервер, по получении овтета - обновляет БД"""
        send_message(self.client_socket, self.get_users_msg())
        CLIENT_LOGGER.info(f'Отправлено get_users сообщение')
        answer = self.get_response_safe()
        if answer is not False:
            self.database.load_known_users(answer[ALERT])

    @Log()
    def update_contacts_list(self):
        """Метод обновления списка контактов. Отправляет запрос на сервер, по получении овтета - обновляет БД"""
        send_message(self.client_socket, self.get_contacts_msg())
        CLIENT_LOGGER.info(f'Отправлено get_contacts сообщение')
        answer = self.get_response_safe()
        if answer is not False:
            for contact in answer[ALERT]:
                self.database.add_contact(contact)

    def load_database(self):
        self.update_users_list()
        self.update_contacts_list()

    @Log()
    def process_incoming_message(self, message):
        """Метод обработки входящего сообщения"""
        if RESPONSE in message:
            if message[RESPONSE] == RESPCODE_OK:
                CLIENT_LOGGER.debug(f'Полученный ответ от сервера: {message[RESPONSE]}')
                return True
            elif message[RESPONSE] == RESPCODE_ACCEPTED:
                CLIENT_LOGGER.debug(f'Полученный ответ от сервера: {message[RESPONSE]}')
                if ALERT in message:
                    CLIENT_LOGGER.debug(f'Получен корректный ответ от сервера: {message[RESPONSE]}')
                    return True
            elif message[RESPONSE] == RESPCODE_AUTH_REQUIRED:
                CLIENT_LOGGER.debug(f'Полученный ответ от сервера: {message[RESPONSE]}')
                if DATA in message:
                    hash = hmac.new(binascii.hexlify(self.password_hash), message[DATA].encode('ascii'), 'MD5')
                    self.digest = hash.digest()
                    return True
                elif KEY in message:
                    return True
            CLIENT_LOGGER.debug('Сервер ответил ошибкой')
            if ALERT in message:
                CLIENT_LOGGER.debug(message[ALERT])
                print(message[ALERT])
            raise ServerError(f'Некорректный ответ от сервера:\n{message}')
        elif ACTION in message:
            if message[ACTION] == MSG and MESSAGE in message:
                encrypted_message = base64.b64decode(message[MESSAGE])
                try:
                    decrypted_message = self.decrypter.decrypt(encrypted_message)
                except (ValueError, TypeError) as e:
                    CLIENT_LOGGER.error(f'Не удалось декодировать сообщение\n{e}')
                    return
                self.database.save_incoming_message(message[FROM], decrypted_message.decode('utf-8'))
                self.new_message.emit(message[FROM])
                return True
        raise ValueError

    @Log()
    def create_presence(self):
        """Метод создания presence запроса"""
        msg = protocol.PRESENCE_MSG_CLIENT
        msg[TIME] = time.time()
        msg[USER][ACCOUNT_NAME] = self.username
        msg[USER][STATUS] = 'Presense status test?'
        msg[USER][PUBLIC_KEY] = self.keys.publickey().export_key().decode('ascii')
        CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение:\n{msg}')
        return msg

    @Log()
    def create_authenticate(self):
        """Метод создания аутентификационного запроса"""
        msg = protocol.AUTHENTICATE_MSG
        msg[TIME] = time.time()
        msg[USER][ACCOUNT_NAME] = self.username
        msg[USER][STATUS] = 'Authenticate'
        msg[USER][PASSWORD] = binascii.b2a_base64(self.digest).decode('ascii')
        CLIENT_LOGGER.debug(f'Сформировано {AUTHENTICATE} сообщение:\n{msg}')
        return msg

    @Log()
    def get_contacts_msg(self):
        """Метод создания запроса списка контактов"""
        msg = protocol.GET_USER_CONTACTS_MSG
        msg[TIME] = time.time()
        msg[USER_LOGIN] = self.username
        CLIENT_LOGGER.debug(f'Сформировано {GET_CONTACTS} сообщение:\n{msg}')
        return msg

    @Log()
    def get_users_msg(self):
        """Метод создания запроса списка пользователей"""
        msg = protocol.GET_USERS_MSG
        msg[TIME] = time.time()
        msg[USER_LOGIN] = self.username
        CLIENT_LOGGER.debug(f'Сформировано {GET_USERS} сообщение:\n{msg}')
        return msg

    @Log()
    def get_pubkey_msg(self, username):
        """Метод создания запроса публичного ключа пользователя по его имени"""
        msg = protocol.GET_PUBKEY_REQ_MSG
        msg[TIME] = time.time()
        msg[USER] = username
        CLIENT_LOGGER.debug(f'Сформировано {GET_PUBLIC_KEY} сообщение:\n{msg}')
        return msg

    def pubkey_request(self, username):
        """Метод отправки запроса публичного ключа и получения ответа"""
        send_message(self.client_socket, self.get_pubkey_msg(username))
        ans = self.get_response_safe()
        if RESPONSE in ans and ans[RESPONSE] == RESPCODE_AUTH_REQUIRED:
            return ans[KEY]
        else:
            CLIENT_LOGGER.error(f'Не удалось получить ключ собеседника {username}.')

    @Log()
    def get_response_safe(self):
        """Метод приема ответов от сервера"""
        try:
            answer = get_message(self.client_socket)
            CLIENT_LOGGER.info(f'Получено сообщение от сервера: {answer}')
            self.process_incoming_message(answer)
            return answer
        except ServerError as err:
            CLIENT_LOGGER.error(err)
        except ValueError:
            CLIENT_LOGGER.error('Ошибка декодирования сообщения от сервера')
        return False

    @Log()
    def create_message(self, user_to, message):
        """Метод создания сообщения"""
        time.sleep(0.5)
        message_full = protocol.CHAT_MSG_CLIENT.copy()
        message_full[TIME] = time.time()
        message_full[FROM] = self.username
        if user_to:
            message_full[TO] = user_to
        message_full[MESSAGE] = message
        CLIENT_LOGGER.debug(f'Сформировано сообщение:\n{message_full}')
        return message_full

    @Log()
    def send_message(self, user_to, message_txt):
        """Метод отправки созданного сообщения"""
        return send_message(self.client_socket, self.create_message(user_to, message_txt))

    @Log()
    def create_exit_message(self):
        """Метод создания сообщения на выход пользователя из чата"""
        msg = protocol.EXIT_MSG_CLIENT
        msg[TIME] = time.time()
        msg[FROM] = self.username
        CLIENT_LOGGER.debug(f'Сформировано EXIT сообщение:\n{msg}')
        return msg

    @Log()
    def exit_(self):
        """Метод отправки сообщения на выход пользователя из чата"""
        return send_message(self.client_socket, self.create_exit_message())

    @Log()
    def create_add_contact_msg(self, user_contact):
        """Метод создания запроса на добавление контакта"""
        msg = protocol.ADD_USER_CONTACT_MSG.copy()
        msg[USER_ID] = user_contact
        msg[TIME] = time.time()
        msg[USER_LOGIN] = self.username
        CLIENT_LOGGER.debug(f'Сформировано {ADD_CONTACT} сообщение:\n{msg}')
        return msg

    def add_contact(self, user_contact):
        """Метод отправки запроса на добавление контакта"""
        return send_message(self.client_socket, self.create_add_contact_msg(user_contact))

    @Log()
    def create_remove_contact_msg(self, user_contact):
        """Метод отправки запроса на удаление контакта"""
        msg = protocol.REMOVE_USER_CONTACT_MSG.copy()
        msg[USER_ID] = user_contact
        msg[TIME] = time.time()
        msg[USER_LOGIN] = self.username
        CLIENT_LOGGER.debug(f'Сформировано {REMOVE_CONTACT} сообщение:\n{msg}')
        return msg

    def remove_contact(self, user_contact):
        """Метод отправки запроса на удаление контакта"""
        return send_message(self.client_socket, self.create_remove_contact_msg(user_contact))

    def run(self):
        """Основной цикл клиента"""
        CLIENT_LOGGER.debug('Запущен процесс клиента.')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет. - из примера
            # если не сделать тут задержку, то отправка может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            try:
                self.client_socket.settimeout(0.5)
                message = get_message(self.client_socket)
            except OSError as err:
                if err.errno:
                    CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
            # Проблемы с соединением
            except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                CLIENT_LOGGER.debug(f'Потеряно соединение с сервером.')
                self.running = False
                self.connection_lost.emit()
            else:
                CLIENT_LOGGER.debug(f'Принято сообщение с сервера: {message}')
                self.process_incoming_message(message)
            finally:
                self.client_socket.settimeout(5)
