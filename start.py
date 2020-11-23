""" Скрипт для запуска """

import subprocess

CLIENT_PROC_DEF = 2
PROCESSES = []

while True:
    action = input('Выберите действие: \n'
                   'q - выход, \n'
                   's - запустить сервер, \n'
                   'c - запустить клиенты, \n'
                   'x - закрыть все процессы\n')

    if action == 'q':
        break
    elif action == 's':
        PROCESSES.append(subprocess.Popen('python server.py',
                                          creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif action == 'c':
        client_num = input('Введите количество клиентов ( по умолчанию - 2 ): ')
        if not client_num:
            client_num = CLIENT_PROC_DEF
        elif client_num.isdigit():
            client_num = int(client_num)
        else:
            print('Введите число в следующий раз')
            continue

        for i in range(client_num):
            user_name = f'cli_{i}'
            PROCESSES.append(subprocess.Popen(f'python client.py -u {user_name}',
                                              creationflags=subprocess.CREATE_NEW_CONSOLE))

    elif action == 'x':
        while PROCESSES:
            killing_process = PROCESSES.pop()
            killing_process.kill()
