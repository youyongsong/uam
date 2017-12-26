import logging

from uam.settings import SourceTypes
from uam.usecases.taps import list_taps
from uam.usecases.exceptions.app import (AppNameFormatInvalid, AppTapsNotFound,
                                         AppAlreadyExist, NoProperVersionMatched,
                                         NoValidVersion, AppFormulaNotFound,
                                         AppFormulaMalformed, AppEntryPointsConflicted,
                                         AppNotInstalled, UpdateLocalTapApp,
                                         NoNewVersionFound)
from uam.entities.app import (recognize_app_name, create_app,
                              deactive_entrypoints, generate_app_shims,
                              generate_shell_shim, select_proper_version,
                              build_formula_path, build_app_list,
                              build_formula_folder_path, diff_app_data)
from uam.entities.exceptions import app as app_excs


logger = logging.getLogger(__name__)


def install_app(DatabaseGateway, SystemGateway, app_name,
                override_entrypoints=None, pinned_version=None):
    try:
        source_type, app_name, formula_lst = recognize_app_name(
            app_name, list_taps(DatabaseGateway))
    except app_excs.AppNameInvalid as error:
        logger.error(f"can not recognize {app_name}'s format.'")
        raise AppNameFormatInvalid(app_name)
    except app_excs.TapsNotFound as error:
        logger.error(f"{app_name}'s taps name not found in all avaliable taps.'")
        raise AppTapsNotFound(app_name)

    if DatabaseGateway.app_exists(app_name, pinned_version=pinned_version):
        raise AppAlreadyExist(app_name)

    # get the formula content
    if source_type == SourceTypes.LOCAL:
        formula_content = SystemGateway.read_yaml_content(formula_lst[0]['path'])
    else:
        for formula in formula_lst:
            if SystemGateway.isfolder(formula['path']):
                taps_name, formula_folder = formula['taps_name'], formula['path']
                break
        else:
            raise AppFormulaNotFound(app_name)

        logger.info(f"{app_name}'s formula found in taps {taps_name}.")
        versions = SystemGateway.list_yaml_names(formula_folder)
        try:
            version = select_proper_version(versions, pinned_version=pinned_version)
        except app_excs.NoValidVersion:
            raise NoValidVersion(taps_name)
        except app_excs.PinnedVersionNotExist:
            raise NoProperVersionMatched(pinned_version)
        logger.info(f"version {version} will be installed.")
        formula_path = build_formula_path(taps_name, app_name, version)
        formula_content = SystemGateway.read_yaml_content(formula_path)

    # create app data structure using formula content and metadata
    try:
        app = create_app(source_type, taps_name, app_name, version, formula_content,
                         pinned_version=pinned_version)
    except app_excs.FormulaMalformed as error:
        raise AppFormulaMalformed(app_name, taps_name)

    conflicted_aliases = DatabaseGateway.get_conflicted_entrypoints(
        app['entrypoints'])
    if override_entrypoints is None:
        if conflicted_aliases:
            raise AppEntryPointsConflicted(conflicted_aliases)
    elif override_entrypoints is False:
        app['entrypoints'] = deactive_entrypoints(
            app['entrypoints'], conflicted_aliases)
    else:
        logger.info("disabling conflicted aliases ...")
        DatabaseGateway.disable_entrypoints(conflicted_aliases)

    shims = generate_app_shims(app)

    SystemGateway.store_app_shims(shims)
    DatabaseGateway.store_app(app)
    return app


def uninstall_app(DatabaseGateway, SystemGateway, DockerServiceGateway,
                  app_name, pinned_version=None):
    try:
        app_id = DatabaseGateway.get_app_id(app_name, pinned_version=pinned_version)
    except DatabaseGateway.AppNotExist:
        logger.error(f"{app_name} not found in database.")
        raise AppNotInstalled(app_name, pinned_version)

    volumes = DatabaseGateway.get_volumes(app_id)
    entrypoints = DatabaseGateway.get_active_entrypoints(app_id)
    vol_names = [v['name'] for v in volumes]
    shim_names = [e['alias'] for e in entrypoints]

    SystemGateway.delete_app_shims(shim_names)
    DockerServiceGateway.delete_volumes(vol_names)
    DatabaseGateway.delete_app(app_id)


def exec_app(DatabaseGateway, SystemGateway, app_name, arguments=''):
    try:
        app = DatabaseGateway.get_app_detail(app_name)
    except DatabaseGateway.AppNotExist:
        logger.error(f"{app_name} not found in database.")
        raise AppNotInstalled(app_name) 
    shim = generate_shell_shim(app)
    SystemGateway.run_temporay_script(shim, arguments=arguments)


def list_apps(DatabaseGateway):
    apps = DatabaseGateway.list_apps()
    app_lst = build_app_list(apps)
    return app_lst


def update_app(DatabaseGateway, SystemGateway, DockerServiceGateway, app_name):
    logger.info(f"checking if {app_name} is installed ...")
    try:
        app = DatabaseGateway.get_app_detail(app_name)
    except DatabaseGateway.AppNotExist:
        logger.warning(f"{app_name} not found in database.")
        raise AppNotInstalled(app_name)

    if app["source_type"] == SourceTypes.LOCAL:
        logger.warning("local type app is not updatable.")
        raise UpdateLocalTapApp(app_name)

    logger.info(f"checking if new version of {app_name} ready ...")
    tap_name = app["taps_alias"]
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
                             formula_content)
    except app.app_excs.FormulaMalformed as error:
        logger.error(f"app's formula is not a valid yaml file: {error}")
        raise AppFormulaMalformed(app_name, tap_name)

    logger.info("diffing the new app version with current app ...")
    change_set = diff_app_data(app, new_app)
    logger.info("changeset of the two versions are generated. ")

    if change_set["deleted_volumes"]:
        logger.info(f"cleaning deleted volumes {change_set['deleted_volumes']} ...")
        logger.info("deleting docker volumes ...")
        DockerServiceGateway.delete_volumes([
            v["name"] for v in change_set["deleted_volumes"]
        ])
        logger.info("deleting database volumes ...")
        DatabaseGateway.delete_volumes(app["id"], [
            v["name"] for v in change_set["deleted_volumes"]
        ])
    if change_set["added_volumes"]:
        logger.info(f"adding new volumes {change_set['added_volumes']} ...")
        logger.info("creating docker volumes ...")
        DockerServiceGateway.create_volumes([
            v["name"] for v in change_set["added_volumes"]
        ])
        logger.info("storing volumes into database ...")
        DatabaseGateway.store_volumes(app["id"], change_set["added_volumes"])

    if change_set["deleted_entrypoints"]:
        logger.info(f"cleanning deleted entrypoints {change_set['deleted_entrypoints']} ...")
        logger.info("deleting shims ...")
        SystemGateway.delete_app_shims([
            e["alias"] for e in change_set["deleted_entrypoints"] if e["enabled"]
        ])
        logger.info("deleting entrypoints from database ...")
        DatabaseGateway.delete_entrypoints(app["id"], [
            e["alias"] for e in change_set["deleted_entrypoints"]
        ])
    if change_set["added_entrypoints"]:
        logger.info(f"storing new entrypoints {change_set['added_entrypoints']} ...")
        DatabaseGateway.store_entrypoints(app["id"], change_set["added_entrypoints"])

    if change_set["deleted_configs"]:
        logger.info(f"cleaning deleted configs {change_set['deleted_configs']} ...")
        DatabaseGateway.delete_configs(app["id"], change_set["deleted_configs"])
    if change_set["added_configs"]:
        logger.info(f"storing new configs {change_set['added_configs']} ...")
        DatabaseGateway.store_configs(app["id"], change_set["added_configs"])

    logger.info("updating the app meta data into database ...")
    DatabaseGateway.update_app_meta(app["id"], change_set["changed_meta_data"])

    logger.info("regenerating all shims ...")
    app_data = DatabaseGateway.retrieve_app_detail(app["id"])
    shims = generate_app_shims(app_data)
    SystemGateway.store_app_shims(shims)