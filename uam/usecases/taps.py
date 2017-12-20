import logging
import os

from uam.settings import TAPS_PATH
from uam.usecases.exceptions import TapsAddConflict
from uam.entities.taps import (validiate_new_taps, complete_shorten_address,
                               get_address_by_alias, build_sorted_taps,
                               is_taps_builtin)
from uam.entities.exceptions import taps as taps_excs


logger = logging.getLogger(__name__)


def add_taps(SystemGateway, DatabaseGateway, alias, address, priority=0):
    logger.info("checking if taps already existed ...")
    try:
        validiate_new_taps(alias, address)
    except taps_excs.AliasConflict as error:
        logger.error(error.message)
        raise TapsAddConflict(error.alias)
    except taps_excs.AddressConflict as error:
        logger.error(error.message)
        raise TapsAddConflict(error.address)

    try:
        DatabaseGateway.valid_taps_conflict(alias, address)
    except DatabaseGateway.TapsAliasConflict as error:
        raise TapsAddConflict(error.alias)
    except DatabaseGateway.TapsAddressConflict as error:
        raise TapsAddConflict(error.address)

    address = complete_shorten_address(address)
    logger.info(f"cloning repo {address} ...")
    SystemGateway.clone_repo(TAPS_PATH, alias, address)
    logger.info(f"storing taps data into database ...")
    DatabaseGateway.store_taps({
        "alias": alias, "address": address, "priority": priority
    })


def remove_taps(SystemGateway, DatabaseGateway, alias):
    logging.info("checking if taps exists ...")
    if is_taps_builtin(alias):
        error = taps_excs.TapsRemoveBuiltin(alias) 
        logger.error(error.help_text)
        raise error
    if not DatabaseGateway.taps_exists(alias):
        error = taps_excs.TapsRemoveNotFound(alias)
        logger.error(error.help_text)
        raise error

    target_path = os.path.join(TAPS_PATH, alias)
    logger.info(f"remoing repo from {target_path} ...")
    SystemGateway.remove_repo(target_path)

    logger.info(f"deleting taps from database ...")
    DatabaseGateway.delete_taps(alias)


def list_taps(DatabaseGateway):
    logger.info("querying all taps from database ...")
    external_taps = DatabaseGateway.list_taps()
    return build_sorted_taps(external_taps)


def update_taps(SystemGateway, DatabaseGateway, alias=None):
    if not alias:
        for t in all_taps:
            update_taps(alias=t['alias'])

    address = get_address_by_alias(alias, list_taps(DatabaseGateway))
    git_addr = complete_shorten_address(address)
    repo_path = os.path.join(TAPS_PATH, alias)
    logger.info(f'updating repo {alias} from {git_addr} ...')
    SystemGateway.update_repo(repo_path, git_addr)