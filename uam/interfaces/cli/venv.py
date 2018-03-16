import click

from uam.settings import CURRENT_VENV
from uam.usecases import venv as venv_usecases
from uam.adapters.system.gateway import SystemGateway
from uam.adapters.docker.gateway import DockerServiceGateway
from uam.adapters.database.gateway import DatabaseGateway

from .helper import ClickHelper as helper


@click.group()
def venv():
    pass


@click.command()
@click.argument("venv_name")
@helper.handle_errors()
def create(venv_name):
    venv_usecases.create_venv(SystemGateway, venv_name)
    helper.echo_success(f"venv {venv_name} created.")


@click.command()
@click.argument("venv_name")
@helper.handle_errors()
def delete(venv_name):
    venv_usecases.delete_venv(DatabaseGateway, SystemGateway, DockerServiceGateway,
                              venv_name)
    helper.echo_success(f"venv {venv_name} deleted.")


@click.command()
@helper.handle_errors()
def ls():
    venvs = venv_usecases.list_venvs(SystemGateway)
    click.echo("  ".join(venvs))


@click.command()
@click.argument("venv_name")
@helper.handle_errors()
def active(venv_name):
    venv_usecases.active_venv(SystemGateway, venv_name,
                              current_venv=CURRENT_VENV)
    click.echo(f"{venv_name} deactived.")


venv.add_command(create)
venv.add_command(delete)
venv.add_command(ls)
venv.add_command(active)