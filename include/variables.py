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
# JMI protocol fields
ACTION = 'action'
TIME = 'time'
TYPE = 'type'
USER = 'user'
ACCOUNT_NAME = 'account_name'
STATUS = 'status'
# Actions
PRESENCE = 'presence'
PROBE = 'probe'
MSG = 'msg'
QUIT = 'quit'
AUTHENTICATE = 'authenticate'
JOIN = 'join'
LEAVE = 'leave'

RESPONSE = 'response'
ALERT = 'alert'

RESPONSE_OK = 200
RESPONSE_OK_TEXT = 'OK'

RESPONSE_BAD_REQUEST = 400
RESPONSE_BAD_REQUEST_TEXT = 'Bad Request'

RESPONSE_SERVER_ERROR = 500