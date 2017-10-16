# -*- coding: utf-8 -*-
import json

from peewee import (Model, ForeignKeyField, CharField,
                    TextField, BooleanField)

from uam.db import db


APP_SOURCE_TYPES = (
    ('file', 'File'),
    ('url', 'URL'),
    ('gh', 'Github'),
    ('bt', 'Bitbucket'),
    ('registry', 'Registry')
)

APP_STATUS = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('semi-active', 'Semi Active')
)


class JSONField(TextField):

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        return json.loads(value)


class App(Model):
    source_type = CharField(max_length=32, choices=APP_SOURCE_TYPES)
    source = TextField()
    version = CharField(max_length=128)
    description = TextField(default='')
    image = TextField()
    environments = JSONField(default='{}')
    status = CharField(max_length=24)

    class Meta:
        database = db
        indexes = (
            (('source_type', 'source'), True),
        )


class EntryPoint(Model):
    alias = CharField(max_length=512)
    app = ForeignKeyField(App, related_name='entrypoints', unique=True)
    container_entrypoint = CharField(max_length=512)
    container_arguments = CharField(max_length=512, default='')
    enabled = BooleanField()

    class Meta:
        database = db


class Volume(Model):
    name = CharField(primary_key=True)
    app = ForeignKeyField(App, related_name='volumes', unique=True)
    path = TextField()

    class Meta:
        database = db


class Config(Model):
    app = ForeignKeyField(App, related_name='configs', unique=True)
    host_path = TextField()
    container_path = TextField()

    class Meta:
        database = db
