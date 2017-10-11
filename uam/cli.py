import click


@click.group()
def uam():
    pass


@click.command()
def hello():
    click.echo("Hello World, I'm uam.")


uam.add_command(hello)
