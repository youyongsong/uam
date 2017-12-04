# -*- coding: utf-8 -*-
import click

from uam.app_service import initialize, install_app, uninstall_app
from uam.exceptions import AppAlreadyExist, EntryPointConflict, AppNotFound


@click.group()
def uam():
    pass


@click.command()
def init():
    click.echo("Initializing uam ...")
    initialize()
    click.echo("Successfully initialized uam.")


@click.command()
@click.argument("app_name")
def install(app_name):
    click.echo("Installing app {}".format(app_name))
    try:
        app = install_app(app_name)
    except EntryPointConflict as exc:
        val = click.prompt("Commands {} already exist. "
                           "Type 'y' to override them, 'n' to ignore them"
                           .format(' '.join(exc.conflicted_entrypoints)))
        if val == 'y':
            try:
                app = install_app(app_name, override_entrypoints=True)
            except AppAlreadyExist:
                click.echo("{} already existed.".format(app_name))
                return
        else:
            return
    except AppAlreadyExist:
        click.echo("{} already existed.".format(app_name))
        return
    click.echo("Successfully installed {}".format(app_name))

    entrys = [entry.alias for entry in app.entrypoints]
    click.echo("The following commands are available now: \n{}".format(
        '\n'.join(['- {}'.format(entry) for entry in entrys])))


@click.command()
@click.argument("app_name")
def uninstall(app_name):
    click.echo("Uninstalling app {}".format(app_name))
    try:
        uninstall_app(app_name)
    except AppNotFound:
        click.echo("App {} not found.".format(app_name))
        raise
        return
    click.echo("Successfully uninstalled {}.".format(app_name))


uam.add_command(init)
uam.add_command(install)
uam.add_command(uninstall)
