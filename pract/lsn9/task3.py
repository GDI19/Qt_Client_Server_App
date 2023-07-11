"""
3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из
примера 2. Но в данном случае результат должен быть итоговым по всем ip-адресам,
представленным в табличном формате (использовать модуль tabulate). Таблица должна
состоять из двух колонок и выглядеть примерно так:
Reachable
-------------
10.0.0.1
10.0.0.2
Unreachable
-------------
10.0.0.3
10.0.0.4
"""
from task2 import host_range_ping
from tabulate import tabulate

ip_from = '10.0.0.1'
ip_to = '10.0.0.6'

def host_range_ping_tab():
    ip_dict = host_range_ping(ip_from, ip_to)
    print(tabulate(ip_dict, headers='keys', tablefmt='pipe'))


if __name__ == '__main__':
    host_range_ping_tab()