"""
2. Каждое из слов «class», «function», «method» записать в 
байтовом типе без преобразования в последовательность кодов 
(не используя методы encode и decode) и определить тип, 
содержимое и длину соответствующих переменных.
"""

str_lst = [b'class', b'function', b'method']

for el in str_lst:
    print(f'<{el}> <length ', len(el), '> ', type(el))

