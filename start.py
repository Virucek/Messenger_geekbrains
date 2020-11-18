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
        client_num = input('Введите количество клиентов (до 25): ')
        if client_num.isdigit():
            client_num = int(client_num)
            if 0 < client_num < 26 and 0 < client_num < 26:
                PROCESSES.append(subprocess.Popen('python server.py',
                                                  creationflags=subprocess.CREATE_NEW_CONSOLE))
                for i in range(client_num):
                    user_name = f'cli_{i}'
                    PROCESSES.append(subprocess.Popen(f'python client.py -u {user_name}',
                                                      creationflags=subprocess.CREATE_NEW_CONSOLE))
            else:
                print('Слишком мало/много процессов! Введите от 1 до 25 в следующий раз!')
                continue
        else:
            print('Введите число в следующий раз')
            continue
    elif action == 'x':
        while PROCESSES:
            killing_process = PROCESSES.pop()
            killing_process.kill()
