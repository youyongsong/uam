import logging

import os
import stat
import uuid
import subprocess
import sys

from uam.settings import BIN_PATH, TEMP_PATH


logger = logging.getLogger(__name__)


class SystemGateway:

    @staticmethod
    def store_app_shims(shims):
        for name, content in shims.items():
            target_path = os.path.join(BIN_PATH, name)
            logger.info(f'creating shim file: {target_path}')
            with open(target_path, 'w') as f_handler:
                f_handler.write(content)

            st = os.stat(target_path)
            os.chmod(target_path, st.st_mode | stat.S_IEXEC)

    @staticmethod
    def delete_app_shims(shim_names):
        for n in shim_names:
            target_path = os.path.join(BIN_PATH, n)
            logger.info(f'removing shim file: {target_path}')
            try:
                os.remove(target_path)
            except FileNotFoundError:
                logger.warning('{} not found'.format(target_path))
            else:
                logger.info('{} removed.'.format(target_path))

    @staticmethod
    def run_temporay_script(shim, commands=''):
        target_path = os.path.join(TEMP_PATH, f'uam-shell-{uuid.uuid4()}')
        logger.debug(f'creating temporay script {target_path}')
        with open(target_path, 'w') as f_handler:
            f_handler.write(shim)
        try:
            subprocess.run(f'{sys.executable} {target_path} {commands}',
                           shell=True)
        finally:
            logger.debug(f'deleting temporay script {target_path}')
            os.remove(target_path)
