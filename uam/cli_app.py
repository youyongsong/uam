import click
from uam.click_helper import ClickHelper as helper

from uam.usecases.app import install_app
from uam.usecases.exceptions import AppInstallError, EntryPointsConflicted
from uam.adapters import TapsGateway, AppGateway


@click.group()
def app():
    pass


@click.command()
@click.argument("app_name")
@helper.handle_exception(AppInstallError)
def install(app_name):
    try:
        app = install_app(AppGateway, TapsGateway, app_name)
    except EntryPointsConflicted as exc:
        val = helper.prompt("Commands '{}' already exist. "
                            "Type 'y' to override them, 'n' to ignore them"
                            .format(', '.join(exc.conflicted_aliases)))
        if val == 'y':
            app = install_app(app_name, override_entrypoints=True)
    helper.echo_success(f"{app['name']} installed.")


app.add_command(install)
