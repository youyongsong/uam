import logging

import docker

from uam.settings import docker_client


logger = logging.getLogger(__name__)


class DockerServiceGateway:

    @staticmethod
    def delete_volume(vol_name):
        logger.info(f'removing docker volume {vol_name}')
        try:
            vol = docker_client.volumes.get(vol_name)
        except docker.errors.NotFound:
            logger.warning(f'volume {vol_name} not found.')
            return
        vol.remove()
        logger.info(f'{vol_name} removed')

    @staticmethod
    def delete_volumes(vol_names):
        for v in vol_names:
            DockerServiceGateway.delete_volume(v)
