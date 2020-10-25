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
        client_write_num = input('Введите количество пишущих клиентов (до 25): ')
        client_read_num = input('Введите количество клиентов, кот. могут только читать (до 25): ')
        if client_write_num.isdigit() and client_read_num.isdigit():
            client_write_num, client_read_num = int(client_write_num), int(client_read_num)
            if 0 < client_write_num < 26 and 0 < client_read_num < 26:
                PROCESSES.append(subprocess.Popen('python server.py',
                                                  creationflags=subprocess.CREATE_NEW_CONSOLE))
                for i in range(client_write_num):
                    user_name = f'cli_wr_{i}'
                    PROCESSES.append(subprocess.Popen(f'python client.py -m write -u {user_name}',
                                                      creationflags=subprocess.CREATE_NEW_CONSOLE))
                for i in range(client_read_num):
                    user_name = f'cli_re_{i}'
                    PROCESSES.append(subprocess.Popen(f'python client.py -m read -u {user_name}',
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
