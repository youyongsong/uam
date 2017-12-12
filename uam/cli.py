import sys

import click
from tabulate import tabulate

from uam.app_service import (initialize, install_app, uninstall_app, info_app,
                             retrieve_alias, exec_shell)
from uam.exceptions import *

from .cli_taps import taps


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
        return
    click.echo("Successfully uninstalled {}.".format(app_name))


@click.command()
@click.argument("app_name")
def info(app_name):
    try:
        app = info_app(app_name)
    except AppNotFound:
        click.echo("App {} not found.".format(app_name))
        return
    click.echo(display_app(app))


@click.command('list')
@click.option("--lst", "-l", is_flag=True, default=False)
def list_alias(lst):
    aliases = retrieve_alias()
    if lst:
        click.echo(display_entrypoints(aliases))
    else:
        click.echo(' '.join([e['alias'] for e in aliases]))
    return


@click.command('shell')
@click.argument('app_name')
@click.option("--uam-port")
def shell(app_name, **kwargs):
    ext_args = sys.argv[3:]
    commands = ''
    if ext_args:
        commands = ' '.join(ext_args)
    exec_shell(app_name, commands=commands)


uam.add_command(taps)
uam.add_command(init)
uam.add_command(install)
uam.add_command(uninstall)
uam.add_command(info)
uam.add_command(list_alias)
uam.add_command(shell)


def display_app(app):
    content = '{}\n\n'.format(app.description)

    content += 'version: {}\n'.format(app.version)
    content += 'image: {}\n'.format(app.image)
    content += '\n'

    content += 'entrypoints:\n'
    for entry in app.entrypoints:
        if entry.enabled:
            content += '{} --> {} {}\n'.format(entry.alias,
                                               entry.container_entrypoint,
                                               entry.container_arguments)
        else:
            content += '{} (inactive)\n'.format(entry.alias)
    content += '\n'

    content += 'configs:\n'
    for config in app.configs:
        content += '{} is mount on {}\n'.format(config.host_path,
                                                config.container_path)
    content += '\n'

    content += 'volumes:\n'
    for vol in app.volumes:
        content += '{} is mount on {}\n'.format(vol.name, vol.path)
    content += '\n'

    content += 'environments:\n'
    for k, v in app.environments.items():
        content += '{}={}\n'.format(k, v)

    return content.strip()


def display_entrypoints(entrypoints):
    table = [
        [e['alias'], '{}::{}'.format(e['app_source_type'], e['app_source'])]
        for e in entrypoints if e['enabled']
    ]
    headers = ['wrapper', 'app']
    return tabulate(table, headers, tablefmt="rst")
