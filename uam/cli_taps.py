import click
from tabulate import tabulate

from uam.app_service import (add_taps, remove_taps, list_taps, update_taps)
from uam.exceptions import *


@click.group()
def taps():
    pass


@click.command()
@click.argument("alias")
@click.argument("address")
@click.option("--priority", default=0)
def add(alias, address, priority):
    try:
        add_taps(alias, address, priority=priority)
    except TapsInvalid:
        return click.echo('😟  add taps failed.')
    except TapsAddError:
        return click.echo('😣  add taps failed, the following tips me be helpful:')
    click.echo(f'🍻🍻  {alias} added!')


@click.command()
@click.argument("alias")
def rm(alias):
    try:
        remove_taps(alias)
    except TapsRemoveInvalid:
        return click.echo('😟  rm taps failed.')
    except TapsRemoveError:
        return click.echo('😣  rm taps failed, the following tips me be helpful:')
    click.echo(f'🍻🍻  {alias} removed!')


@click.command()
def ls():
    click.echo(display_taps_list(list_taps()))


@click.command()
@click.argument("alias", default='')
def update(alias):
    try:
        update_taps(alias)
    except MultiTapsUpdateError:
        return click.echo('😣  some taps update failed, the following tips me be helpful:')
    except TapsUpdateError:
        return click.echo('😟  rm taps failed.')
    except TapsUpdateInvalid:
        return click.echo('😣  update taps failed, the following tips me be helpful:')
    click.echo(f'🍻🍻  all taps updated!')


taps.add_command(add)
taps.add_command(rm)
taps.add_command(ls)
taps.add_command(update)


def display_taps_list(taps_list):
    table = [
        [t['alias'], t['address'], t['priority']] for t in taps_list
    ]
    headers = ['alias', 'address', 'priority']
    return tabulate(table, headers, tablefmt="rst")
