import logging


from uam.settings import (db, docker_client, BUILTIN_TAPS,
                          UAM_PATH, TAPS_PATH, GLOBAL_NETWORK_NAME)

import docker
from uam.adapters.database.models import (Taps, App, EntryPoint,
                                          Volume, Config)
import subprocess
import os


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


def get_abs_address(address):
    short_pattern = re.compile(r"^[\w\-_\.]+/[\w\-_\.]+$")
    if short_pattern.match(address):
        return f'git@github.com:{address}.git'
    return address
