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
from uam.entities.exceptions.app import (TapsNotFound, AppNameInvalid,
                                         FormulaMalformed, NoValidVersion,
                                         PinnedVersionNotExist)


logger = logging.getLogger(__name__)


class AppStatus:
    Active = "active"
    Inactive = "inactive"
    SemiActive = "semi-active"


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
                logger.error(f"can not recognize {app_name}'s taps.")
                raise TapsNotFound()
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
            logger.error(f"can not recognize {app_name}'s format.")
            raise AppNameInvalid()
    return (source_type, app_name, formula_lst)


def create_app(source_type, taps_name, app_name, version, formula: str,
               pinned_version=None):
    try:
        data = yaml.load(formula)
    except yaml.error.YAMLError as exc:
        logger.error(f"formual content does not match yaml format: {exc}")
        raise FormulaMalformed()

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
        'configs': data.get('configs', []),
        "pinned": False,
        "pinned_version": ""
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
    if pinned_version:
        app["pinned"] = True
        app["pinned_version"] = pinned_version

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


def generate_shell_shim(app):
    with open(os.path.join(os.path.dirname(__file__),
                           'shim.tmpl'), 'r') as f_handler:
        template = Template(f_handler.read())

    return template.render({
        "app": app,
        "entrypoint": {"container_entrypoint": app["shell"]},
        "volumes": app["volumes"],
        "configs": app["configs"],
        "python_path": sys.executable,
        "meta_labels": CONTAINER_META_LABELS,
        "network": GLOBAL_NETWORK_NAME,
    })


def deactive_entrypoints(entrypoints, aliases):
    return [
        {**e, **{'enabled': False}}
        for e in entrypoints
        if e['alias'] in aliases
    ]


def select_proper_version(versions, pinned_version=None):
    # format versions
    versions_lst = []
    for v in versions:
        try:
            versions_lst.append([Version(v, partial=True), v])
        except ValueError:
            logger.warning(f"{v} is not a valid semantic version, "
                            "ignoring it ...")
    if not versions_lst:
        logger.error("all versions are not valid semantic version format.")
        raise NoValidVersion()

    # select the pinned version
    if pinned_version:
        pinned = Version(pinned_version, partial=True)
        for v in versions_lst:
            if pinned == v[0]:
                return v[1]
        else:
            logger.error(f"{pinned_version} is not in avaiable versions list.")
            raise PinnedVersionNotExist()

    # select the latest version
    latest = sorted(versions_lst, key=lambda v: v[0], reverse=True)[0]
    return latest[1]


def build_formula_path(taps_name, app_name, version, ext="yaml"):
    return os.path.join(TAPS_PATH, taps_name, FORMULA_FOLDER_NAME,
                        app_name, version)


def get_app_status(app_data):
    entrypoints_enabled_status_lst = [e["enabled"] for e in app_data["entrypoints"]]
    if all(entrypoints_enabled_status_lst):
        app_status = AppStatus.Active
    elif any(entrypoints_enabled_status_lst):
        app_status = AppStatus.SemiActive
    else:
        app_status = AppStatus.Inactive
    return app_status


def build_app_list(apps):
    app_lst = {}
    for app in apps:
        if app["name"] not in app_lst:
            app_lst[app["name"]] = []
        app_info = {**app, **{"status": get_app_status(app)}}
        app_lst[app["name"]].append(app_info)
    return app_lst