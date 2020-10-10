""" Скрипт для запуска """

import subprocess

PROCESSES = []

while True:
    action = input('Выберите действие: \n'
                   'q - выход, \n'
                   's - запустить сервер и клиенты, \n'
                   'x - закрыть все процессы\n')

    if action == 'q':
        break
    elif action == 's':
        client_proc_num = input('Введите количество клиентских процессов (до 25): ')
        if client_proc_num.isdigit():
            client_proc_num = int(client_proc_num)
            if 0 < client_proc_num < 26:
                PROCESSES.append(subprocess.Popen('python server.py',
                                                  creationflags=subprocess.CREATE_NEW_CONSOLE))
                for i in range(client_proc_num):
                    PROCESSES.append(subprocess.Popen('python client.py',
                                                      creationflags=subprocess.CREATE_NEW_CONSOLE))
            else:
                print('Слишком много процессов! Введите от 0 до 25 в следующий раз!')
                continue
        else:
            print('Введите число в следующий раз')
            continue
    elif action == 'x':
        while PROCESSES:
            killing_process = PROCESSES.pop()
            killing_process.kill()
