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

    def __init__(self):
        self.database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=3600,
                                             connect_args={"check_same_thread": False})

        self.metadata = MetaData()

        users_table = Table('users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String))

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

        self.metadata.create_all(bind=self.database_engine)

        mapper(self.Users, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history_table)
        mapper(self.UserContacts, user_contacts_table)

        session = sessionmaker(bind=self.database_engine)
        self.session = session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    @Log()
    def user_login(self, user_name, ip_address, port):
        try:
            user_id = self.session.query(self.Users).filter_by(name=user_name)

            if not user_id.count():
                user = self.Users(user_name=user_name)
                self.session.add(user)
                self.session.commit()
            else:
                user = user_id.first()

            login_date = datetime.now()

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
        users = self.session.query(self.Users.id, self.Users.name).all()
        return users

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

    def add_user_contact(self, owner_name, user_name):
        try:
            owner = self.session.query(self.Users).filter_by(name=owner_name).first()
            user_contact = self.session.query(self.Users).filter_by(name=user_name).first()
            contact_record = self.UserContacts(owner.id, user_contact.id)
            self.session.add(contact_record)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

    def user_contact_list(self, owner_name):
        owner = self.session.query(self.Users).filter_by(name=owner_name).first()
        contacts = self.session.query(self.UserContacts.owner, self.UserContacts.user).filter_by(owner=owner.id).all()

        return contacts


if __name__ == '__main__':
    test_db = ServerStorage()
    test_db.user_login('user_1', '192.168.10.20', 9876)
    test_db.user_login('user_2', '192.168.11.33', 7890)

    print(test_db.active_users_list())
    print(test_db.login_history())

    test_db.add_user_contact('user_2', 'user_1')

    print(f'contact_list - {test_db.user_contact_list("user_2")}')

    test_db.user_logout('user_1')

    print(test_db.active_users_list())

    print(test_db.login_history('user_1'))
    print(test_db.login_history('user_2'))

    print(test_db.users_list())
