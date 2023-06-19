
import os
import subprocess
import time

PROCESS = []

while True:
    ACTION = input('Выберите действие: q - выход, '
                   's - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break
        
    elif ACTION == 's':
        catalog = os.getcwd()
        p = f'python3 "{catalog}/server.py"'
        PROCESS.append(subprocess.Popen(['konsole', '-e', p]))
        print(p)
        time.sleep(0.1)
        for i in range(5):
            p = f'python3 "{catalog}/client.py" -n user{i}'
            PROCESS.append(subprocess.Popen(['konsole', '-e', p]))
            print(p)
            time.sleep(0.1)
            
    elif ACTION == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            VICTIM.kill()