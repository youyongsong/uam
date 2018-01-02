import click

from .tap import tap
from .app import app
from .system import system


@click.group()
def uam():
    pass


uam.add_command(tap)
uam.add_command(app)
uam.add_command(system)
