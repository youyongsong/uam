import traceback
import functools

import click

from uam.settings import UamUnknownError, ErrorTypes, DEBUG


class ClickHelper:

    @staticmethod
    def handle_exception(*exceptions):
        def exception_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as exc:
                    ClickHelper.echo_errors(exc)
                except Exception as exc:
                    ClickHelper.echo_errors(UamUnknownError(exc))
            return wrapper
        return exception_decorator

    @staticmethod
    def handle_errors(user_errors=[], resource_errors=[]):
        def exception_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except tuple(user_errors) as exc:
                    exc.type = ErrorTypes.USER_ERROR
                    ClickHelper.echo_errors(exc)
                except tuple(resource_errors) as exc:
                    exc.type = ErrorTypes.SYSTEM_ERROR
                    ClickHelper.echo_errors(exc)
                except Exception as exc:
                    exc.type = ErrorTypes.UNKNOWN_ERROR
                    ClickHelper.echo_errors(exc)
            return wrapper
        return exception_decorator

    @staticmethod
    def prompt(msg):
        return click.prompt("🤔  " + msg)

    @staticmethod
    def echo_success(msg):
        return click.echo("🍻🍻  "+msg)

    @staticmethod
    def echo_errors(error):
        if error.type == ErrorTypes.USER_ERROR:
            click.echo(f'😟  {error}')
        if error.type == ErrorTypes.SYSTEM_ERROR:
            click.echo(f'🏚 ️ {error}')
        if error.type == ErrorTypes.UNKNOWN_ERROR:
            click.echo(f'🐞  {error}')