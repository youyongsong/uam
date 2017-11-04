# -*- coding: utf-8 -*-
import uuid

from uam.app import App, EntryPoint, Volume, Config
from uam.utils import dict_add


def create_app(db, app_data, override_entrypoints=True):
    entrypoints = app_data.pop('entrypoints', [])
    volumes = app_data.pop('volumes', [])
    configs = app_data.pop('configs', [])
    with db.atomic():
        app = App.create(**app_data)

        if entrypoints:
            conflicted = get_conflicted_entrypoints(db, entrypoints)
            if conflicted:
                if override_entrypoints:
                    EntryPoint.update(enabled=False).where(EntryPoint.alias << conflicted)
                else:
                    for entry in entrypoints:
                        if entry['alias'] in conflicted:
                            entry['enabled'] = False
            entrypoints = [dict_add(entry, {'app': app.id}) for entry in entrypoints]
            EntryPoint.insert_many(entrypoints).execute()

        if volumes:
            volumes = [
                dict_add(volume, {'name': str(uuid.uuid4()), 'app': app.id})
                for volume in volumes
            ]
            Volume.insert_many(volumes).execute()

        if configs:
            configs = [dict_add(config, {'app': app.id}) for config in configs]
            Config.insert_many(configs).execute()

    return app.id


def list_apps():
    pass


def view_app(source_type, source):
    pass


def get_conflicted_entrypoints(db, entrypoints):
    return [
        e.alias
        for e in EntryPoint.select().where(
            (EntryPoint.alias << [item['alias'] for item in entrypoints]) &
            (EntryPoint.enabled == True))
    ]
