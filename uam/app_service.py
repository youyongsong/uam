# -*- coding: utf-8 -*-
import os
import stat

import docker
import daiquiri
import yaml
from jinja2 import Template

from uam.settings import db, DB_PATH, BIN_PATH, docker_client
from uam.utils import dict_add

from .app import App, EntryPoint, Volume, Config
from .app_core import (create_app, get_conflicted_entrypoints,
                       delete_app, get_active_entrypoints, get_volumes)
from .exceptions import (EntryPointConflict, AppSourceNotExist,
                         MainfestInvalidYaml)


logger = daiquiri.getLogger(__name__)


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

    app = create_app(db, app_data, override_entrypoints)
    create_app_wrapper(app)
    return app


def uninstall_app(app_name):
    app_data = load_app_data(app_name)
    source_type, source = app_data['source_type'], app_data['source']
    active_entrypoints = get_active_entrypoints(db, source_type, source)
    volumes = get_volumes(db, source_type, source)
    delete_app(db, source_type, source)
    delete_wrappers(active_entrypoints)
    delete_volumes(volumes)


def load_app_data(app_name):
    source_lst = app_name.split('::')
    if len(source_lst) == 1:
        source_type, source = 'registry', source_lst[0]
    else:
        source_type, source = source_lst[:2]
    if source_type == 'file':
        source = os.path.abspath(source)
        if not os.path.isfile(source):
            raise AppSourceNotExist(source)
        with open(source, 'r') as f_handler:
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


def delete_wrappers(entrypoints):
    if not os.path.exists(BIN_PATH):
        return

    for entry_name in entrypoints:
        target_path = os.path.join(BIN_PATH, entry_name)
        logger.info('Removing wrapper {} from {}...'.format(entry_name,
                                                            target_path))
        os.remove(target_path)
        logger.info('{} was removed.'.format(entry_name))


def delete_volumes(volumes):
    for v in volumes:
        logger.info('Removing volume {}...'.format(v))
        try:
            volume = docker_client.volumes.get(v)
        except docker.errors.NotFound:
            logger.warning('volume {} not found.'.format(v))
        else:
            volume.remove()
            logger.info('{} was removed.'.format(v))
