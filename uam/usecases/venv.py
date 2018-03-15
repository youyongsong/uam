import os

from uam.settings import VENVS_PATH


def create_venv():
    # create
    pass

def delete_venv():
    pass


def list_venv():
    pass


def active_venv():
    pass


def deactive_venv():
    pass

def get_venv_path(SystemGateway, venv):
    if not venv:
        return None
    venv_path = os.path.join(VENVS_PATH, venv)
    SystemGateway.assure_folder(venv_path)
    return venv_path