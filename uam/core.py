# -*- coding: utf-8 -*-
import os

from uam.db import db, DB_PATH
from uam.app import App, EntryPoint, Volume, Config


def initialize():
    base_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    db.connect()
    db.create_tables([App, EntryPoint, Volume, Config], safe=True)
    db.close()


def create_app(app_data):
    pass


def list_apps():
    pass


def view_app(source_type, source):
    pass
