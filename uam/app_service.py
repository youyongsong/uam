# -*- coding: utf-8 -*-
import logging
import os
import stat
import shutil
import sys
import subprocess
import uuid
import re

import docker
import yaml
from jinja2 import Template

from uam.settings import (db, UAM_PATH, DB_PATH, BIN_PATH, TEMP_PATH,
                          docker_client, CONTAINER_META_LABELS,
                          GLOBAL_NETWORK_NAME, TAPS_PATH, BUILTIN_TAPS)
from uam.utils import dict_add

from .app import Taps, App, EntryPoint, Volume, Config
from .app_core import (create_app, get_conflicted_entrypoints,
                       delete_app, get_active_entrypoints, get_volumes,
                       get_app, list_entrypoints)
from .exceptions import *


logger = logging.getLogger(__name__)


def initialize():
    if not os.path.exists(UAM_PATH):
        logger.info(f"creating uam's home path {UAM_PATH} ...")
        os.makedirs(UAM_PATH)

    logger.info("initializing database ...")
    db.create_tables([Taps, App, EntryPoint, Volume, Config], safe=True)

    logger.info('downloading builtin taps ...')
    curdir = os.path.abspath(os.curdir)
    try:
        os.chdir(TAPS_PATH)
        for t in BUILTIN_TAPS:
            if os.path.exists(os.path.join(TAPS_PATH, t['alias'])):
                continue
            abs_address = get_abs_address(t['address'])
            logger.info(f"cloning taps {abs_address} ...")
            command = f"git clone --depth 1 {abs_address} {t['alias']}"
            logger.debug(command)
            subprocess.run(command, shell=True, check=True)
    finally:
        os.chdir(curdir)

    try:
        docker_client.networks.get(GLOBAL_NETWORK_NAME)
    except docker.errors.NotFound:
        logger.info(f'creating docker network {GLOBAL_NETWORK_NAME} ...')
        docker_client.networks.create(GLOBAL_NETWORK_NAME, driver="bridge",
                                      labels=CONTAINER_META_LABELS)


def add_taps(alias, address, priority=0):
    err_msg = ''
    if alias in [t['alias'] for t in BUILTIN_TAPS]:
        err_msg = (f'{alias} in used by builtin taps, please try another '
                   'alias name.')
    elif address in [t['address'] for t in BUILTIN_TAPS]:
        err_msg = f'{address} is builtin taps, you do not need to add it.'
    elif Taps.select().where(Taps.alias == alias):
        err_msg = f'{alias} is already used, please try another alias name.'
    elif Taps.select().where(Taps.address == address):
        err_msg = (f'{address} is already added before, you can not add '
                   'it again.')
    if err_msg:
        logger.warning(err_msg)
        raise TapsInvalid(err_msg)

    abs_address = get_abs_address(address)
    curdir = os.path.abspath(os.curdir)
    os.chdir(TAPS_PATH)
    try:
        logger.info(f'cloning taps {abs_address} ...')
        command = f'git clone --depth 1 {abs_address} {alias}'
        logger.debug(command)
        subprocess.run(command, shell=True, check=True)
    except Exception as exc:
        err_msg = f'{abs_address} clone failed: {exc}'
        logger.error(err_msg)
        raise TapsAddError(err_msg, code='git_clone_error')
    finally:
        os.chdir(curdir)

    try:
        logger.info('storing taps data into local db ...')
        Taps.create(**{'alias': alias, 'address': address,
                       'priority': priority})
    except Exception as exc:
        err_msg = f'failed to store taps data, reason: {exc}'
        logger.error(err_msg)
        raise TapsAddError(err_msg, code='save_database_error')


def remove_taps(alias):
    err_msg = ''
    if alias in [t['alias'] for t in BUILTIN_TAPS]:
        err_msg = f'{alias} is builtin taps, can not be deleted.'
    elif not Taps.select().where(Taps.alias == alias):
        err_msg = f'{alias} does not exist.'
    if err_msg:
        logger.warning(err_msg)
        raise TapsRemoveInvalid(err_msg)

    target_path = os.path.join(TAPS_PATH, alias)
    try:
        shutil.rmtree(target_path)
    except Exception as exc:
        err_msg = f'failed to delete {target_path}, reason: {exc}'
        logger.error(err_msg)
        raise TapsRemoveError(err_msg, code='delete_repo_error')

    try:
        taps = Taps.get(Taps.alias == alias)
        taps.delete_instance()
    except Exception as exc:
        err_msg = f'faield to delete insatance in database.'
        raise TapsRemoveError(err_msg, code='delete_instance_error')


def list_taps():
    taps_list = BUILTIN_TAPS.copy()
    for t in Taps.select():
        taps_list.append({
            'alias': t.alias,
            'address': t.address,
            'priority': t.priority
        })
    return sorted(taps_list, key=lambda k: k['priority'], reverse=True)


def update_taps(alias=None):
    all_taps = list_taps()

    if not alias:
        for t in all_taps:
            errors = []
            try:
                update_taps(alias=t['alias'])
            except (TapsUpdateInvalid, TapsUpdateError) as exc:
                errors.append(exc)
        if errors:
            raise MultiTapsUpdateError(errors)
        return

    if alias not in [t['alias'] for t in all_taps]:
        err_msg = f'{alias} taps does not exist.'
        logger.warning(err_msg)
        raise TapsUpdateInvalid(err_msg)

    logger.info(f'updating taps {alias} ...')
    address = [t['address'] for t in all_taps if t['alias'] == alias][0]
    abs_address = get_abs_address(address)
    cur_dir = os.path.abspath(os.curdir)
    alias_path = os.path.join(TAPS_PATH, alias)
    os.chdir(alias_path)
    try:
        subprocess.run(f'git pull {abs_address}', shell=True, check=True)
    except Exception as exc:
        err_msg = f'git pull {abs_address} failed, reason: {exc}'
        logger.error(err_msg)
        raise TapsUpdateError(err_msg, code='pull_repo_error')


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
                'python_path': sys.executable,
                'meta_labels': CONTAINER_META_LABELS,
                'network': GLOBAL_NETWORK_NAME,
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
            'python_path': sys.executable,
            'meta_labels': CONTAINER_META_LABELS,
            'network': GLOBAL_NETWORK_NAME,
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


def get_abs_address(address):
    short_pattern = re.compile(r"^[\w\-_\.]+/[\w\-_\.]+$")
    if short_pattern.match(address):
        return f'git@github.com:{address}.git'
    return address
