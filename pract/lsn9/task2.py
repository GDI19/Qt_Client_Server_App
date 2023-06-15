"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса. По результатам проверки должно
выводиться соответствующее сообщение
"""

from task1 import hosts_ping
import ipaddress


str_ip_range = ['192.158.0.1', '192.158.0.28']


def host_range_ping(ip_str1, ip_str2):
    ip_addr1 = ipaddress.ip_address(ip_str1)
    ip_addr2 = ipaddress.ip_address(ip_str2)

    ip_list = []
    new_ip = ip_addr1
    while new_ip <= ip_addr2:
        print(new_ip)
        ip_list.append(str(new_ip))
        new_ip = new_ip +1

    res = hosts_ping(ip_list)
    return res

if __name__ == '__main__':
    host_range_ping(str_ip_range[0], str_ip_range[1])
