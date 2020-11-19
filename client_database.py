""" Клиентское хранилище """
from datetime import datetime

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker

from include.decorators import Log


class ClientStorage:

    class KnownUsers:
        def __init__(self, user_name):
            self.id = None
            self.name = user_name

    class Contacts:
        def __init__(self, contact_name):
            self.id = None
            self.name = contact_name

    class Messages:
        def __init__(self, user_name, direction, body):
            self.id = None
            self.user = user_name
            self.direction = direction
            self.body = body
            self.date = datetime.now()

    def __init__(self, client_database):

        self.database_engine = create_engine(client_database, echo=False, pool_recycle=3600,
                                             connect_args={"check_same_thread": False})
        self.metadata = MetaData()

        known_users_table = Table('known_users', self.metadata,
                                  Column('id', Integer, primary_key=True),
                                  Column('name', String))

        contacts_table = Table('contacts', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('name', String, unique=True))

        messages_table = Table('messages', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('user', String),
                               Column('direction', String),
                               Column('body', String),
                               Column('date', DateTime))

        self.metadata.create_all(bind=self.database_engine)

        mapper(self.KnownUsers, known_users_table)
        mapper(self.Contacts, contacts_table)
        mapper(self.Messages, messages_table)

        session = sessionmaker(bind=self.database_engine)
        self.session = session()

    def get_known_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.name).all()]

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    @Log()
    def load_known_users(self, new_users):
        self.session.query(self.KnownUsers).delete()
        for user_name in new_users:
            user = self.KnownUsers(user_name)
            self.session.add(user)
        self.session.commit()

    # @Log()
    # def load_contacts(self, new_contacts):
    #
    #     for contact_name in new_contacts:
    #         contact = self.Contacts(contact_name)
    #         self.session.add(contact)
    #     self.session.commit()

    @Log()
    def add_contact(self, new_contact):
        if not self.session.query(self.Contacts).filter_by(name=new_contact).count():
            contact = self.Contacts(new_contact)
            self.session.add(contact)
            self.session.commit()

    @Log()
    def remove_contact(self, del_contact):

        self.session.query(self.Contacts).filter_by(name=del_contact).delete()
        self.session.commit()

    @Log()
    def save_incoming_message(self, user, body):
        msg = self.Messages(user, 'I', body)
        self.session.add(msg)
        self.session.commit()

    @Log()
    def save_outgoing_message(self, user, body):
        msg = self.Messages(user, 'O', body)
        self.session.add(msg)
        self.session.commit()

    def get_message_history(self, user=None):
        query = self.session.query(self.Messages)
        if user:
            query = query.filter_by(user=user)

        return [(msg.user, msg.direction, msg.body, msg.date) for msg in query.all()]


# отладка
if __name__ == '__main__':
    db_url = f'sqlite:///client_test1.db3'
    test_db = ClientStorage(db_url)
    for i in ['test3', 'test4', 'test5']:
        test_db.add_contact(i)
    test_db.add_contact('test4')
    test_db.load_known_users(['test1', 'test2', 'test3', 'test4', 'test5'])
    test_db.save_incoming_message('test2', f'тестовое исходящее сообщение к test2:{datetime.now()}!')
    test_db.save_outgoing_message('test2', f'тестовое входящее сообщение от test2:{datetime.now()}!')
    test_db.save_outgoing_message('test5', f'третье тестовое входящее сообщение от test5: {datetime.now()}!')
    print(test_db.get_contacts())
    print(test_db.get_known_users())
    print(test_db.get_message_history('test2'))
    print(test_db.get_message_history('test3'))
    print(test_db.get_message_history())
    test_db.remove_contact('test4')
    print(test_db.get_contacts())
