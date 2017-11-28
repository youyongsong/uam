# -*- coding: utf-8 -*-
import os
import stat

import yaml
from jinja2 import Template

from uam.settings import db, DB_PATH, BIN_PATH
from uam.utils import dict_add

from .app import App, EntryPoint, Volume, Config
from .app_core import create_app, get_conflicted_entrypoints
from .exceptions import (EntryPointConflict, AppSourceNotExist,
                         MainfestInvalidYaml)


def initialize():
    base_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    db.create_tables([App, EntryPoint, Volume, Config], safe=True)


def install_app(app_name, override_entrypoints=None):
    app_data = load_app_data(app_name)
    app_data['entrypoints'] = [
        dict_add(entry, {'alias': alias})
        for alias, entry in app_data.get('entrypoints', {}).items()
    ]
    if override_entrypoints is None:
        conflicted = get_conflicted_entrypoints(db, app_data['entrypoints'])
        if conflicted:
            raise EntryPointConflict(conflicted)

    app_id = create_app(db, app_data, override_entrypoints)
    create_app_wrapper(App.get(App.id == app_id))


def load_app_data(app_name):
    source_lst = app_name.split('::')
    if len(source_lst) == 1:
        source_type, source = 'registry', source_lst[0]
    else:
        source_type, source = source_lst[:2]
    if source_type == 'file':
        source_path = os.path.abspath(source)
        if not os.path.isfile(source_path):
            raise AppSourceNotExist(source_path)
        with open(source_path, 'r') as f_handler:
            try:
                app_data = yaml.load(f_handler)
            except yaml.error.YAMLError:
                raise MainfestInvalidYaml()
    else:
        raise Exception('Not implemented yet.')
    app_data['source_type'] = source_type
    app_data['source'] = source
    return app_data


def create_app_wrapper(app):
    with open(os.path.join(os.path.dirname(__file__),
                           'excutable_app.tmpl'), 'r') as f_handler:
        template = Template(f_handler.read())
    for entry in app.entrypoints:
        if not os.path.exists(BIN_PATH):
            os.makedirs(BIN_PATH)
        target_path = os.path.join(BIN_PATH, entry.alias)
        with open(target_path, 'w') as f_handler:
            content = template.render({
                'app': app,
                'entrypoint': entry,
                'volumes': app.volumes,
                'configs': app.configs
            })
            f_handler.write(content.encode('utf-8'))

        st = os.stat(target_path)
        os.chmod(target_path, st.st_mode | stat.S_IEXEC)
