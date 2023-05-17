"""
3. Определить, какие из слов «attribute», «класс», «функция», 
«type» невозможно записать в байтовом типе.
"""
w_lst = ['attribute', 'класс', 'функция', 'type']

for el in w_lst:
    try:
        bytes(el, 'ascii')
    except UnicodeEncodeError:
        print(el, '- невозможно записать в байтовом типе.')