from datetime import datetime

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey, DateTime, desc, null, \
    UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapper, sessionmaker

from include.decorators import Log
from include.variables import SERVER_DATABASE
from log_configs.server_log_config import get_logger

SERVER_LOGGER = get_logger()


class ServerStorage:

    class Users:
        def __init__(self, user_name):
            self.id = None
            self.name = user_name
            self.last_login = datetime.now()

    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_datetime):
            self.id = None
            self.user = user_id
            self.ip = ip_address
            self.port = port
            self.login_time = login_datetime

    class LoginHistory:

        def __init__(self, user_id, ip_address, port, login_date):
            self.id = None
            self.user = user_id
            self.ip = ip_address
            self.port = port
            self.login_date = login_date
            self.logout_date = null()

    # Список контактов, где owner - пользователь, а user - его контакт
    class UserContacts:
        def __init__(self, owner_id, user_id):
            self.id = None
            self.owner = owner_id
            self.user = user_id

    class UserStats:
        def __init__(self, user_id):
            self.id = None
            self.user = user_id
            self.sent = 0
            self.accepted = 0

    def __init__(self, database_file=SERVER_DATABASE):
        self.database_engine = create_engine(database_file, echo=False, pool_recycle=3600,
                                             connect_args={"check_same_thread": False})

        self.metadata = MetaData()

        users_table = Table('users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String),
                            Column('last_login', DateTime))

        active_users_table = Table('active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('users.id'), unique=True),
                                   Column('ip', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime))

        login_history_table = Table('login_history', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('users.id')),
                                    Column('ip', String),
                                    Column('port', Integer),
                                    Column('login_date', DateTime),
                                    Column('logout_date', DateTime, nullable=True))

        user_contacts_table = Table('user_contacts', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('owner', ForeignKey('users.id')),
                                    Column('user', ForeignKey('users.id')),
                                    UniqueConstraint('owner', 'user', name='owner_user')
                                    )

        user_stats_table = Table('user_stats', self.metadata,
                                 Column('id', Integer, primary_key=True),
                                 Column('user', ForeignKey('users.id')),
                                 Column('sent', Integer),
                                 Column('accepted', Integer),
                                 )

        self.metadata.create_all(bind=self.database_engine)

        mapper(self.Users, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history_table)
        mapper(self.UserContacts, user_contacts_table)
        mapper(self.UserStats, user_stats_table)

        session = sessionmaker(bind=self.database_engine)
        self.session = session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    @Log()
    def user_login(self, user_name, ip_address, port):
        try:
            login_date = datetime.now()
            user_id = self.session.query(self.Users).filter_by(name=user_name)

            if not user_id.count():
                user = self.Users(user_name=user_name)
                self.session.add(user)
                self.session.commit()
                user_stat = self.UserStats(user.id)
                self.session.add(user_stat)
            else:
                user = user_id.first()
                user.last_login = login_date

            act_user_id = self.ActiveUsers(user.id, ip_address, port, login_date)
            self.session.add(act_user_id)

            login_history_rec = self.LoginHistory(user.id, ip_address, port, login_date)
            self.session.add(login_history_rec)

            self.session.commit()
        except Exception as e:
            SERVER_LOGGER.debug(f'user_login провалился!\n {e}')

    @Log()
    def user_logout(self, user_name):

        user = self.session.query(self.Users).filter_by(name=user_name).first()

        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        log_rec = self.session.query(self.LoginHistory).filter_by(user=user.id).order_by(self.LoginHistory.login_date
                                                                                         .desc()).limit(1)
        log_rec.first().logout_date = datetime.now()

        self.session.commit()

    @Log()
    def users_list(self):
        # users = self.session.query(self.Users.id, self.Users.name).all()
        # return users
        return [user[0] for user in self.session.query(self.Users.name).all()]

    @Log()
    def active_users_list(self):
        users = self.session.query(
            self.Users.name,
            self.ActiveUsers.ip,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time).join(self.Users).all()

        return users

    @Log()
    def login_history(self, user_name=None):
        query = self.session.query(self.Users.name,
                                   self.LoginHistory.login_date,
                                   self.LoginHistory.logout_date,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.Users)
        if user_name:
            query = query.filter(self.Users.name == user_name)
        return query.all()

    @Log()
    def add_user_contact(self, owner_name, user_name):
        try:
            owner = self.session.query(self.Users).filter_by(name=owner_name).first()
            user_contact = self.session.query(self.Users).filter_by(name=user_name).first()
            contact_record = self.UserContacts(owner.id, user_contact.id)
            self.session.add(contact_record)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

    @Log()
    def remove_user_contact(self, owner_name, user_name):
        try:
            owner = self.session.query(self.Users).filter_by(name=owner_name).first()
            user_contact = self.session.query(self.Users).filter_by(name=user_name).first()
            contact_record = self.session.query(self.UserContacts).filter_by(owner=owner.id, user=user_contact.id).first()
            if contact_record:
                SERVER_LOGGER.debug('Запись в UserContacts найдена')
            else:
                SERVER_LOGGER.debug('Запись в UserContacts ненайдена!')
            self.session.delete(contact_record)
            self.session.commit()
        except IntegrityError as err:
            SERVER_LOGGER.error(f'Удаление не удалось, выполняется rollback. \n{err}')
            self.session.rollback()
        except Exception as err:
            SERVER_LOGGER.error(f'Проблемы при удалении контакта:\n{err}')

    @Log()
    def get_user_contact_list(self, owner_name):
        owner = self.session.query(self.Users).filter_by(name=owner_name).first()
        contacts = self.session.query(self.UserContacts.user, self.Users.name).\
            filter_by(owner=owner.id).\
            join(self.Users, self.UserContacts.user == self.Users.id).all()

        return [contact[1] for contact in contacts]

    def process_message(self, sender, recipient):

        sender = self.session.query(self.Users).filter_by(name=sender).first()
        recipient = self.session.query(self.Users).filter_by(name=recipient).first()

        sender_row = self.session.query(self.UserStats).filter_by(user=sender.id).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UserStats).filter_by(user=recipient.id).first()
        recipient_row.accepted += 1

        self.session.commit()

    @Log()
    def get_user_stats(self):
        query = self.session.query(
            self.Users.name,
            self.Users.last_login,
            self.UserStats.sent,
            self.UserStats.accepted
        ).join(self.Users).all()
        # Возвращаем список кортежей
        return query


if __name__ == '__main__':
    test_db = ServerStorage()
    test_db.user_login('user_1', '192.168.10.20', 9876)
    test_db.user_login('user_2', '192.168.11.33', 7890)
    test_db.user_login('user_3', '192.168.11.33', 7891)

    print(test_db.active_users_list())
    print(test_db.login_history())

    test_db.add_user_contact('user_2', 'user_1')
    test_db.add_user_contact('user_2', 'user_3')

    print(f'contact_list - {test_db.get_user_contact_list("user_2")}')

    test_db.user_logout('user_1')

    print(test_db.active_users_list())

    print(test_db.login_history('user_1'))
    print(test_db.login_history('user_2'))

    print(test_db.users_list())
