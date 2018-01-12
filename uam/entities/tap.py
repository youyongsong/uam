import re
import logging

from uam.entities.exceptions import AliasConflict, AddressConflict

from uam.settings import BUILTIN_TAPS


logger = logging.getLogger(__name__)


def complete_shorten_address(address):
    shorten_pattern = re.compile(r"^[\w\-_\.]+/[\w\-_\.]+$")
    if shorten_pattern.match(address):
        return f'git@github.com:{address}.git'
    return address


def get_address_by_alias(alias, taps):
    return [
        t["address"] for t in taps if t["alias"] == alias
    ][0]


def validiate_new_tap(alias, address):
    if alias in [t["alias"] for t in BUILTIN_TAPS]:
        error = AliasConflict(alias)
        logger.error(error.message)
        raise error
    if address in [t["address"] for t in BUILTIN_TAPS]:
        error = AddressConflict(address)
        logger.error(error.message)
        raise error
    return True


def build_sorted_taps(external_taps):
    builtin_taps = BUILTIN_TAPS
    return sorted(builtin_taps + external_taps,
                  key=lambda k: k["priority"], reverse=True)


def is_tap_builtin(alias):
    for t in BUILTIN_TAPS:
        if alias == t["alias"]:
            return True
    return False