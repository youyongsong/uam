import os
import uuid
import sys

import yaml
from jinja2 import Template

from uam.settings import (TAPS_PATH, FORMULA_FOLDER_NAME,
                          CONTAINER_META_LABELS, GLOBAL_NETWORK_NAME)
from uam.entities.exceptions import (TapsNotFound, AppNameInvalid,
                                     FormulaMalformed)


def recognize_app_name(app_name, taps):
    if app_name.startswith(('.', '/')):
        source_type = 'local'
        path = app_name
        app_name = os.path.splitext(os.path.basename(app_name)),
        formula_lst = [{'taps_name': '', 'path': 'path'}]
    else:
        lst = app_name.split('/')
        source_type = 'taps'
        if len(lst) == 2:
            taps_name, app_name = lst
            if taps_name not in [t['alias'] for t in taps]:
                raise TapsNotFound(taps_name)
            path = os.path.join(TAPS_PATH, taps_name, FORMULA_FOLDER_NAME,
                                app_name)
            formula_lst = [
                {'taps_name': taps_name, 'path': f'{path}.yaml'},
                {'taps_name': taps_name, 'path': f'{path}.yml'}
            ]
        elif len(lst) == 1:
            app_name = lst[0]
            formula_lst = []
            for t in taps:
                path = os.path.join(TAPS_PATH, t['alias'], FORMULA_FOLDER_NAME,
                                    app_name)
                formula_lst.extend([
                    {'taps_name': t['alias'], 'path': f'{path}.yaml'},
                    {'taps_name': t['alias'], 'path': f'{path}.yml'}
                ])
        else:
            raise AppNameInvalid(app_name)
    return (source_type, app_name, formula_lst)


def create_app(source_type, taps_name, app_name, formula: str):
    try:
        data = yaml.load(formula)
    except yaml.error.YAMLError as exc:
        raise FormulaMalformed(exc)

    # TODO formula schema check

    app = {
        'name': app_name,
        'source_type': source_type,
        'taps_alias': taps_name,
        'version': data['version'],
        'description': data.get('description', ''),
        'image': data['image'],
        'shell': data.get('shell', 'sh'),
        'status': 'active',
        'environments': data.get('environments', {}),
        'configs': data.get('configs', [])
    }
    app['volumes'] = [
        {'name': f'uam-{uuid.uuid4()}', 'path': v['path']}
        for v in data.get('volumes', [])
    ]
    app['entrypoints'] = [
        {
            'alias': k,
            'container_entrypoint': v['container_entrypoint'],
            'container_arguments': v.get('container_arguments', ''),
            'enabled': True
        }
        for k, v in data['entrypoints'].items()
    ]

    return app


def generate_app_shims(app):
    with open(os.path.join(os.path.dirname(__file__),
                           'shim.tmpl'), 'r') as f_handler:
        template = Template(f_handler.read())

    shims = {}
    for entry in app['entrypoints']:
        shim = template.render({
            'app': app,
            'entrypoint': entry,
            'volumes': app['volumes'],
            'configs': app['configs'],
            'python_path': sys.executable,
            'meta_labels': CONTAINER_META_LABELS,
            'network': GLOBAL_NETWORK_NAME,
        })
        shims[entry['alias']] = shim
    return shims


def deactive_entrypoints(entrypoints, aliases):
    return [
        {**e, **{'enabled': False}}
        for e in entrypoints
        if e['alias'] in aliases
    ]
