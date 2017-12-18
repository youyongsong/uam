import click

from uam.adapters.database.gateway import DatabaseGateway
from uam.adapters.docker.gateway import DockerServiceGateway
from uam.adapters.system.gateway import SystemGateway
from uam.usecases import system as system_usecases

from .helper import ClickHelper as helper


@click.group()
def system():
    pass


@click.command()
@helper.handle_exception()
def init():
    click.echo("initializing uam environment")
    system_usecases.initialize(SystemGateway, DatabaseGateway,
                               DockerServiceGateway)
    helper.echo_success("uam environment setup.")


system.add_command(init)