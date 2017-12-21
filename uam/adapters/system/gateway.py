import logging
import os
import stat
import uuid
import subprocess
import sys
import shutil

from uam.settings import BIN_PATH, TEMP_PATH
from uam.adapters.system.exceptions import YamlFileNotExist


logger = logging.getLogger(__name__)


class SystemGateway:

    @staticmethod
    def isfolder(path):
        return os.path.isdir(path)

    @staticmethod
    def assure_folder(path):
        if not os.path.exists(path):
            logger.info(f"creating folder {path}...")
            os.makedirs(path)

    @staticmethod
    def clone_repo(target_path, target_name, git_addr):
        curdir = os.path.abspath(os.curdir)
        try:
            os.chdir(target_path)
            if os.path.exists(os.path.join(target_path, target_name)):
                logger.info(f"{target_path}/{target_name} already existed, no need to clone.")
                return
            logger.info(f"cloning repo {git_addr}")
            command = f"git clone --depth 1 {git_addr} {target_name}"
            subprocess.run(command, shell=True, check=True)
        finally:
            os.chdir(curdir)

    @staticmethod
    def remove_repo(repo_path):
        shutil.rmtree(repo_path)

    @staticmethod
    def update_repo(repo_path, git_addr):
        curdir = os.path.abspath(os.curdir)
        try:
            os.chdir(repo_path)
            command = f"git pull {git_addr}"
            subprocess.run(command, shell=True, check=True)
        finally:
            os.chdir(curdir)

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
    def run_temporay_script(shim, arguments=''):
        target_path = os.path.join(TEMP_PATH, f'uam-shell-{uuid.uuid4()}')
        logger.info(f'creating temporay script {target_path}')
        with open(target_path, 'w') as f_handler:
            f_handler.write(shim)
        try:
            subprocess.run(f'{sys.executable} {target_path} {arguments}',
                           shell=True)
        finally:
            logger.info(f'deleting temporay script {target_path}')
            os.remove(target_path)

    @staticmethod
    def list_yaml_names(folder):
        return [
            os.path.splitext(f)[0]
            for f in os.listdir(folder)
            if os.path.splitext(f)[1] in (".yaml", ".yml")
        ]

    @staticmethod
    def read_yaml_content(path):
        for ext in ("", ".yaml", ".yml"):
            new_path = path + ext
            if os.path.isfile(new_path):
                path = new_path
                break
        else:
            raise YamlFileNotExist(path)
        
        with open(path, "r") as f_handler:
            content = f_handler.read()
        return content