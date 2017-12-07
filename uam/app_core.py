# -*- coding: utf-8 -*-
import uuid

from uam.app import App, EntryPoint, Volume, Config
from uam.exceptions import AppAlreadyExist, AppNotFound
from uam.utils import dict_add


def create_app(db, app_data, override_entrypoints=True):
    entrypoints = app_data.pop('entrypoints', [])
    volumes = app_data.pop('volumes', [])
    configs = app_data.pop('configs', [])
    with db.atomic():
        if App.select().where((App.source == app_data['source']) &
                              (App.source_type == app_data['source_type'])):
            raise AppAlreadyExist
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
                dict_add(volume, {'name': f'uam-{uuid.uuid4()}', 'app': app.id})
                for volume in volumes
            ]
            Volume.insert_many(volumes).execute()

        if configs:
            configs = [dict_add(config, {'app': app.id}) for config in configs]
            Config.insert_many(configs).execute()

    return app


def delete_app(db, source_type, source):
    with db.atomic():
        try:
            app = App.get(App.source_type == source_type, App.source == source)
        except App.DoesNotExist:
            raise AppNotFound('{}::{}'.format(source_type, source))
        app.delete_instance(recursive=True)


def get_app(db, source_type, source):
    with db.atomic():
        try:
            app = App.get(App.source_type == source_type, App.source == source)
        except App.DoesNotExist:
            raise AppNotFound('{}::{}'.format(source_type, source))
    return app


def list_entrypoints(db):
    return [
        {
            'alias': e.alias,
            'enabled': e.enabled,
            'entrypoint': e.container_entrypoint,
            'arguments': e.container_arguments,
            'app_source': e.app.source,
            'app_source_type': e.app.source_type,
        }
        for e in EntryPoint.select().order_by(EntryPoint.app)
    ]


def get_conflicted_entrypoints(db, entrypoints):
    return [
        e.alias
        for e in EntryPoint.select().where(
            (EntryPoint.alias << [item['alias'] for item in entrypoints]) &
            (EntryPoint.enabled == True))
    ]


def get_volumes(db, source_type, source):
    with db.atomic():
        try:
            app = App.get(App.source_type == source_type, App.source == source)
        except App.DoesNotExist:
            raise AppNotFound('{}::{}'.format(source_type, source))
        return [
            vol.name for vol in Volume.select().where(Volume.app == app.id)
        ]


def get_active_entrypoints(db, source_type, source):
    with db.atomic():
        try:
            app = App.get(App.source_type == source_type, App.source == source)
        except App.DoesNotExist:
            raise AppNotFound('{}::{}'.format(source_type, source))
        return [
            e.alias
            for e in EntryPoint.select().where((EntryPoint.app == app.id) &
                                               (EntryPoint.enabled == True))
        ]
