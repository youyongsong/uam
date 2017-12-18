import logging

from uam.settings import SourceTypes
from uam.usecases.taps import list_taps
from uam.usecases.exceptions import (AppExisted, FormulaNotFound,
                                     EntryPointsConflicted, AppEntityInstallError,
                                     UninstallAppNotFound, ExecAppNotFound)
from uam.entities.app import (recognize_app_name, create_app,
                              deactive_entrypoints, generate_app_shims,
                              select_proper_version, build_formula_path)
from uam.entities.exceptions import (RecognizeAppError, AppCreateError,
                                     VersionSelectError)


logger = logging.getLogger(__name__)


def install_app(DatabaseGateway, SystemGateway, app_name,
                override_entrypoints=None):
    try:
        source_type, app_name, formula_lst = recognize_app_name(
            app_name, list_taps(DatabaseGateway))
    except RecognizeAppError as error:
        raise AppEntityInstallError(error)

    if DatabaseGateway.app_exists(app_name):
        raise AppExisted(app_name)

    if source_type == SourceTypes.LOCAL:
        formula_content = SystemGateway.read_yaml_content(formula_lst[0]['path'])
    else:
        for formula in formula_lst:
            if SystemGateway.isfolder(formula['path']):
                taps_name, formula_folder = formula['taps_name'], formula['path']
                break
        else:
            raise FormulaNotFound(app_name)
        logger.info(f"{app_name}'s formula found in taps {taps_name}.")
        versions = SystemGateway.list_yaml_names(formula_folder)
        try:
            version = select_proper_version(versions)
        except VersionSelectError as error:
            raise AppEntityInstallError(error)
        logger.info(f"version {version} will be installed.")
        formula_path = build_formula_path(taps_name, app_name, version)
        formula_content = SystemGateway.read_yaml_content(formula_path)

    try:
        app = create_app(source_type, taps_name, app_name, version, formula_content)
    except AppCreateError as error:
        raise AppEntityInstallError(error)
    if override_entrypoints is None:
        conflicted_aliases = DatabaseGateway.get_conflicted_entrypoints(
            app['entrypoints'])
        if conflicted_aliases:
            raise EntryPointsConflicted(app_name, conflicted_aliases)
    elif override_entrypoints is False:
        app['entrypoints'] = deactive_entrypoints(
            app['entrypoints'], conflicted_aliases)

    shims = generate_app_shims(app)

    SystemGateway.store_app_shims(shims)
    DatabaseGateway.store_app(app)
    return app


def uninstall_app(DatabaseGateway, SystemGateway, DockerServiceGateway,
                  app_name):
    try:
        app_id = DatabaseGateway.get_app_id(app_name)
    except DatabaseGateway.AppNotExist:
        raise UninstallAppNotFound(app_name)

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
        raise ExecAppNotFound(app_name)
    shim = generate_shell_shim(app)
    SystemGateway.run_temporay_script(shim, arguments=arguments)