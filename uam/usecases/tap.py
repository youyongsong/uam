import logging
import os

from uam.settings import TAP_PATH
from uam.usecases.exceptions import TapAddConflict, TapRemoveBuiltin, TapRemoveNotFound
from uam.entities.tap import (validiate_new_tap, complete_shorten_address,
                              get_address_by_alias, build_sorted_taps,
                              is_tap_builtin)
from uam.entities.exceptions import tap as tap_excs


logger = logging.getLogger(__name__)


def add_tap(SystemGateway, DatabaseGateway, alias, address, priority=0):
    logger.info("checking if tap already existed ...")
    try:
        validiate_new_tap(alias, address)
    except tap_excs.AliasConflict as error:
        logger.error(error.message)
        raise TapAddConflict(error.alias)
    except tap_excs.AddressConflict as error:
        logger.error(error.message)
        raise TapAddConflict(error.address)

    try:
        DatabaseGateway.valid_tap_conflict(alias, address)
    except DatabaseGateway.TapAliasConflict as error:
        raise TapAddConflict(error.alias)
    except DatabaseGateway.TapAddressConflict as error:
        raise TapAddConflict(error.address)

    address = complete_shorten_address(address)
    logger.info(f"cloning repo {address} ...")
    SystemGateway.clone_repo(TAP_PATH, alias, address)
    logger.info(f"storing tap data into database ...")
    DatabaseGateway.store_tap({
        "alias": alias, "address": address, "priority": priority
    })


def remove_tap(SystemGateway, DatabaseGateway, alias):
    logging.info("checking if tap exists ...")
    if is_tap_builtin(alias):
        error = TapRemoveBuiltin(alias)
        logger.error(error.help_text)
        raise error
    if not DatabaseGateway.tap_exists(alias):
        error = TapRemoveNotFound(alias)
        logger.error(error.help_text)
        raise error

    target_path = os.path.join(TAP_PATH, alias)
    logger.info(f"remoing repo from {target_path} ...")
    SystemGateway.remove_repo(target_path)

    logger.info(f"deleting tap from database ...")
    DatabaseGateway.delete_tap(alias)


def list_taps(DatabaseGateway):
    logger.info("querying all taps from database ...")
    external_taps = DatabaseGateway.list_taps()
    return build_sorted_taps(external_taps)


def update_tap(SystemGateway, DatabaseGateway, alias=None):
    if not alias:
        for t in list_taps(DatabaseGateway):
            update_tap(SystemGateway, DatabaseGateway, alias=t['alias'])

    address = get_address_by_alias(alias, list_taps(DatabaseGateway))
    git_addr = complete_shorten_address(address)
    repo_path = os.path.join(TAP_PATH, alias)
    logger.info(f'updating repo {alias} from {git_addr} ...')
    SystemGateway.update_repo(repo_path, git_addr)