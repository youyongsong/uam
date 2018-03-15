import logging

from uam.settings import SourceTypes
from uam.usecases.tap import list_taps
from uam.usecases.venv import get_venv_path
from uam.usecases.exceptions.app import (AppNameFormatInvalid, AppTapNotFound,
                                         AppAlreadyExist, NoProperVersionMatched,
                                         NoValidVersion, AppFormulaNotFound,
                                         AppFormulaMalformed, AppEntryPointsConflicted,
                                         AppNotInstalled, UpdateLocalTapApp,
                                         NoNewVersionFound)
from uam.entities.app import (AppStatus, recognize_app_name, create_app,
                              deactive_entrypoints, generate_app_shims,
                              generate_shell_shim, select_proper_version,
                              build_formula_path, build_app_list,
                              build_formula_folder_path, diff_app_data,
                              get_app_status, filter_disabled_aliases)
from uam.entities.exceptions import app as app_excs


logger = logging.getLogger(__name__)


def install_app(DatabaseGateway, SystemGateway, app_name,
                override_entrypoints=None, pinned_version=None, venv=""):
    try:
        source_type, app_name, formula_lst = recognize_app_name(
            app_name, list_taps(DatabaseGateway))
    except app_excs.AppNameInvalid:
        logger.error(f"can not recognize {app_name}'s format.'")
        raise AppNameFormatInvalid(app_name)
    except app_excs.TapNotFound as error:
        logger.error(f"{app_name}'s tap name not found in all avaliable tap.'")
        raise AppTapNotFound(app_name)

    if DatabaseGateway.app_exists(app_name, pinned_version=pinned_version, venv=venv):
        raise AppAlreadyExist(app_name)

    # get the formula content
    if source_type == SourceTypes.LOCAL:
        formula_content = SystemGateway.read_yaml_content(formula_lst[0]['path'])
        tap_name = None
    else:
        for formula in formula_lst:
            if SystemGateway.isfolder(formula['path']):
                tap_name, formula_folder = formula['tap_name'], formula['path']
                break
        else:
            raise AppFormulaNotFound(app_name)

        logger.info(f"{app_name}'s formula found in tap {tap_name}.")
        versions = SystemGateway.list_yaml_names(formula_folder)
        try:
            version = select_proper_version(versions, pinned_version=pinned_version)
        except app_excs.NoValidVersion:
            raise NoValidVersion(tap_name)
        except app_excs.PinnedVersionNotExist:
            raise NoProperVersionMatched(pinned_version)
        logger.info(f"version {version} will be installed.")
        formula_path = build_formula_path(tap_name, app_name, version)
        formula_content = SystemGateway.read_yaml_content(formula_path)

    # create app data structure using formula content and metadata
    try:
        app = create_app(source_type, tap_name, app_name, version, formula_content,
                         pinned_version=pinned_version, venv=venv)
    except app_excs.FormulaMalformed as error:
        raise AppFormulaMalformed(app_name, tap_name)

    conflicted_aliases = DatabaseGateway.get_conflicted_entrypoints(
        [e["alias"] for e in app["entrypoints"]], venv=venv)
    if override_entrypoints is None:
        if conflicted_aliases:
            raise AppEntryPointsConflicted(conflicted_aliases)
    elif override_entrypoints is False:
        app['entrypoints'] = deactive_entrypoints(
            app['entrypoints'], conflicted_aliases)
    else:
        logger.info("disabling conflicted aliases ...")
        DatabaseGateway.disable_entrypoints(conflicted_aliases, venv=venv)

    shims = generate_app_shims(app)

    SystemGateway.store_app_shims(shims, venv_path=get_venv_path(SystemGateway, venv))
    DatabaseGateway.store_app(app)
    return app


def uninstall_app(DatabaseGateway, SystemGateway, DockerServiceGateway,
                  app_name, pinned_version=None, venv=""):
    try:
        app_id = DatabaseGateway.get_app_id(app_name,
                                            pinned_version=pinned_version, venv=venv)
    except DatabaseGateway.AppNotExist:
        logger.error(f"{app_name} not found in database.")
        raise AppNotInstalled(app_name, pinned_version)

    volumes = DatabaseGateway.get_volumes(app_id)
    entrypoints = DatabaseGateway.get_active_entrypoints(app_id)
    vol_names = [v['name'] for v in volumes]
    shim_names = [e['alias'] for e in entrypoints]

    SystemGateway.delete_app_shims(shim_names,
                                   venv_path=get_venv_path(SystemGateway, venv))
    DockerServiceGateway.delete_volumes(vol_names)
    DatabaseGateway.delete_app(app_id)


def exec_app(DatabaseGateway, SystemGateway, app_name, pinned_version=None,
             arguments='', venv=""):
    try:
        app = DatabaseGateway.get_app_detail(app_name, pinned_version=pinned_version,
                                             venv=venv)
    except DatabaseGateway.AppNotExist:
        logger.error(f"{app_name} not found in database.")
        raise AppNotInstalled(app_name)
    shim = generate_shell_shim(app)
    SystemGateway.run_temporay_script(shim, arguments=arguments)


def list_apps(DatabaseGateway, venv=""):
    apps = DatabaseGateway.list_apps(venv=venv)
    app_lst = build_app_list(apps)
    return app_lst


def update_app(DatabaseGateway, SystemGateway, DockerServiceGateway, app_name,
               venv=""):
    app = _get_app_from_db(DatabaseGateway, app_name, venv=venv)
    if app["source_type"] == SourceTypes.LOCAL:
        logger.warning("local type app is not updatable.")
        raise UpdateLocalTapApp(app_name)

    logger.info(f"checking if new version of {app_name} ready ...")
    tap_name = app["tap_alias"]
    formula_folder_path = build_formula_folder_path(tap_name, app_name)
    versions = SystemGateway.list_yaml_names(formula_folder_path)
    try:
        version = select_proper_version(versions)
    except app_excs.NoValidVersion:
        logger.warning(f"no yaml files inside {formula_folder_path} "
                       "matches version naming format.")
        raise NoValidVersion(tap_name)
    if version == app["version"]:
        logger.info("current app's version is already the latest.")
        raise NoNewVersionFound(version)
    logger.info(f"{app_name} will be upgraded to vresion {version}.")
    formula_path = build_formula_path(tap_name, app_name, version)
    formula_content = SystemGateway.read_yaml_content(formula_path)

    logger.info("building new app data using the new version's formula ...")
    try:
        new_app = create_app(app["source_type"], tap_name, app_name, version,
                             formula_content, venv=venv)
    except app.app_excs.FormulaMalformed as error:
        logger.error(f"app's formula is not a valid yaml file: {error}")
        raise AppFormulaMalformed(app_name, tap_name)

    logger.info("diffing the new app version with current app ...")
    change_set = diff_app_data(app, new_app)
    logger.info("changeset of the two versions are generated. ")

    _apply_change_set(DatabaseGateway, SystemGateway, DockerServiceGateway,
                      app["id"], change_set, venv=venv)


def reinstall_app(DatabaseGateway, SystemGateway, DockerServiceGateway, app_name,
                  pinned_version=None, venv=""):
    app = _get_app_from_db(DatabaseGateway, app_name, pinned_version=pinned_version,
                           venv=venv)

    logger.info(f"reading {app_name}'s formula ...")
    formula_path = build_formula_path(app["tap_alias"], app_name, app["version"])
    formula_content = SystemGateway.read_yaml_content(formula_path)

    logger.info("rebuilding app data from formula ...")
    try:
        new_app = create_app(app["source_type"], app["tap_alias"], app_name,
                             app["version"], formula_content, venv=venv)
    except app.app_excs.FormulaMalformed as error:
        logger.error(f"app's formula is not a valid yaml file: {error}")
        raise AppFormulaMalformed(app_name, app["tap_alias"])

    logger.info("diffing the current formula with the installed one ...")
    change_set = diff_app_data(app, new_app)
    logger.info("changeset are generated. ")

    _apply_change_set(DatabaseGateway, SystemGateway, DockerServiceGateway,
                      app["id"], change_set, venv=venv)


def active_app(DatabaseGateway, SystemGateway, app_name, pinned_version=None,
               venv=""):
    logger.info("searching app inside database ...")
    try:
        app = DatabaseGateway.get_app_detail(app_name,
                                             pinned_version, venv=venv)
    except DatabaseGateway.AppNotExist:
        logger.warning(f"{app_name} {pinned_version if pinned_version else ''} "
                       "not found in database.")
        raise AppNotInstalled(app_name, pinned_version)

    logger.info("checking if app's status ...")
    if get_app_status(app) == AppStatus.Active:
        logger.info(f"{app_name} is active now, nothing to do else ...")
        return

    logger.info("filtering app's disabled entrypoints ...")
    disabled_aliases = filter_disabled_aliases(app["entrypoints"])
    logger.info(f"checking if {disabled_aliases} conflicted with existed aliases ...")
    conflicted_aliases = DatabaseGateway.get_conflicted_entrypoints(disabled_aliases,
                                                                    venv=venv)
    if conflicted_aliases:
        logger.info(f"disabling existed conflicted aliases {conflicted_aliases} ...")
        DatabaseGateway.disable_entrypoints(conflicted_aliases, venv=venv)
    logger.info(f"enabling app's entrypoints {disabled_aliases} ...")
    DatabaseGateway.enable_entrypoints(app["id"], disabled_aliases)

    logger.info("regenerating app's shims ...")
    app = DatabaseGateway.retrieve_app_detail(app["id"], venv=venv)
    shims = generate_app_shims(app)
    SystemGateway.store_app_shims(shims, venv=venv)


def _get_app_from_db(DatabaseGateway, app_name, pinned_version=None, venv=""):
    logger.info(f"checking if {app_name} is installed ...")
    try:
        app = DatabaseGateway.get_app_detail(app_name, pinned_version=pinned_version,
                                             venv=venv)
    except DatabaseGateway.AppNotExist:
        logger.warning(f"{app_name} not found in database.")
        raise AppNotInstalled(app_name)
    return app


def _apply_change_set(DatabaseGateway, SystemGateway, DockerServiceGateway,
                      app_id, change_set, venv=""):
    if change_set["deleted_volumes"]:
        logger.info(f"cleaning deleted volumes {change_set['deleted_volumes']} ...")
        logger.info("deleting docker volumes ...")
        DockerServiceGateway.delete_volumes([
            v["name"] for v in change_set["deleted_volumes"]
        ])
        logger.info("deleting database volumes ...")
        DatabaseGateway.delete_volumes(app_id, [
            v["name"] for v in change_set["deleted_volumes"]
        ])
    if change_set["added_volumes"]:
        logger.info(f"adding new volumes {change_set['added_volumes']} ...")
        logger.info("creating docker volumes ...")
        DockerServiceGateway.create_volumes([
            v["name"] for v in change_set["added_volumes"]
        ])
        logger.info("storing volumes into database ...")
        DatabaseGateway.store_volumes(app_id, change_set["added_volumes"])

    if change_set["deleted_entrypoints"]:
        logger.info(f"cleanning deleted entrypoints {change_set['deleted_entrypoints']} ...")
        logger.info("deleting shims ...")
        SystemGateway.delete_app_shims([
            e["alias"] for e in change_set["deleted_entrypoints"] if e["enabled"]
        ], venv_path=get_venv_path(venv))
        logger.info("deleting entrypoints from database ...")
        DatabaseGateway.delete_entrypoints(app_id, [
            e["alias"] for e in change_set["deleted_entrypoints"]
        ])
    if change_set["added_entrypoints"]:
        logger.info(f"storing new entrypoints {change_set['added_entrypoints']} ...")
        DatabaseGateway.store_entrypoints(app_id, change_set["added_entrypoints"])

    if change_set["deleted_configs"]:
        logger.info(f"cleaning deleted configs {change_set['deleted_configs']} ...")
        DatabaseGateway.delete_configs(app_id, change_set["deleted_configs"])
    if change_set["added_configs"]:
        logger.info(f"storing new configs {change_set['added_configs']} ...")
        DatabaseGateway.store_configs(app_id, change_set["added_configs"])

    if change_set["changed_meta_data"]:
        logger.info("updating the app meta data into database ...")
        DatabaseGateway.update_app_meta(app_id, change_set["changed_meta_data"])

    logger.info("regenerating all shims ...")
    app_data = DatabaseGateway.retrieve_app_detail(app_id)
    shims = generate_app_shims(app_data)
    SystemGateway.store_app_shims(shims, venv=venv)


def download_app_image(DatabaseGateway, DockerServiceGateway, app_name, pinned_version=None, venv=""):
    logger.info("searching app inside database ...")
    try:
        app = DatabaseGateway.get_app_detail(app_name,
                                             pinned_version, venv=venv)
    except DatabaseGateway.AppNotExist:
        logger.warning(f"{app_name} {pinned_version if pinned_version else ''} "
                       "not found in database.")
        raise AppNotInstalled(app_name, pinned_version)
    logger.info(f"downloding {app_name}'s image ...")
    DockerServiceGateway.pull_image(app["image"])