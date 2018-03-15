# -*- coding: utf-8 -*-
import logging.config
import os

import docker
from colorlog import ColoredFormatter
from peewee import SqliteDatabase


def str2bool(v):
    return v and v.lower() in ('yes', 'true', 't', '1')


HOME_DIR = os.path.expanduser('~')
UAM_PATH = os.path.join(HOME_DIR, '.uam')
if not os.path.isdir(UAM_PATH):
    os.mkdir(UAM_PATH)

DB_PATH = os.path.join(UAM_PATH, "uam.db")
db = SqliteDatabase(DB_PATH)

TAP_PATH = os.path.join(UAM_PATH, 'taps')
if not os.path.exists(TAP_PATH):
    os.makedirs(TAP_PATH)

BIN_PATH = os.path.join(UAM_PATH, 'bin')
if not os.path.exists(BIN_PATH):
    os.makedirs(BIN_PATH)

TEMP_PATH = os.path.join(UAM_PATH, '.temp')
if not os.path.exists(TEMP_PATH):
    os.makedirs(TEMP_PATH)

VENVS_PATH = os.path.join(UAM_PATH, "venvs")
if not os.path.exists(VENVS_PATH):
    os.makedirs(VENVS_PATH)

UAM_VENV_VAR = "UAM_VENV"
CURRENT_VENV = os.getenv(UAM_VENV_VAR, "")

docker_client = docker.from_env()


DEBUG = str2bool(os.getenv('UAM_DEBUG', 'false'))


BUILTIN_TAPS = [
    {
        'alias': 'core',
        'address': 'youyongsong/uam-core',
        'priority': 10
    }
]
FORMULA_FOLDER_NAME = 'Formula'

FORMULA_EXTENSIONS = ['yaml', 'yml']


CONTAINER_META_LABELS = {
    'provider': 'uam',
    'provider description': 'universal application manager.',
}

GLOBAL_NETWORK_NAME = 'uam_global_network'


class ErrorTypes:
    USER_ERROR = "user_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"


class SourceTypes:
    LOCAL = 'local'
    TAP = 'tap'


class UamBaseException(Exception):
    code = ''
    type = ''
    help_text = ''

    def __init__(self):
        super(UamBaseException, self).__init__(self.help_text)


class UamUnknownError(UamBaseException):
    code = 'unknown_error'
    type = ErrorTypes.UNKNOWN_ERROR
    help_text = 'something wrong unknown happend, error detail is: {}'

    def __init__(self, exc):
        self.help_text = self.help_text.format(exc)
        super(UamUnknownError, self).__init__()


class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        return DEBUG


class RequireDebugFalse(logging.Filter):
    def filter(self, record):
        return not DEBUG


LOG_COLORS = {
    'DEBUG': 'white',
    'INFO': 'white',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red'
}


LOG_PREFIXS = {
    'DEBUG': '⚙',
    'INFO': '⚙',
    'WARNING': '⚠️',
    'ERROR': '💢',
    'CRITICAL': '🚨',
}


class CustomedFormatter(ColoredFormatter):

    def format(self, record):
        message = super(CustomedFormatter, self).format(record)
        prefix = LOG_PREFIXS.get(record.levelname)
        return f'  {prefix}   {message}'


LOGGING = {
    'version': 1,
    'formatters': {
        'prod': {
            '()': CustomedFormatter,
            'format': '%(log_color)s%(message)s',
            'log_colors': LOG_COLORS
        },
        'dev': {
            '()': CustomedFormatter,
            'format': ('%(log_color)s|%(levelname)-8s|%(asctime)-25s'
                       '|%(threadName)-11s|%(name)s:%(lineno)d %(message)s'),
            'log_colors': LOG_COLORS
        }
    },
    'filters': {
        'require-debug-true': {
            '()': RequireDebugTrue
        },
        'require-debug-false': {
            '()': RequireDebugFalse
        },
    },
    'handlers': {
        'console-dev': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'dev',
            'filters': ['require-debug-true']
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'prod',
            'filters': ['require-debug-false']
        }
    },
    'loggers': {
        '': {
            'handlers': ['console-dev', 'console'],
            'level': 'DEBUG' if DEBUG else 'INFO'
        }
    }
}

logging.config.dictConfig(LOGGING)
