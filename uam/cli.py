# -*- coding: utf-8 -*-
import click

from uam.core import initialize


'''
Todo Commands:
- info <app>
  Explore the infomation of specified app.
- update <app>
  Update the app to a higer version.
- doctor
  Examine the system to see if there is something misconfiged.
- regenerate <app>
  Regenerate the executable wrappers for the specified app. If no app
  specified, this command will regenerate all executable wrappers.
'''


@click.group()
def uam():
    pass


@click.command()
def init():
    click.echo("Initializing uam ...")
    initialize()
    click.echo("Successfully initialized uam.")


@click.command()
def import_db():
    click.echo("Not implemented yet...")


@click.command()
def export_db():
    click.echo("Not implemented yet...")


uam.add_command(init)
