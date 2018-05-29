import click
import crayons

from uam.settings import CURRENT_VENV
from uam.usecases import app as app_usecases
from uam.usecases.exceptions import app as app_excs
from uam.entities.app import AppStatus
from uam.adapters.database.gateway import DatabaseGateway
from uam.adapters.docker.gateway import DockerServiceGateway
from uam.adapters.system.gateway import SystemGateway

from .helper import ClickHelper as helper


@click.group()
def app():
    pass


@click.command()
@click.argument("app_name")
@click.option("--pinned", default="")
@helper.handle_errors()
def install(app_name, pinned):
    try:
        app = app_usecases.install_app(DatabaseGateway, SystemGateway,
                                       app_name, pinned_version=pinned,
                                       venv=CURRENT_VENV)
    except app_excs.AppEntryPointsConflicted as exc:
        if helper.confirm("Commands '{}' already exist, do you want to override them? "
                          .format(', '.join(exc.conflicted_aliases))):
            app = app_usecases.install_app(DatabaseGateway, SystemGateway,
                                           app_name, override_entrypoints=True,
                                           pinned_version=pinned, venv=CURRENT_VENV)
        else:
            app = app_usecases.install_app(DatabaseGateway, SystemGateway,
                                           app_name, override_entrypoints=False,
                                           pinned_version=pinned, venv=CURRENT_VENV)
    if helper.confirm(f"Do you want to download image {app['image']} now?"):
        app_usecases.download_app_image(DatabaseGateway, DockerServiceGateway,
                                        app["name"], pinned_version=pinned,
                                        venv=CURRENT_VENV)
    helper.echo_success(f"{app['name']} installed.")


@click.command()
@click.argument("app_name")
@click.option("--pinned", default="")
@helper.handle_errors()
def uninstall(app_name, pinned):
    app_usecases.uninstall_app(DatabaseGateway, SystemGateway,
                               DockerServiceGateway, app_name, pinned_version=pinned,
                               venv=CURRENT_VENV)
    helper.echo_success(f"{app_name} uninstalled.")


@click.command("shell")
@click.argument("app_name")
@click.option("--pinned", default="")
@helper.handle_errors()
def exec_app(app_name, pinned):
    app_usecases.exec_app(DatabaseGateway, SystemGateway, app_name,
                          pinned_version=pinned, venv=CURRENT_VENV)


@click.command("ls")
def list_apps():
    app_lst = app_usecases.list_apps(DatabaseGateway, venv=CURRENT_VENV)
    click.echo(display_app_list(app_lst))


@click.command("upgrade")
@click.argument("app_name")
@helper.handle_errors()
def upgrade_app(app_name):
    click.echo(f"upgrading app {app_name} ...")
    app_usecases.update_app(DatabaseGateway, SystemGateway, DockerServiceGateway,
                            app_name, venv=CURRENT_VENV)
    helper.echo_success(f"{app_name} upgraded.")


@click.command("active")
@click.argument("app_name")
@click.option("--pinned", default="")
@helper.handle_errors()
def active(app_name, pinned):
    click.echo(f"activing app {format_name(app_name, pinned)} ...")
    app_usecases.active_app(DatabaseGateway, SystemGateway, app_name, pinned,
                            venv=CURRENT_VENV)
    helper.echo_success(f"{format_name(app_name, pinned)} actived.")


@click.command()
@click.argument("app_name")
@click.argument("formula_path", default="")
@click.option("--pinned", default="")
@helper.handle_errors()
def reinstall(app_name, formula_path, pinned):
    click.echo(f"reinstalling app {format_name(app_name, pinned)} ...")
    app_usecases.reinstall_app(DatabaseGateway, SystemGateway, DockerServiceGateway,
                               app_name, pinned, venv=CURRENT_VENV, formula_path=formula_path)
    helper.echo_success(f"{format_name(app_name, pinned)} reinstalled.")


app.add_command(install)
app.add_command(uninstall)
app.add_command(exec_app)
app.add_command(list_apps)
app.add_command(upgrade_app)
app.add_command(active)
app.add_command(reinstall)


def format_name(app_name, pinned=None):
    if pinned:
        return f"{app_name}📌 {pinned}"
    else:
        return app_name


def display_app_list(app_lst):
    app_display_lst = []
    for name, versions in app_lst.items():
        sorted_versions = sorted(versions, key=lambda v: (v["pinned"], v["version"]))
        version_display_lst = []
        for v in sorted_versions:
            if v["status"] == AppStatus.Active:
                color_func = crayons.green
            elif v["status"] == AppStatus.SemiActive:
                color_func = crayons.yellow
            else:
                color_func = crayons.white
            if v["pinned"]:
                version_display_lst.append(str(color_func(v["pinned_version"])) + "📌 ")
            else:
                version_display_lst.append(str(color_func(v["version"])))
        versions_display_text = ", ".join(version_display_lst)
        app_display_text = f"{name}({versions_display_text})"
        app_display_lst.append(app_display_text)
    return "    ".join(app_display_lst)