"""
таблицы
a) клиент:
    * логин;
    * информация.
b) история клиента:
    * время входа;
    * ip-адрес.
c) список контактов (составляется на основании выборки всех записей с id_владельца):
    * id_владельца;
    * id_клиента.
"""
import datetime
from sqlalchemy.orm import mapper, sessionmaker
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
            
    class UsersHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port


    def __init__(self) -> None:
        # echo=False - отключаем ведение лога (вывод sql-запросов)
        # pool_recycle = 7200 (переуст-ка соед-я через 2 часа)По умолчанию соединение сбрасывается через 8 часов
        self.database_engine = create_engine('sqlite:////home/gdi/visual-studio-code/practice/server_database.db', echo=False)

        self.metadata = MetaData()

        users_table = Table('users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(50), unique=True),
            Column('last_login', DateTime)
        )

        active_users_table = Table('Active_users', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user', ForeignKey('users.id'), unique = True),
            Column('ip_address', String(50)),
            Column('ip_port', Integer),
            Column('login_time', DateTime)
        )

        users_history = Table('Users_History', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', ForeignKey('users.id')),
            Column('date_time', DateTime),
            Column('ip', String(50)),
            Column('port', String(50))
        )

        self.metadata.create_all(self.database_engine)

        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.UsersHistory, users_history)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        print(username, ip, port)

        found_user = self.session.query(self.AllUsers).filter_by(name=username )

        if found_user.count():
            user = found_user.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.AllUsers(username )
            self.session.add(user)
            self.session.commit()


        new_active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history =  self.UsersHistory(user.id, datetime.datetime.now(), ip, port)
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
        return query.all()
    

    # Функция возвращает список кортежей активных пользователей
    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.ip_port,
            self.ActiveUsers.login_time
        )
        return query.all()
    

    # Функция возвращающая историю входов по пользователю или всем пользователям
    def login_history(self, username=None):
        query = self.session.query(
            self.AllUsers.name,
            self.UsersHistory.date_time,
            self.UsersHistory.ip,
            self.UsersHistory.port
        ).join(self.AllUsers)

        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()


if __name__ == "__main__":
    test_db = ServerStorage()

    test_db.user_login('client_1', '192.168.1.4', 8888)
    test_db.user_login('client_2', '192.168.1.5', 7777)

    print(test_db.active_users_list())
    
    test_db.user_logout('client_1')
    print(test_db.active_users_list())

    test_db.login_history('client_1')
    print(test_db.users_list())

