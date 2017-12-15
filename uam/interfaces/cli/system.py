import click

from uam.usecases import system as system_usecases

from .helper import ClickHelper as helper


@click.group()
def system():
    pass


@click.command()
@helper.handle_exception()
def init():
    click.echo("initializing uam environment")
    system_usecases.initialize()
    helper.echo_success("uam environment setup.")


system.add_command(init)
