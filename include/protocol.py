""" Описание форматов сообщения протокола JIM """

from include.variables import *

# Шаблон Presence сообщения протокола JIM
PRESENCE_MSG_CLIENT = {
    ACTION: PRESENCE,
    TIME: None,
    TYPE: STATUS,
    USER: {
        ACCOUNT_NAME: NOT_LOGGED_USER,
        STATUS: None,
        PUBLIC_KEY: None,
    }
}
# Шаблон успешного ответа
SERVER_RESPONSE_OK = {
    RESPONSE: RESPCODE_OK,
    ALERT: RESPONSE_OK_TEXT
}
# Шаблон неуспешного ответа (400, bad request)
SERVER_RESPONSE_BAD_REQUEST = {
    RESPONSE: RESPCODE_BAD_REQ,
    ALERT: RESPONSE_BAD_REQUEST_TEXT
}
# Шаблон неуспешной ответа (500, ошибка сервера)
SERVER_RESPONSE_SERVER_ERROR = {
    RESPONSE: RESPCODE_SERVER_ERROR,
}

# Шаблон сообщения в общий чат
CHAT_MSG_CLIENT = {
    ACTION: MSG,
    TIME: None,
    FROM: None,
    MESSAGE: None
}

# Шаблон сообщения пользователю
CHAT_USER_MSG_CLIENT = {
    ACTION: MSG,
    TIME: None,
    FROM: None,
    TO: None,
    MESSAGE: None
}

# Шаблон сообщения выхода из чата
EXIT_MSG_CLIENT = {
    ACTION: EXIT,
    TIME: None,
    FROM: None
}


# Шаблон запроса списка контактов
GET_USER_CONTACTS_MSG = {
    ACTION: GET_CONTACTS,
    TIME: None,
    USER_LOGIN: None
}

# Шаблон успешного ответа на get запрос (202)
RESPONSE_USERS_CONTACTS_MSG = {
    RESPONSE: RESPCODE_ACCEPTED,
    ALERT: None,
}

ADD_USER_CONTACT_MSG = {
    ACTION: ADD_CONTACT,
    USER_ID: None,
    TIME: None,
    USER_LOGIN: None,
}

REMOVE_USER_CONTACT_MSG = {
    ACTION: REMOVE_CONTACT,
    USER_ID: None,
    TIME: None,
    USER_LOGIN: None,
}

# Шаблон запроса списка пользователей
GET_USERS_MSG = {
    ACTION: GET_USERS,
    TIME: None,
    USER_LOGIN: None
}

# Шаблон запроса для аутентификации от клиента
AUTHENTICATE_MSG = {
    ACTION: AUTHENTICATE,
    TIME: None,
    USER: {
        ACCOUNT_NAME: None,
        PASSWORD: None,
    }
}

# Шаблон запроса пароля для аутентификации от сервера
AUTHENTICATE_REQUIRED_MSG = {
    RESPONSE: RESPCODE_AUTH_REQUIRED,
    DATA: None,
}

# Шаблон запроса публичного ключа пользователя
GET_PUBKEY_REQ_MSG = {
    ACTION: GET_PUBLIC_KEY,
    TIME: None,
    USER: None,
}

# Шаблон ответа на запрос с публичным ключом от сервера
PUBKEY_RESP = {
    RESPONSE: RESPCODE_AUTH_REQUIRED,
    KEY: None,
}