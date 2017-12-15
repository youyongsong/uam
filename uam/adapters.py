import logging
import os
import stat

import docker

from uam.settings import (db, docker_client, BIN_PATH, UamBaseException,
                          ErrorTypes)
from uam.app import Taps, App, EntryPoint, Volume, Config


logger = logging.getLogger(__name__)


class DatabaseError(UamBaseException):
    type = ErrorTypes.SYSTEM_ERROR


class AppNotExist(DatabaseError):
    code = 'app_not_found'
    type = ErrorTypes.USER_ERROR
    help_text = "app {} not found in database."

    def __init__(self, name):
        self.help_text = self.help_text.format(name)
        return super(AppNotFound, self).__init__()


class DatabaseGateway:
    AppNotExist = AppNotExist

    @staticmethod
    def app_exists(name):
        if App.select().where(App.name == name):
            return True
        return False

    @staticmethod
    def get_app_id(name):
        try:
            app = App.get(App.name == name)
        except App.DoesNotExist:
            raise AppNotFound(name)
        return app.id

    @staticmethod
    def store_app(app):
        entrypoints = app.pop('entrypoints')
        volumes = app.pop('volumes')
        configs = app.pop('configs')
        with db.atomic():
            app_model = App.create(**app)
            EntryPoint.insert_many(
                [{**e, **{'app': app_model.id}} for e in entrypoints]
            ).execute()
            Volume.insert_many(
                [{**v, **{'app': app_model.id}} for v in volumes]
            ).execute()
            Config.insert_many(
                [{**c, **{'app': app_model.id}} for c in configs]
            ).execute()

    @staticmethod
    def delete_app(app_id):
        App.get(App.id == app_id).delete_instance(recursive=True)

    @staticmethod
    def list_taps():
        return [
            {
                'alias': t.alias,
                'address': t.address,
                'priority': t.priority
            }
            for t in Taps.select()
        ]

    @staticmethod
    def get_conflicted_entrypoints(entrypoints):
        return [
            e.alias for e in EntryPoint.select().where(
                (EntryPoint.alias << [item['alias'] for item in entrypoints]) &
                (EntryPoint.enabled == True)
            )
        ]

    @staticmethod
    def get_active_entrypoints(app_id):
        return [
            {
                'alias': e.alias,
                'container_entrypoint': e.container_entrypoint,
                'container_arguments': e.container_arguments,
                'enabled': e.enabled
            }
            for e in EntryPoint.select().where((EntryPoint.app == app_id) &
                                               (EntryPoint.enabled == True))
        ]

    @staticmethod
    def get_volumes(app_id):
        return [
            {
                'name': v.name,
                'path': v.path
            }
            for v in Volume.select().where(Volume.app == app_id)
        ]


class SystemGateway:

    @staticmethod
    def store_app_shims(shims):
        for name, content in shims.items():
            target_path = os.path.join(BIN_PATH, name)
            logger.info(f'creating shim file: {target_path}')
            with open(target_path, 'w') as f_handler:
                f_handler.write(content)

            st = os.stat(target_path)
            os.chmod(target_path, st.st_mode | stat.S_IEXEC)

    @staticmethod
    def delete_app_shims(shim_names):
        for n in shim_names:
            target_path = os.path.join(BIN_PATH, n)
            logger.info(f'removing shim file: {target_path}')
            try:
                os.remove(target_path)
            except FileNotFoundError:
                logger.warning('{} not found'.format(target_path))
            else:
                logger.info('{} removed.'.format(target_path))

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
