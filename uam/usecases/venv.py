import logging

from uam.settings import VENVS_PATH, UAM_VENV_VAR, UAM_DISABLE_VENV_PROMPT_VAR
from uam.usecases.exceptions.venv import VenvAlreadyActived, VenvNotExist
from uam.entities.venv import build_venv_path, generate_venv_shell_post_commands


logger = logging.getLogger(__name__)


def create_venv(SystemGateway, venv_name):
    venv_path = build_venv_path(venv_name)
    SystemGateway.assure_folder(venv_path)


def delete_venv(DatabaseGateway, SystemGateway, DockerServiceGateway, venv_name):
    from uam.usecases.app import list_apps, uninstall_app  # noqa, avoid circula reference

    venv_path = build_venv_path(venv_name)
    logger.info(f"uninstalling apps inside venv {venv_name} ...")
    app_lst = list_apps(DatabaseGateway, venv=venv_name)
    for name, apps in app_lst.items():
        for app in apps:
            if not app["pinned_version"]:
                logger.info(f"uninstalling app {name} ...")
            else:
                logger.info(f"uninstalling app {name}📌 {app['pinned_version']} ...")
            uninstall_app(DatabaseGateway, SystemGateway, DockerServiceGateway,
                          name, pinned_version=app["pinned_version"], venv=venv_name)
    logger.info(f"deleting venv folder of {venv_name} ...")
    SystemGateway.remove_folder(venv_path)


def list_venvs(SystemGateway):
    return SystemGateway.list_folders(VENVS_PATH)


def active_venv(SystemGateway, venv_name, current_venv=""):
    if venv_name == current_venv:
        raise VenvAlreadyActived(venv_name)
    if venv_name not in list_venvs(SystemGateway):
        raise VenvNotExist(venv_name)

    logger.info(f"preparing envvars for venv {venv_name} ...")
    path_var = SystemGateway.getenv("PATH")
    if not SystemGateway.getenv(UAM_DISABLE_VENV_PROMPT_VAR):
        disable_venv_prompt = False
        ps1_var = SystemGateway.get_ps1_str()
    else:
        disable_venv_prompt = True
        ps1_var = ""

    shell_path = SystemGateway.getenv("SHELL")
    venv_shell_post_commands = generate_venv_shell_post_commands(
        venv_name, shell_path, path_var, ps1_var=ps1_var,
        disable_venv_prompt=disable_venv_prompt
    )

    logger.info(f"starting venv({venv_name}) shell ...")
    venv_help_msg = (f"# you are now inside venv({venv_name}) shell now\n"
                     "# if you want to quit this venv shell, press 'exit'.\n")
    SystemGateway.run_shell(shell_path, post_commands=venv_shell_post_commands,
                            post_msg=venv_help_msg)


def get_venv_path(SystemGateway, venv):
    if not venv:
        return None
    venv_path = build_venv_path(venv)
    SystemGateway.assure_folder(venv_path)
    return venv_path