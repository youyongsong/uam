# -*- coding: utf-8 -*-
import click

from uam.app_service import initialize, install_app
from uam.exceptions import EntryPointConflict


'''
Todo Commands:
- uninstall <app>
- active <app>  # active the app's entrypoints (will override conflicted entrypoints)
- info <app>
  Explore the infomation of specified app.
- update <app>
  Update the app to a higer version.
- doctor
  Examine the system to see if there is something misconfiged.
- regenerate <app>
  Regenerate the executable wrappers for the specified app. If no app
  specified, this command will regenerate all executable wrappers.
- import <file-name>
  import data from a file.
- export <file-name>
  export db to specified file.
'''


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
        install_app(app_name)
    except EntryPointConflict as exc:
        val = click.prompt("Commands {} already exist. "
                           "Type 'y' to override them, 'n' to ignore them"
                           .format(' '.join(exc.conflicted_entrypoints)))
        if val == 'y':
            install_app(app_name, override_entrypoints=True)
        else:
            return
    click.echo("Successfully installed {}".format(app_name))
    click.echo("The following commands are available now: \n{}")


uam.add_command(init)
uam.add_command(install)
