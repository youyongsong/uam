import logging

import docker

from uam.settings import docker_client


logger = logging.getLogger(__name__)


class DockerServiceGateway:

    @staticmethod
    def assure_network(network_name, labels={}):
        try:
            docker_client.networks.get(network_name)
        except docker.errors.NotFound:
            logger.info(f'creating docker network {network_name} ...')
            docker_client.networks.create(network_name, driver="bridge",
                                          labels=labels)

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
