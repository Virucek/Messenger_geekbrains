Include package
=================================================

Пакет общих утилит, использующихся в разных модулях проекта.

decorators.py
---------------

.. automodule:: include.decorators
	:members:

descriptors.py
---------------------

.. autoclass:: include.descriptors.Port
    :members:

.. autoclass:: include.descriptors.IpAddress
    :members:

errors.py
---------------------

.. autoclass:: include.errors.ServerError
   :members:


utils.py
---------------------

include.utils. **get_message** (client)


    Функция получения сообщения из сокета.
    Декодирует сообщение, десериализирует json, возвращает словарь

include.utils. **send_message** (socket, message)


	Функция отправки сообщения в сокет, его сериализация в json и кодирование
    :param socket: сокет, куда отправлять сообщение
    :param message: словарь сообщения
    :return: В случае успеха - ничего, иначе - ValueError


variables.py
---------------------

Содержит разные глобальные переменные проекта.

protocol.py
---------------------

Содержит шаблоны сообщений используемого протокола JIM.
