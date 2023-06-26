import datetime
from sqlalchemy.orm import registry, mapper, sessionmaker
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, ForeignKey, DateTime


class ServerStorage:

    class AllUsers:
        def __init__(self, username) -> None:
            self.id = None
            self.name = username
            self.last_login = datetime.datetime.now()

    class ActiveUsers:
        def __init__(self, user_id, ip_address, ip_port, login_time):
            self.id = None
            self.user = user_id
            self.ip_address = ip_address
            self.ip_port = ip_port
            self.login_time = login_time
            
    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    class UsersContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact
        
    class UsersHistory:
        def __init__(self, user, sent):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0
            


    def __init__(self) -> None:
        # echo=False - отключаем ведение лога (вывод sql-запросов)
        # pool_recycle = 7200 (переуст-ка соед-я через 2 часа)По умолчанию соединение сбрасывается через 8 часов
        self.database_engine = create_engine('sqlite:////home/gdi/visual-studio-code/practice/server_database.db', echo=False)

        # self.metadata = MetaData()
        self.mapper_registry = registry()

        users_table = Table('Users', self.mapper_registry.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50), unique=True),
            Column('last_login', DateTime)
        )

        active_users_table = Table('Active_users', self.mapper_registry.metadata,
            Column('id', Integer, primary_key=True),
            Column('user', ForeignKey('Users.id'), unique = True),
            Column('ip_address', String(50)),
            Column('ip_port', Integer),
            Column('login_time', DateTime)
        )

        login_history = Table('Login_History', self.mapper_registry.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', ForeignKey('Users.id')),
            Column('date_time', DateTime),
            Column('ip', String(50)),
            Column('port', String(50))
        )

        contacts = Table('Contacts', self.mapper_registry.metadata,
            Column('id', Integer, primary_key=True),
            Column('user', ForeignKey('Users.id')),
            Column('contact', ForeignKey('Users.id'))
            )
        
        users_history = Table('History', self.mapper_registry.metadata,
            Column('id', Integer, primary_key=True),
            Column('user', ForeignKey('Users.id')),
            Column('sent', Integer),
            Column('accepted', Integer)                  
            )

        # SQLAlchemy < 2
        # self.metadata.create_all(self.database_engine)
        # mapper(..)

        self.mapper_registry.map_imperatively(self.AllUsers, users_table)
        self.mapper_registry.map_imperatively(self.ActiveUsers, active_users_table)
        self.mapper_registry.map_imperatively(self.LoginHistory, login_history)
        self.mapper_registry.map_imperatively(self.UsersContacts, contacts)
        self.mapper_registry.map_imperatively(self.UsersHistory, users_history)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        print('-'*20)
        print(username, ip, port)
        print('-'*20)

        found_user = self.session.query(self.AllUsers).filter_by(name=username)
        print('found_user:', found_user)
        print('count found_user:', found_user.count())

        if found_user.count():
            user = found_user.first()
            print('-'*20)
            print(user)
            print('-'*20)

            user.last_login = datetime.datetime.now()
        else:
            user = self.AllUsers(username )
            print('-'*20)
            print(user)
            print('-'*20)

            self.session.add(user)
            self.session.commit()


        new_active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history =  self.LoginHistory(user.id, datetime.datetime.now(), ip, port)
        self.session.add(history)

        self.session.commit()


    # Функция фиксирующая отключение пользователя
    def user_logout(self, username):
        leaving_user = self.session.query(self.AllUsers).filter_by(name=username).first()

        self.session.query(self.ActiveUsers).filter_by(user=leaving_user.id).delete()

        self.session.commit()


    # Функция возвращает список кортежей известных пользователей со временем последнего входа.
    def users_list(self):
        query = self.session.query(self.AllUsers.name, self.AllUsers.last_login,)
        print('query u_list', query)
        return query.all()
    

    # Функция возвращает список кортежей активных пользователей
    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.ip_port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return query.all()
    

    # Функция возвращающая историю входов по пользователю или всем пользователям
    def login_history(self, username=None):
        query = self.session.query(
            self.AllUsers.name,
            self.LoginHistory.date_time,
            self.LoginHistory.ip,
            self.LoginHistory.port
        ).join(self.AllUsers)

        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()
    

    # Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
    def process_message(self, sender, recipient):
        sender_id = self.session.query(self.AllUsers).filter_by(name=sender).first().id
        recipient_id = self.session.query(self.AllUsers).filter_by(name=recipient).first().id

        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender_id).first()
        sender_row.sent += 1

        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient_id).first()
        recipient_row.accepted +=1

        self.session.commit()

    
    def add_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()


    def remove_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact:
            return
        
        print(self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id).delete()
            )
        self.session.commit()

    
    def get_contacts(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username).one()

        query = self.session.query(self.UsersContacts, self.AllUsers.name).filter_by(
            user=user.id).join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)
        print('get contacts query.all():', query.all())

        return [contact[1] for contact in query.all()]
    

    def message_history(self):
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)
        print('message query.all():', query.all())
        return query.all()


if __name__ == "__main__":
    test_db = ServerStorage()

    test_db.user_login('client_1', '192.168.1.4', 8888)
    test_db.user_login('client_2', '192.168.1.5', 7777)
    
    print('-'*20)
    print('active_users_list: 2', test_db.active_users_list())
    
    print('-'*20)
    test_db.user_logout('client_1')
    print('active_users_list: 1', test_db.active_users_list())
    
    print('-'*20)
    test_db.login_history('client_1')
    print('users_list', test_db.users_list())

    print('-'*20)
    test_db.login_history('client_1')
    print('login_history c1', test_db.login_history('client_1'))

    test_db.user_login('client_3', '192.168.1.113', 8080)
    test_db.user_login('client_4', '192.168.1.113', 8081)
    
    print('-'*20)
    print('users_list()', test_db.users_list())
    print('active_users_list()', test_db.active_users_list())

    test_db.user_logout('client_1')

    print('login_history(re)', test_db.login_history('re'))

    test_db.add_contact('client_1', 'client_3')
    test_db.add_contact('client_1', 'client_4')
    test_db.add_contact('client_3', 'client_2')
    test_db.remove_contact('client_1', 'client_4')


    #test_db.process_message('client_1', 'client_4')

    print('message_history():', test_db.message_history())
