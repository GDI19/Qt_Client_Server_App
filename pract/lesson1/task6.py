"""
6. Создать текстовый файл test_file.txt, заполнить его тремя 
строками: «сетевое программирование», «сокет», «декоратор». 
Проверить кодировку файла по умолчанию. Принудительно открыть 
файл в формате Unicode и вывести его содержимое.
"""
import chardet


lst = ['сетевое программирование', 'сокет', 'декоратор']

with open('test_file.txt', 'w') as f:
    for el in lst:
        f.write(f'{el}\n' )


data = open('test_file.txt', 'rb').read()
data_encoding = chardet.detect(data)['encoding']
print('encoding:', data_encoding)


with open('test_file.txt', 'r',encoding='utf-8') as f:
    print(f.read())
