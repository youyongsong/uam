import click
from tabulate import tabulate

from uam.adapters.database.gateway import DatabaseGateway
from uam.usecases import taps as taps_usecases
from uam.usecases.taps_exceptions import (TapsAddError, TapsRemoveError,
                                          TapsListError, TapsUpdateError)

from .helper import ClickHelper as helper


@click.group()
def taps():
    pass


@click.command()
@click.argument("alias")
@click.argument("address")
@click.option("--priority", default=0)
@helper.handle_exception(TapsAddError)
def add(alias, address, priority):
    taps_usecases.add_taps(alias, address, priority=priority)
    helper.echo_success(f"{alias} added!")


@click.command()
@click.argument("alias")
@helper.handle_exception(TapsRemoveError)
def rm(alias):
    taps_usecases.remove_taps(alias)
    helper.echo_success(f'{alias} removed!')


@click.command()
@helper.handle_exception(TapsListError)
def ls():
    click.echo(
        display_taps_list(
            taps_usecases.list_taps(DatabaseGateway)))


@click.command()
@click.argument("alias", default='')
@helper.handle_exception(TapsUpdateError)
def update(alias):
    taps_usecases.update_taps(alias)
    helper.echo_success('all taps updated!')


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
