import click

from . import tap
from . import app
from . import system


@click.group()
def uam():
    pass


@click.command()
@click.argument("app_name")
@click.option("--pinned", default="")
@click.pass_context
def install(ctx, app_name, pinned):
    ctx.forward(app.install)


@click.command()
@click.argument("app_name")
@click.option("--pinned", default="")
@click.pass_context
def uninstall(ctx, app_name, pinned):
    ctx.forward(app.uninstall)


@click.command()
@click.argument("app_name")
@click.option("--pinned", default="")
@click.pass_context
def shell(ctx, app_name, pinned):
    ctx.forward(app.exec_app)


@click.command()
@click.pass_context
def ls(ctx):
    ctx.forward(app.list_apps)


@click.command()
@click.argument("app_name")
@click.pass_context
def upgrade(ctx, app_name):
    ctx.forward(app.upgrade_app)


@click.command()
@click.pass_context
def init(ctx):
    ctx.forward(system.init)


uam.add_command(install)
uam.add_command(uninstall)
uam.add_command(shell)
uam.add_command(ls)
uam.add_command(upgrade)
uam.add_command(init)
uam.add_command(tap.tap)
uam.add_command(app.app)
uam.add_command(system.system)
