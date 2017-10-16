# -*- coding: utf-8 -*-
from peewee import SqliteDatabase


DB_PATH = "/usr/local/uam/data.db"
db = SqliteDatabase(DB_PATH)
