import logging
import os
import uuid
import sys

import yaml
from jinja2 import Template
from semantic_version import Version

from uam.settings import (TAP_PATH, FORMULA_FOLDER_NAME,
                          CONTAINER_META_LABELS, GLOBAL_NETWORK_NAME,
                          SourceTypes)
from uam.entities.exceptions.app import (TapNotFound, AppNameInvalid,
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
        formula_lst = [{'tap_name': '', 'path': path}]
    else:
        lst = app_name.split('/')
        source_type = SourceTypes.TAP
        if len(lst) == 2:
            tap_name, app_name = lst
            if tap_name not in [t['alias'] for t in taps]:
                logger.error(f"can not recognize {app_name}'s tap.")
                raise TapNotFound()
            formula_lst = [{
                'tap_name': tap_name,
                'path': os.path.join(TAP_PATH, tap_name, FORMULA_FOLDER_NAME,
                                     app_name)
            }]
        elif len(lst) == 1:
            app_name = lst[0]
            formula_lst = [
                {
                    'tap_name': t['alias'],
                    'path': os.path.join(TAP_PATH, t['alias'],
                                         FORMULA_FOLDER_NAME, app_name)
                }
                for t in taps
            ]
        else:
            logger.error(f"can not recognize {app_name}'s format.")
            raise AppNameInvalid()
    return (source_type, app_name, formula_lst)


def create_app(source_type, tap_name, app_name, version, formula: str,
               pinned_version=None, venv=""):
    try:
        data = yaml.load(formula)
    except yaml.error.YAMLError as exc:
        logger.error(f"formual content does not match yaml format: {exc}")
        raise FormulaMalformed()

    # TODO formula schema check

    app = {
        'name': app_name,
        'source_type': source_type,
        'tap_alias': tap_name,
        'version': version,
        'description': data.get('description', ''),
        'image': data['image'],
        'shell': data.get('shell', 'sh'),
        'status': 'active',
        'environments': data.get('environments', {}),
        'configs': data.get('configs', []),
        "pinned": False,
        "pinned_version": "",
        "venv": venv,
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


def generate_app_shims(app, selected_aliases=None):
    with open(os.path.join(os.path.dirname(__file__),
                           'shim.tmpl'), 'r') as f_handler:
        template = Template(f_handler.read())

    shims = {}
    for entry in app['entrypoints']:
        if selected_aliases and entry["alias"] not in selected_aliases:
            continue
        if not entry["enabled"]:
            continue
        logger.info(f"generating app shim {entry['alias']} ...")
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


def filter_disabled_aliases(entrypoints):
    return [e["alias"] for e in entrypoints if not e["enabled"]]


def deactive_entrypoints(entrypoints, aliases=None):
    if not aliases:
        return [{**e, "enabled": False} for e in entrypoints]
    else:
        return [
            {**e, "enabled": False}
            for e in entrypoints if e['alias'] in aliases
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


def build_formula_folder_path(tap_name, app_name):
    return os.path.join(TAP_PATH, tap_name, FORMULA_FOLDER_NAME,
                        app_name)


def build_formula_path(tap_name, app_name, version):
    return os.path.join(TAP_PATH, tap_name, FORMULA_FOLDER_NAME,
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


def diff_app_data(old_app, new_app):
    change_set = {}

    (change_set["deleted_volumes"],
     change_set["added_volumes"],
     change_set["unchanged_volumes"]) = _diff_lst(
         old_app["volumes"], new_app["volumes"], ("path",)
     )

    (change_set["deleted_entrypoints"],
     change_set["added_entrypoints"],
     change_set["unchanged_entrypoints"]) = _diff_lst(
         old_app["entrypoints"], new_app["entrypoints"],
         ("alias", "container_entrypoint", "container_arguments")
     )

    (change_set["deleted_configs"],
     change_set["added_configs"],
     change_set["unchanged_configs"]) = _diff_lst(
         old_app["configs"], new_app["configs"],
         ("host_path", "container_path")
     )

    change_set["changed_meta_data"] = {
        field: new_app[field]
        for field in ("version", "description", "image", "environments",
                      "shell")
        if new_app[field] != old_app[field]
    }

    return change_set


def _diff_lst(old_lst, new_lst, keys):
    old_set = {tuple(i[k] for k in keys) for i in old_lst}
    new_set = {tuple(i[k] for k in keys) for i in new_lst}
    deleted_items = [
        item
        for key in old_set - new_set
        for item in old_lst if key == tuple(item[k] for k in keys)
    ]
    added_items = [
        item
        for key in new_set - old_set
        for item in new_lst if key == tuple(item[k] for k in keys)
    ]
    unchanged_items = [
        item
        for key in old_set & new_set
        for item in old_lst if key == tuple(item[k] for k in keys)
    ]
    return deleted_items, added_items, unchanged_items