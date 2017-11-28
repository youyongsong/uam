# -*- coding: utf-8 -*-
import re

from playhouse.test_utils import test_database
from peewee import SqliteDatabase

from .app import App, EntryPoint, Volume, Config
from .app_core import create_app


test_db = SqliteDatabase(':memory')


def test_create_app():
    with test_database(test_db, (App, EntryPoint, Volume, Config)):
        app_data = {
            'source': '/usr/local/example.yaml',
            'source_type': 'file',
            'image': 'index.alauda.cn/library/python:2',
            'environments': {'a': 1, 'b': 2},
            'version': '0.0.1',
            'entrypoints': {
                'python': {
                    'container_entrypoint': '/usr/local/bin/python'
                },
                'pip': {
                    'container_entrypoint': '/usr/local/bin/pip'
                }
            },
            'volumes': [{'path': '/usr/local/bin'},
                        {'path': '/usr/local/lib/python3.6/site-packages'}],
            'configs': [
                {
                    'host_path': '$HOME/.pip',
                    'container_path': '/root/.pip'
                }
            ]
        }
        app_id = create_app(test_db, app_data)
        app = App.get(App.id == app_id)
        assert app.status == 'active'
        assert app.environments == {'a': 1, 'b': 2}
        assert len(app.configs) == 1
        assert app.configs[0].host_path == '$HOME/.pip'
        assert app.configs[0].container_path == '/root/.pip'
        assert len(app.entrypoints) == 2
        for e in app.entrypoints:
            assert e.alias in ('python', 'pip')
            assert e.enabled is True
            assert e.container_arguments == ''
            if e.alias == 'python':
                assert e.container_entrypoint == '/usr/local/bin/python'
            else:
                assert e.container_entrypoint == '/usr/local/bin/pip'
        assert len(app.volumes) == 2
        for v in app.volumes:
            assert re.match('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', v.name)


def test_create_app_conflict():
    pass


def test_create_app_override():
    pass


def test_create_app_not_override():
    pass
