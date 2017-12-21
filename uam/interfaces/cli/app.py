import click

from uam.usecases import app as app_usecases
from uam.usecases.exceptions import app as app_excs
from uam.usecases.exceptions import (AppInstallError, AppUninstallError,
                                     EntryPointsConflicted)
from uam.adapters.database.gateway import DatabaseGateway
from uam.adapters.docker.gateway import DockerServiceGateway
from uam.adapters.system.gateway import SystemGateway

from .helper import ClickHelper as helper


@click.group()
def app():
    pass


@click.command()
@click.argument("app_name")
@helper.handle_exception(AppInstallError)
def install(app_name):
    try:
        app = app_usecases.install_app(DatabaseGateway, SystemGateway,
                                       app_name)
    except EntryPointsConflicted as exc:
        val = helper.prompt("Commands '{}' already exist. "
                            "Type 'y' to override them, 'n' to ignore them"
                            .format(', '.join(exc.conflicted_aliases)))
        if val == 'y':
            app = app_usecases.install_app(app_name, override_entrypoints=True)
    helper.echo_success(f"{app['name']} installed.")


@click.command()
@click.argument("app_name")
@helper.handle_exception(AppUninstallError)
def uninstall(app_name):
    app_usecases.uninstall_app(DatabaseGateway, SystemGateway,
                               DockerServiceGateway, app_name)
    helper.echo_success(f"{app_name} uninstalled.")


@click.command("shell")
@click.argument("app_name")
@helper.handle_errors(user_errors=[app_excs.AppExecNotFound])
def exec_app(app_name):
    app_usecases.exec_app(DatabaseGateway, SystemGateway, app_name)


app.add_command(install)
app.add_command(uninstall)
app.add_command(exec_app)
