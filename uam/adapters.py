import logging
import os
import stat

from uam.settings import db, BIN_PATH
from uam.app import Taps, App, EntryPoint, Volume, Config


logger = logging.getLogger(__name__)


class AppGateway:
    @staticmethod
    def app_exists(name):
        if App.select().where(App.name == name):
            return True
        return False

    @staticmethod
    def get_conflicted_entrypoints(entrypoints):
        return [
            e.alias for e in EntryPoint.select().where(
                (EntryPoint.alias << [item['alias'] for item in entrypoints]) &
                (EntryPoint.enabled == True)
            )
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
    def store_app_shims(shims):
        for name, content in shims.items():
            target_path = os.path.join(BIN_PATH, name)
            logger.info(f'creating shim file: {target_path}')
            with open(target_path, 'w') as f_handler:
                f_handler.write(content)

            st = os.stat(target_path)
            os.chmod(target_path, st.st_mode | stat.S_IEXEC)


class TapsGateway:
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

