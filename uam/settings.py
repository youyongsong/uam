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

BIN_PATH = os.path.join(UAM_PATH, 'bin')

docker_client = docker.from_env()


DEBUG = str2bool(os.getenv('UAM_DEBUG', 'false'))


class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        return DEBUG


class RequireDebugFalse(logging.Filter):
    def filter(self, record):
        return not DEBUG


LOG_COLORS = {
    'DEBUG':    'white',
    'INFO':     'white',
    'WARNING':  'yellow',
    'ERROR':    'red',
    'CRITICAL': 'bold_red',
}


LOG_PREFIXS = {
    'DEBUG':    '⚙',
    'INFO':     '⚙',
    'WARNING':  '⚠️',
    'ERROR':    '💢',
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
