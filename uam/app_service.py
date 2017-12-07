# -*- coding: utf-8 -*-
import logging
import os
import stat
import sys
import subprocess
import uuid

import docker
import yaml
from jinja2 import Template

from uam.settings import db, DB_PATH, BIN_PATH, TEMP_PATH, docker_client
from uam.utils import dict_add

from .app import App, EntryPoint, Volume, Config
from .app_core import (create_app, get_conflicted_entrypoints,
                       delete_app, get_active_entrypoints, get_volumes,
                       get_app, list_entrypoints)
from .exceptions import (EntryPointConflict, AppSourceNotExist,
                         MainfestInvalidYaml)


logger = logging.getLogger(__name__)


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


def info_app(app_name):
    app_data = load_app_data(app_name)
    source_type, source = app_data['source_type'], app_data['source']
    return get_app(db, source_type, source)


def uninstall_app(app_name):
    app_data = load_app_data(app_name)
    source_type, source = app_data['source_type'], app_data['source']
    active_entrypoints = get_active_entrypoints(db, source_type, source)
    volumes = get_volumes(db, source_type, source)
    delete_app(db, source_type, source)
    delete_wrappers(active_entrypoints)
    delete_volumes(volumes)


def exec_shell(app_name, commands=''):
    app_data = load_app_data(app_name)
    source_type, source = app_data['source_type'], app_data['source']
    app = get_app(db, source_type, source)
    wrapper_path = create_shell_wrapper(app)
    try:
        subprocess.run(f'{sys.executable} {wrapper_path} {commands}', shell=True)
    finally:
        logger.debug(f'Removing shell wrapper f{wrapper_path}')
        try:
            os.remove(wrapper_path)
        except Exception as exc:
            logger.debug(f'Failed to remove {wrapper_path}: {exc}')


def retrieve_alias():
    return list_entrypoints(db)


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
        target_path = os.path.join(BIN_PATH, entry.alias)
        with open(target_path, 'w') as f_handler:
            content = template.render({
                'app': app,
                'entrypoint': entry,
                'volumes': app.volumes,
                'configs': app.configs,
                'python_path': sys.executable
            })
            f_handler.write(content)

        st = os.stat(target_path)
        os.chmod(target_path, st.st_mode | stat.S_IEXEC)


def create_shell_wrapper(app):
    with open(os.path.join(os.path.dirname(__file__),
                           'excutable_app.tmpl'), 'r') as f_handler:
        template = Template(f_handler.read())
    target_path = os.path.join(TEMP_PATH, f'uam-shell-{uuid.uuid4()}')
    logger.debug(f'Creating shell wrapper {target_path}')

    with open(target_path, 'w') as f_handler:
        content = template.render({
            'app': app,
            'entrypoint': {'container_entrypoint': app.shell},
            'volumes': app.volumes,
            'configs': app.configs,
            'python_path': sys.executable
        })
        f_handler.write(content)

    return target_path


def delete_wrappers(entrypoints):
    if not os.path.exists(BIN_PATH):
        return

    for entry_name in entrypoints:
        target_path = os.path.join(BIN_PATH, entry_name)
        logger.info('Removing wrapper {} from {}...'.format(entry_name,
                                                            target_path))
        try:
            os.remove(target_path)
        except FileNotFoundError:
            logger.info('{} not found'.format(target_path))
        else:
            logger.info('{} removed.'.format(target_path))


def delete_volumes(volumes):
    for v in volumes:
        logger.info('Removing volume {}...'.format(v))
        try:
            volume = docker_client.volumes.get(v)
        except docker.errors.NotFound:
            logger.warning('volume {} not found.'.format(v))
        else:
            volume.remove()
            logger.info('{} removed.'.format(v))
