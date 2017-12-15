import logging
import os

from uam.usecases.taps import list_taps
from uam.usecases.exceptions import (AppExisted, FormulaNotFound,
                                     EntryPointsConflicted, AppEntityError)
from uam.entities.app import (recognize_app_name, create_app,
                              deactive_entrypoints, generate_app_shims)
from uam.entities.exceptions import RecognizeAppError, AppCreateError


logger = logging.getLogger(__name__)


def install_app(AppGateway, TapsGateway, app_name, override_entrypoints=None):
    try:
        source_type, app_name, formula_lst = recognize_app_name(
            app_name, list_taps(TapsGateway))
    except RecognizeAppError as error:
        raise AppEntityError(error)

    if AppGateway.app_exists(app_name):
        raise AppExisted(app_name)

    for formula in formula_lst:
        taps_name, formula_path = formula['taps_name'], formula['path']
        if not os.path.isfile(formula_path):
            continue
        logger.info(f'installing {app_name} from taps {taps_name}')
        with open(formula_path, 'r') as f_handler:
            formula_content = f_handler.read()
            break
    else:
        raise FormulaNotFound(app_name)

    try:
        app = create_app(source_type, taps_name, app_name, formula_content)
    except AppCreateError as error:
        raise AppEntityError(error)
    if override_entrypoints is None:
        conflicted_aliases = AppGateway.get_conflicted_entrypoints(
            app['entrypoints'])
        if conflicted_aliases:
            raise EntryPointsConflicted(app_name, conflicted_aliases)
    elif override_entrypoints is False:
        app['entrypoints'] = deactive_entrypoints(
            app['entrypoints'], conflicted_aliases)

    shims = generate_app_shims(app)

    AppGateway.store_app_shims(shims)
    AppGateway.store_app(app)
    return app
