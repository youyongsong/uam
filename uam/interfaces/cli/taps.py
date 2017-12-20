import click
from tabulate import tabulate

from uam.adapters.system.gateway import SystemGateway
from uam.adapters.database.gateway import DatabaseGateway
from uam.usecases import taps as taps_usecases
from uam.usecases.exceptions import taps as taps_excs

from .helper import ClickHelper as helper


@click.group()
def taps():
    pass


@click.command()
@click.argument("alias")
@click.argument("address")
@click.option("--priority", default=0)
@helper.handle_exception(taps_excs.TapsAddError)
def add(alias, address, priority):
    click.echo(f"adding taps {alias} using address {address} ...")
    taps_usecases.add_taps(SystemGateway, DatabaseGateway,
                           alias, address, priority=priority)
    helper.echo_success(f"{alias} added!")


@click.command()
@click.argument("alias")
@helper.handle_exception(taps_excs.TapsRemoveError)
def rm(alias):
    click.echo(f"removing taps {alias} ...")
    taps_usecases.remove_taps(SystemGateway, DatabaseGateway, alias)
    helper.echo_success(f'{alias} removed!')


@click.command()
def ls():
    click.echo(f"listing all added taps ...")
    click.echo(
        display_taps_list(
            taps_usecases.list_taps(DatabaseGateway)))


@click.command()
@click.argument("alias", default='')
def update(alias):
    click.echo(f"updateing taps {alias} ...")
    taps_usecases.update_taps(SystemGateway, DatabaseGateway, alias)
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
