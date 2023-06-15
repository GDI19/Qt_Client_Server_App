"""
1. Написать функцию 
host_ping(), 
в которой с помощью утилиты ping 
будет проверяться доступность сетевых узлов. 
Аргументом функции является 
- список, c сетевыми узелами представленые именем хоста или ip-адресом. 
В функции необходимо
перебирать ip-адреса и проверять их доступность 
«Узел доступен», «Недоступные узлы». 
При этом ip-адрес сетевого узла должен создаваться с
помощью функции 
ip_address().
"""

import ipaddress
import subprocess
from tabulate import tabulate


str_ip_list = ['ya.ru', '192.168.0.1', '192.158.0.1', '192.148.0.1']


def hosts_ping(lst):
    dict_ip_addresses = {
        'Доступные узлы': [],
        'Недоступные узлы': [],
    }
    for addr in lst:
        ping_addr = subprocess.Popen(['ping', addr, '-w', '3', '-n', '1'], shell=False,  stdout=subprocess.PIPE)
        ping_addr.wait()
        if ping_addr.returncode == 0:
            print(f'{addr} - доступен')
            dict_ip_addresses['Доступные узлы'].append(addr)
        else:
            print(f'{addr} - недоступен')
            dict_ip_addresses['Недоступные узлы'].append(addr)
    return dict_ip_addresses


def make_ip_address(str_ip_address):
    return ipaddress.ip_address(str_ip_address)


def check_ip(str_ip_addresses):
    dict_ip_addresses = {
        'Доступные узлы': [],
        'Недоступные узлы': [],
    }
    for str_ip_addr in str_ip_addresses:
        ip_addr = make_ip_address(str_ip_addr)
        if ip_addr.is_loopback:
            dict_ip_addresses['Недоступные узлы'].append(f'{ip_addr} - loopback адрес')
        elif ip_addr.is_multicast:
            dict_ip_addresses['Недоступные узлы'].append(f'{ip_addr} - multicast адрес')
        elif ip_addr.is_reserved:
            dict_ip_addresses['Недоступные узлы'].append(f'{ip_addr} - IETF-зарезервированный адрес')
        elif ip_addr.is_private:
            dict_ip_addresses['Недоступные узлы'].append(f'{ip_addr} - адрес выделен для частных сетей')
        else:
            dict_ip_addresses['Доступные узлы'].append({ip_addr})
    
    return dict_ip_addresses
        

if __name__ == '__main__':
    # result = check_ip(str_ip_list)
    # print(tabulate(result, headers='keys', tablefmt="grid"))
    hosts_ping(str_ip_list)