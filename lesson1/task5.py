"""
5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и 
преобразовать результаты из байтовового в строковый тип 
на кириллице.
"""

import subprocess
import chardet

args = ['ping', 'yandex.ru']
subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)


def detect_encoding(bytes):
    return chardet.detect(bytes)['encoding']


for line in subproc_ping.stdout:
    detected_encoding = detect_encoding(line)
    print('encoded: ', detected_encoding)
    
    line_utf8 = line.decode(detected_encoding).encode(encoding='utf-8')
    print('encoded again in UTF-8')
    print(line_utf8.decode(encoding='utf-8'))