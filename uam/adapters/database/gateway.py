import logging
from functools import reduce

from uam.settings import db

from .models import Tap, App, EntryPoint, Volume, Config
from .exceptions import (AppNotExist, TapAliasConflict,
                         TapAddressConflict)


logger = logging.getLogger(__name__)


class DatabaseGateway:
    AppNotExist = AppNotExist
    TapAliasConflict = TapAliasConflict
    TapAddressConflict = TapAddressConflict

    @staticmethod
    def assure_tables():
        db.create_tables([Tap, App, EntryPoint, Volume, Config], safe=True)

    @staticmethod
    def store_tap(tap):
        Tap.create(**tap)

    @staticmethod
    def delete_tap(alias):
        tap = Tap.get(Tap.alias == alias)
        tap.delete_instance()

    @staticmethod
    def list_taps():
        return [
            {
                'alias': t.alias,
                'address': t.address,
                'priority': t.priority
            }
            for t in Tap.select()
        ]

    @staticmethod
    def valid_tap_conflict(alias, address):
        if Tap.select().where(Tap.alias == alias):
            msg = f"tap named {alias} already existed."
            logger.error(msg)
            raise TapAliasConflict(msg)
        if Tap.select().where(Tap.address == address):
            msg = f"tap addressed {address} already existed."
            logger.error(msg)
            raise TapAddressConflict(msg)
        return True

    @staticmethod
    def tap_exists(alias):
        if Tap.select().where(Tap.alias == alias):
            return True
        return False

    @staticmethod
    def app_exists(name, pinned_version=None, venv=""):
        if pinned_version:
            if App.select().where(
                (App.name == name) & (App.pinned == True) &
                (App.pinned_version == pinned_version) &
                (App.venv == venv)
            ):
                return True
            return False
        else:
            if App.select().where(
                (App.name == name) & (App.pinned == False) &
                (App.venv == venv)
            ):
                return True
            return False

    @staticmethod
    def get_app_id(name, pinned_version=None, venv=""):
        if not pinned_version:
            query = ((App.name == name) & (App.pinned == False) &
                     (App.venv == venv))
        else:
            query = ((App.name == name) & (App.pinned == True) &
                     (App.pinned_version == pinned_version) &
                     (App.venv == venv))
        try:
            app = App.get(query)
        except App.DoesNotExist as error:
            msg = f"app {name}@{pinned_version} not found in database: {error}."
            logger.error(msg)
            raise AppNotExist(msg)
        return app.id

    @staticmethod
    def get_app_detail(name, pinned_version=None, venv=""):
        if not pinned_version:
            query = ((App.name == name) & (App.pinned == False) &
                     (App.venv == venv))
        else:
            query = ((App.name == name) & (App.pinned == True) &
                     (App.pinned_version == pinned_version) &
                     (App.venv == venv))
        try:
            app = App.get(query)
        except App.DoesNotExist as error:
            msg = f"app {name} not found in database: {error}"
            logger.error(msg)
            raise AppNotExist(msg)
        return _build_app_data(app)

    @staticmethod
    def retrieve_app_detail(app_id):
        app = App.get(App.id == app_id)
        return _build_app_data(app)

    @staticmethod
    def list_apps(venv=""):
        return [
            _build_app_data(app) for app in App.select().where(
                App.venv == venv
            )
        ]

    @staticmethod
    def store_app(app):
        entrypoints = app.pop('entrypoints')
        volumes = app.pop('volumes')
        configs = app.pop('configs')
        with db.atomic():
            app_model = App.create(**app)
            if entrypoints:
                EntryPoint.insert_many(
                    [{**e, **{'app': app_model.id}} for e in entrypoints]
                ).execute()
            if volumes:
                Volume.insert_many(
                    [{**v, **{'app': app_model.id}} for v in volumes]
                ).execute()
            if configs:
                Config.insert_many(
                    [{**c, **{'app': app_model.id}} for c in configs]
                ).execute()

    @staticmethod
    def update_app_meta(app_id, changed_data):
        App.update(**changed_data).where(App.id == app_id).execute()

    @staticmethod
    def delete_app(app_id):
        App.get(App.id == app_id).delete_instance(recursive=True)

    @staticmethod
    def get_conflicted_entrypoints(aliases, venv=""):
        return list(set([
            e.alias for e in EntryPoint.select().where(
                (EntryPoint.alias << aliases) & (EntryPoint.enabled == True) &
                (EntryPoint.app.venv == venv)
            )
        ]))

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
    def enable_entrypoints(app_id, aliases):
        EntryPoint.update(enabled=True).where(
            (EntryPoint.alias << aliases) & (EntryPoint.app == app_id)
        ).execute()

    @staticmethod
    def disable_entrypoints(aliases, venv=""):
        EntryPoint.update(enabled=False).where(
           (EntryPoint.alias << aliases) & (EntryPoint.app.venv == venv)).execute()

    @staticmethod
    def delete_entrypoints(app_id, aliases):
        EntryPoint.delete().where(
            (EntryPoint.app == app_id) & (EntryPoint.alias << aliases)).execute()

    @staticmethod
    def store_entrypoints(app_id, entrypoints):
        if not entrypoints:
            return
        EntryPoint.insert_many(
            [{"app": app_id, **e} for e in entrypoints]
        ).execute()

    @staticmethod
    def get_volumes(app_id):
        return [
            {
                'name': v.name,
                'path': v.path
            }
            for v in Volume.select().where(Volume.app == app_id)
        ]

    @staticmethod
    def delete_volumes(app_id, vol_names):
        Volume.delete().where(
            (Volume.name << vol_names) & (Volume.app == app_id)).execute()

    @staticmethod
    def store_volumes(app_id, volumes):
        if not volumes:
            return
        Volume.insert_many(
            [{"app": app_id, **v} for v in volumes]
        ).execute()

    @staticmethod
    def delete_configs(app_id, configs):
        query = reduce(lambda x, y: x | y, [
            Config.host_path == c["host_path"] &
            Config.container_path == c["container_path"] &
            Config.app == app_id
            for c in configs
        ])
        Config.delete().where(query).execute()

    @staticmethod
    def store_configs(app_id, configs):
        if not configs:
            return
        Config.insert_many(
            [{"app": app_id, **c} for c in configs]
        ).execute()


def _build_app_data(app):
    app_data = {
        "id": app.id,
        'name': app.name,
        'source_type': app.source_type,
        'tap_alias': app.tap_alias,
        'version': app.version,
        'description': app.description,
        'image': app.image,
        'shell': app.shell,
        'environments': app.environments,
        'pinned': app.pinned,
        'pinned_version': app.pinned_version
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
            'enabled': e.enabled
        } for e in app.entrypoints
    ]
    return app_data