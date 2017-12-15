import logging

from uam.settings import BUILTIN_TAPS, TAPS_PATH

import re
import os
import subprocess
import shutil
from uam.adapters.database.models import Taps
from .taps_exceptions import *


logger = logging.getLogger(__name__)


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
        # raise TapsInvalid(err_msg)
        raise TapsAddError()

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
        # raise TapsAddError(err_msg, code='git_clone_error')
        raise TapsAddError()
    finally:
        os.chdir(curdir)

    try:
        logger.info('storing taps data into local db ...')
        Taps.create(**{'alias': alias, 'address': address,
                       'priority': priority})
    except Exception as exc:
        err_msg = f'failed to store taps data, reason: {exc}'
        logger.error(err_msg)
        # raise TapsAddError(err_msg, code='save_database_error')
        raise TapsAddError()


def remove_taps(alias):
    err_msg = ''
    if alias in [t['alias'] for t in BUILTIN_TAPS]:
        err_msg = f'{alias} is builtin taps, can not be deleted.'
    elif not Taps.select().where(Taps.alias == alias):
        err_msg = f'{alias} does not exist.'
    if err_msg:
        logger.warning(err_msg)
        # raise TapsRemoveInvalid(err_msg)
        raise TapsRemoveError()

    target_path = os.path.join(TAPS_PATH, alias)
    try:
        shutil.rmtree(target_path)
    except Exception as exc:
        err_msg = f'failed to delete {target_path}, reason: {exc}'
        logger.error(err_msg)
        # raise TapsRemoveError(err_msg, code='delete_repo_error')
        raise TapsRemoveError()

    try:
        taps = Taps.get(Taps.alias == alias)
        taps.delete_instance()
    except Exception as exc:
        err_msg = f'faield to delete insatance in database.'
        # raise TapsRemoveError(err_msg, code='delete_instance_error')
        raise TapsRemoveError()


def list_taps(DatabaseGateway):
    builtin_taps = BUILTIN_TAPS
    external_taps = DatabaseGateway.list_taps()
    return sorted(builtin_taps+external_taps,
                  key=lambda k: k['priority'], reverse=True)


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
            # raise MultiTapsUpdateError(errors)
            raise TapsUpdateError()
        return

    if alias not in [t['alias'] for t in all_taps]:
        err_msg = f'{alias} taps does not exist.'
        logger.warning(err_msg)
        # raise TapsUpdateInvalid(err_msg)
        raise TapsUpdateErrorn()

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
        # raise TapsUpdateError(err_msg, code='pull_repo_error')
        raise TapsUpdateError


def get_abs_address(address):
    short_pattern = re.compile(r"^[\w\-_\.]+/[\w\-_\.]+$")
    if short_pattern.match(address):
        return f'git@github.com:{address}.git'
    return address
