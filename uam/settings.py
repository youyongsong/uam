# -*- coding: utf-8 -*-
import logging

import daiquiri
import docker
from peewee import SqliteDatabase


daiquiri.setup(level=logging.INFO)


DB_PATH = "/usr/local/uam/data.db"
db = SqliteDatabase(DB_PATH)

BIN_PATH = '/usr/local/uam/bin/'

docker_client = docker.from_env()
