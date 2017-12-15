import click

from .taps import taps
from .app import app
from .system import system


@click.group()
def uam():
    pass


uam.add_command(taps)
uam.add_command(app)
uam.add_command(system)
