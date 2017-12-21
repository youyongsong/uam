from uam.settings import UamBaseException


class AppExecError(UamBaseException):
    pass


class AppExecNotFound(AppExecError):
    help_text = "{} not found, you may need to install it first."

    def __init__(self, name):
        self.name = name
        self.help_text = self.help_text.format(name)
        return super(AppExecNotFound, self).__init__()