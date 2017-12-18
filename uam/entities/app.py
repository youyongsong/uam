import logging
import os
import uuid
import sys

import yaml
from jinja2 import Template
from semantic_version import Version

from uam.settings import (TAPS_PATH, FORMULA_FOLDER_NAME,
                          CONTAINER_META_LABELS, GLOBAL_NETWORK_NAME,
                          SourceTypes)
from uam.entities.exceptions import (TapsNotFound, AppNameInvalid,
                                     FormulaMalformed, NoValidVersion)


logger = logging.getLogger(__name__)


def recognize_app_name(app_name, taps):
    if app_name.startswith(('.', '/')):
        source_type = SourceTypes.LOCAL
        path = app_name
        app_name = os.path.splitext(os.path.basename(app_name)),
        formula_lst = [{'taps_name': '', 'path': 'path'}]
    else:
        lst = app_name.split('/')
        source_type = SourceTypes.TAPS
        if len(lst) == 2:
            taps_name, app_name = lst
            if taps_name not in [t['alias'] for t in taps]:
                raise TapsNotFound(taps_name)
            formula_lst = [{
                'taps_name': taps_name,
                'path': os.path.join(TAPS_PATH, taps_name, FORMULA_FOLDER_NAME,
                                     app_name)
            }]
        elif len(lst) == 1:
            app_name = lst[0]
            formula_lst = [
                {
                    'taps_name': t['alias'],
                    'path': os.path.join(TAPS_PATH, t['alias'],
                                         FORMULA_FOLDER_NAME, app_name)
                }
                for t in taps
            ]
        else:
            raise AppNameInvalid(app_name)
    return (source_type, app_name, formula_lst)


def create_app(source_type, taps_name, app_name, version, formula: str):
    try:
        data = yaml.load(formula)
    except yaml.error.YAMLError as exc:
        raise FormulaMalformed(exc)

    # TODO formula schema check

    app = {
        'name': app_name,
        'source_type': source_type,
        'taps_alias': taps_name,
        'version': version,
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


def select_proper_version(versions):
    versions_lst = []
    for v in versions:
        try:
            versions_lst.append([Version(v, partial=True), v])
        except ValueError:
            logger.warning(f"{v} is not a valid semantic version.")
    if not versions_lst:
        raise NoValidVersion()
    latest = sorted(versions_lst, key=lambda v: v[0], reverse=True)[0]
    return latest[1]


def build_formula_path(taps_name, app_name, version, ext="yaml"):
    return os.path.join(TAPS_PATH, taps_name, FORMULA_FOLDER_NAME,
                        app_name, version)