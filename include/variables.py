""" Переменные константные """
# Default server port
DEFAULT_PORT = 7777
# Default server IP Host
DEFAULT_HOST = '127.0.0.1'
# Maximum connections, processing by server at one time
MAX_CONNECTIONS = 5
# Maximum TCP package size
MAX_PACKAGE_SIZE = 2048
# Default encoding
ENCODING = 'utf-8'
# Default log level
LOG_LEVEL = 'DEBUG'
# Server Database
SERVER_DATABASE = 'sqlite:///server.db3'


# Supporting server commands
HELP = 'help'
EXIT = 'exit'
USERS = 'users'
ACTIVE = 'active'
HISTORY = 'history'

# supporting variables
EXIT_F = '!quit'
GET_CONTACTS_F = '!contacts'
ADD_CONTACT_F = '!add'
REMOVE_CONTACT_F = '!del'
HELP_F = '!help'
GET_USERS_F = '!users'
REFRESH_F = '!refresh'

CLIENT_COMMANDS = (EXIT_F, GET_CONTACTS_F, ADD_CONTACT_F, REMOVE_CONTACT_F, HELP_F, GET_USERS_F, REFRESH_F)

# JMI protocol fields
ACTION = 'action'
TIME = 'time'
TYPE = 'type'
USER = 'user'
ACCOUNT_NAME = 'account_name'
STATUS = 'status'
USER_LOGIN = 'user_login'
USER_ID = 'user_id'
PASSWORD = 'password'
PUBLIC_KEY = 'public_key'

NOT_LOGGED_USER = 'Anonymous'
# Actions
PRESENCE = 'presence'
PROBE = 'probe'
MSG = 'msg'
QUIT = 'quit'
AUTHENTICATE = 'authenticate'
JOIN = 'join'
LEAVE = 'leave'
GET_CONTACTS = 'get_contacts'
ADD_CONTACT = 'add_contact'
REMOVE_CONTACT = 'del_contact'
GET_USERS = 'get_users'
GET_PUBLIC_KEY = 'get_public_key'


EXIT = 'exit'

FROM = 'from'
TO = 'to'
MESSAGE = 'message'

DATA = 'dataxxx'
KEY = 'key'

RESPONSE = 'response'
ALERT = 'alert'

RESPCODE_OK = 200
RESPONSE_OK_TEXT = 'OK'

RESPCODE_ACCEPTED = 202

RESPCODE_BAD_REQ = 400
RESPONSE_BAD_REQUEST_TEXT = 'Bad Request'

RESPCODE_SERVER_ERROR = 500

RESPCODE_AUTH_REQUIRED = 511