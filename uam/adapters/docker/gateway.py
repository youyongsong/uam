import logging
import subprocess

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
        logger.info(f'removing docker volume {vol_name} ...')
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
            try:
                DockerServiceGateway.delete_volume(v)
            except docker.errors.NotFound:
                logger.info(f"volume {v} not found, skipping it ...")
            except docker.errors.APIError as err:
                logger.warning(f"volume {v} delete error: {err}")

    @staticmethod
    def create_volume(vol_name, labels={}):
        logger.info(f"creating docker volume {vol_name} ...")
        vol = docker_client.volumes.create(vol_name, labels=labels)
        logger.info(f"volume {vol_name} created.")

    @staticmethod
    def create_volumes(vol_names, labels={}):
        for v in vol_names:
            try:
                DockerServiceGateway.create_volume(v, labels)
            except docker.errors.APIError as err:
                logger.warning(f"volume {v} create error: {err}")

    @staticmethod
    def pull_image(image_name):
        logger.info(f"pulling docker image {image_name} ...")
        subprocess.run(f"docker pull {image_name}", shell=True)