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

#supporting variables
EXIT_F = 'q!'


# JMI protocol fields
ACTION = 'action'
TIME = 'time'
TYPE = 'type'
USER = 'user'
ACCOUNT_NAME = 'account_name'
STATUS = 'status'

NOT_LOGGED_USER = 'Anonymous'
# Actions
PRESENCE = 'presence'
PROBE = 'probe'
MSG = 'msg'
QUIT = 'quit'
AUTHENTICATE = 'authenticate'
JOIN = 'join'
LEAVE = 'leave'

EXIT = 'exit'

FROM = 'from'
TO = 'to'
MESSAGE = 'message'

RESPONSE = 'response'
ALERT = 'alert'

RESPCODE_OK = 200
RESPONSE_OK_TEXT = 'OK'

RESPCODE_BAD_REQ = 400
RESPONSE_BAD_REQUEST_TEXT = 'Bad Request'

RESPCODE_SERVER_ERROR = 500