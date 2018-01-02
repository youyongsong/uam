import json

from peewee import (Model, ForeignKeyField, CharField,
                    TextField, BooleanField, IntegerField)

from uam.settings import db


APP_SOURCE_TYPES = (
    ('local', 'local'),
    ('tap', 'tap')
)


class JSONField(TextField):

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        return json.loads(value)


class Tap(Model):
    alias = CharField(max_length=128, unique=True)
    address = CharField(max_length=2048, unique=True)
    priority = IntegerField(default=0)

    class Meta:
        database = db


class App(Model):
    name = CharField(max_length=64)
    source_type = CharField(max_length=32, choices=APP_SOURCE_TYPES)
    tap_alias = CharField(max_length=128)
    version = CharField(max_length=128)
    description = TextField(default='')
    image = TextField()
    environments = JSONField(default='{}')
    shell = CharField(max_length=128, default='sh')
    pinned = BooleanField(default=False)
    pinned_version = CharField(max_length=128)

    class Meta:
        database = db
        indexes = (
            (("name", "version", "pinned"), True),
        )


class EntryPoint(Model):
    alias = CharField(max_length=512)
    app = ForeignKeyField(App, related_name='entrypoints')
    container_entrypoint = CharField(max_length=512)
    container_arguments = CharField(max_length=512, default='')
    enabled = BooleanField(default=True)

    class Meta:
        database = db
        indexes = (
            (('alias', 'app'), True),
        )


class Volume(Model):
    name = CharField(primary_key=True)
    app = ForeignKeyField(App, related_name='volumes')
    path = TextField()

    class Meta:
        database = db


class Config(Model):
    app = ForeignKeyField(App, related_name='configs')
    host_path = TextField()
    container_path = TextField()

    class Meta:
        database = db
        indexes = (
            (('app', 'container_path'), True),
        )
