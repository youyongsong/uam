import logging

from uam.settings import db

from .models import Taps, App, EntryPoint, Volume, Config
from .exceptions import (AppNotExist, TapsAliasConflict,
                         TapsAddressConflict)


logger = logging.getLogger(__name__)


class DatabaseGateway:
    AppNotExist = AppNotExist
    TapsAliasConflict = TapsAliasConflict
    TapsAddressConflict = TapsAddressConflict

    @staticmethod
    def assure_tables():
        db.create_tables([Taps, App, EntryPoint, Volume, Config], safe=True)

    @staticmethod
    def store_taps(taps):
        Taps.create(**taps)

    @staticmethod
    def delete_taps(alias):
        taps = Taps.get(Taps.alias == alias)
        taps.delete_instance()

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
    def valid_taps_conflict(alias, address):
        if Taps.select().where(Taps.alias == alias):
            error = TapsAliasConflict(alias)
            logger.warning(error.message)
            raise error
        if Taps.select().where(Taps.address == address):
            error = TapsAddressConflict(address)
            logger.warning(error.message)
            raise error
        return True

    @staticmethod
    def taps_exists(alias):
        if Taps.select().where(Taps.alias == alias):
            return True
        return False

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
            raise AppNotExist(name)
        return app.id

    @staticmethod
    def get_app_detail(name):
        try:
            app = App.get(App.name == name)
        except App.DoesNotExist:
            raise AppNotExist(name)
        app_data = {
            'name': name,
            'source_type': app.source_type,
            'taps_alias': app.taps_alias,
            'version': app.version,
            'description': app.description,
            'image': app.image,
            'shell': app.shell,
            'environments': app.environments,
        }
        app_data['volumes'] = [
            {'name': v.name, 'path': v.path} for v in app.volumes
        ]
        app_data['configs'] = [
            {'host_path': c.host_path, 'container_path': c.container_path}
            for c in app.configs
        ]
        app_data['entrypoints'] = [
            {
                'alias': e.alias,
                'container_entrypoint': e.container_entrypoint,
                'container_arguments': e.container_arguments,
                'enabled': e.container_enabled
            } for e in app.entrypoints
        ]

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
