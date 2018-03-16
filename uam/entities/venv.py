import logging
import os

from uam.settings import VENVS_PATH, UAM_VENV_VAR


logger = logging.getLogger(__name__)


def build_venv_path(venv_name):
    return os.path.join(VENVS_PATH, venv_name)


def generate_venv_shell_post_commands(venv_name, shell_path, path_var,
                                      ps1_var=None, disable_venv_prompt=False):
    venv_path = build_venv_path(venv_name)
    envvars = {
        UAM_VENV_VAR: venv_name,
        "PATH": ":".join([venv_path, path_var]),
    }
    if not disable_venv_prompt:
        envvars["PS1"] = f"({venv_name}) {ps1_var}"

    return [
        f'export {name}="{val}"'
        for name, val in envvars.items()
    ]