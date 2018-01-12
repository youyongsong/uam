from invoke import task


def status(s):
    """Prints things in bold."""
    print("🏷️ \033[1m{0}\033[0m".format(s))


@task
def lint(ctx):
    """
    Lint code using flake8 tools.
    """
    status("linting code ...")
    ctx.run("flake8 --show-source --statistics --count")


@task(lint)
def install(ctx):
    """
    Install uam as a cli tool for local development.
    """
    status("installing uam ...")
    ctx.run("pip3 install --editable .")
    status("uam installed.")


@task
def test(ctx):
    """
    Run uam test cases.
    """
    status("begining to run test cases ...")


@task(lint)
def build(ctx):
    """
    Build uam project to a single executable file using pyinstaller.
    """
    status("building with pyinstaller ...")