print(' ------------ Data-дескриптор ---------------')
class DataDesc:
    ''' Data-дескриптор
    '''
    def __get__(self, obj, cls=None):
        print(' DataDesc.__get__')
        print(' ', self, obj, cls)
        return '**magic-descriptor**'
    
    def __set__(self, obj, value):
        print(' DataDesc.__set__')
        print(' ', self, obj, value)
        pass
    
    def __delete__(self, obj):
        print(' DataDesc.__delete__')
        print(' ', self, obj)
        pass

class D:
    ''' Класс с дескриптором данных
    '''
    d = DataDesc()

d_obj = D()

print('0. Содержимое d_obj.__dict__ в самом начале:', d_obj.__dict__)
print('1. Получить значение атрибута...')
# При доступе к атрибуту будет вызван метод __get__ дескриптора
x = d_obj.d
print('1. Значение атрибута (доступ через дескриптор):', x)

# Создание атрибута в словаре экземпляра класса (дескриптор)
print('2. Установить значение атрибута...')
d_obj.d = "полезное значение"
print('3. Содержимое d_obj.__dict__ после установки атрибута:', d_obj.__dict__)
x = d_obj.d
print('4. Значение атрибута (доступ через дескриптор):', x)

# Удаление атрибута из словаря экземпляра класса
print('5. Удалить атрибут...')
del d_obj.d
print('6. Содержимое d_obj.__dict__ удаления атрибута:', d_obj.__dict__)
print('7. Получить атрибут на уровне класса...')
x = D.d
print('8. Значение атрибута D.d:', x)

# Дескриптор будет заменён обычной строкой на уровне класса
print('9. Установить D.d ...')
D.d = "=A value in class="

# <<-- здесь не вызывается метод __set__
print(' == \/ Обратите внимание \/ ==')
print('10. Значение атрибута D.d:', D.d)
print('11. Значение атрибута d_obj.d:', d_obj.d)
print()
print()
print('-'*20, '\/Сохраняем данные\/', '-'*20)
print()
print('Хранить данные в атрибуте объекта дескриптора')

# Первый способ сохранить данные — просто в атрибуте объекта дескриптора.
class Grade:
    def __init__(self):
        self._value = 0
    def __get__(self, instance, instance_type):
        return self._value
    def __set__(self, instance, value):
        if not (1 <= value <= 5):
            raise ValueError("Оценка должна быть от 1 до 5")
        self._value = value

class Exam():
    ''' Класс Экзамен.
    Для простоты хранит только оценку за экзамен.
    '''
    grade = Grade()

# Но не стоит забывать, что при таком подходе
# данные будут сохранены на уровне атрибута класса Экзамен!!!
# Т.е. будут общими для всех экземпляров класса Экзамен.
# Для демонстрации создадим два Экзамена:
math_exam = Exam()
math_exam.grade = 3
language_exam = Exam()
language_exam.grade = 5
print(" Проверим результаты: ")
print("Первый экзамен ", math_exam.grade, " — верно?")
print("Второй экзамен ", language_exam.grade, " — верно?")
print('Потому что... ')
print('math_exam.grade is language_exam.grade =', math_exam.grade is
language_exam.grade)

print()
print('Хранить данные в отдельном атрибуте внешнего класса')
class Grade:
    def __init__(self, name):
        # Для данного подхода необходимо сформировать отдельное имя атрибута
        self.name = '_' + name
    def __get__(self, instance, instance_type):
        if instance is None:
            return self
        return "*{}*".format(getattr(instance, self.name))
    def __set__(self, instance, value):
        if not (1 <= value <= 100):
            raise ValueError("Балл ЕГЭ должен быть от 1 до 100")
        setattr(instance, self.name, value)

class ExamEGE():
    ''' Комплексный экзамен, на котором оцениваются разные критерии. '''
    # Для обновленного Grade нужно добавить строковые имена
    math_grade = Grade('math_grade')
    writing_grade = Grade('writing_grade')
    science_grade = Grade('science')

marks = ExamEGE()
marks.math_grade = 3

marks2 = ExamEGE()
marks2.math_grade = 5
print(" Проверим результаты: ")
print("Первый экзамен ", marks.math_grade, " — верно?")
print("Второй экзамен ", marks2.math_grade, " — верно?")

