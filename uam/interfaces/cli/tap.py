import click
from tabulate import tabulate

from uam.adapters.system.gateway import SystemGateway
from uam.adapters.database.gateway import DatabaseGateway
from uam.usecases import tap as tap_usecases
from uam.usecases.exceptions import tap as tap_excs

from .helper import ClickHelper as helper


@click.group()
def tap():
    pass


@click.command()
@click.argument("alias")
@click.argument("address")
@click.option("--priority", default=0)
@helper.handle_exception(tap_excs.TapAddError)
def add(alias, address, priority):
    click.echo(f"adding tap {alias} using address {address} ...")
    tap_usecases.add_tap(SystemGateway, DatabaseGateway,
                         alias, address, priority=priority)
    helper.echo_success(f"{alias} added!")


@click.command()
@click.argument("alias")
@helper.handle_exception(tap_excs.TapRemoveError)
def rm(alias):
    click.echo(f"removing tap {alias} ...")
    tap_usecases.remove_tap(SystemGateway, DatabaseGateway, alias)
    helper.echo_success(f'{alias} removed!')


@click.command()
def ls():
    click.echo(f"listing all added taps ...")
    click.echo(
        display_tap_list(
            tap_usecases.list_taps(DatabaseGateway)))


@click.command()
@click.argument("alias", default='')
def update(alias):
    click.echo(f"updateing tap {alias} ...")
    tap_usecases.update_tap(SystemGateway, DatabaseGateway, alias)
    helper.echo_success('all taps updated!')


tap.add_command(add)
tap.add_command(rm)
tap.add_command(ls)
tap.add_command(update)


def display_tap_list(tap_list):
    table = [
        [t['alias'], t['address'], t['priority']] for t in tap_list
    ]
    headers = ['alias', 'address', 'priority']
    return tabulate(table, headers, tablefmt="rst")
