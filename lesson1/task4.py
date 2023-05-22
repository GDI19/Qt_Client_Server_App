"""
4. Преобразовать слова «разработка», «администрирование», 
«protocol», «standard» из строкового представления в байтовое и 
выполнить обратное преобразование (используя методы encode и 
decode).
"""
w_lst = ['разработка', 'администрирование', 'protocol', 'standard' ]
b_lst = []
from_b_lst = []

for el in w_lst:
    b_word = el.encode('utf-8')
    b_lst.append(b_word)



for el in b_lst:
    from_b_word = el.decode('utf-8')
    from_b_lst.append(from_b_word)


def to_print_el(lst):
    for el in lst:
        print(el, type(el))


to_print_el(b_lst)
print('-' * 30)
to_print_el(from_b_lst)
