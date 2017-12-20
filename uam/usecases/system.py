import logging


from uam.settings import (BUILTIN_TAPS, UAM_PATH, TAPS_PATH,
                          GLOBAL_NETWORK_NAME, CONTAINER_META_LABELS)
from uam.entities.taps import complete_shorten_address


logger = logging.getLogger(__name__)


def initialize(SystemGateway, DatabaseGateway, DockerServiceGateway):
    logger.info("checking uam's home path...")
    SystemGateway.assure_folder(UAM_PATH)

    logger.info("checking database ...")
    DatabaseGateway.assure_tables()

    logger.info("checking builtin taps ...")
    for t in BUILTIN_TAPS:
        logger.info(f"checking {t['alias']}")
        git_addr = complete_shorten_address(t["address"])
        SystemGateway.clone_repo(TAPS_PATH, t['alias'], git_addr)

    logger.info("checking docker assets")
    logger.info(f"checking docker network {GLOBAL_NETWORK_NAME}")
    DockerServiceGateway.assure_network(GLOBAL_NETWORK_NAME,
                                        labels=CONTAINER_META_LABELS)