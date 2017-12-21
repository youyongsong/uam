from uam.settings import UamBaseException


class AppInstallError(UamBaseException):
    pass


class AppNameFormatInvalid(AppInstallError):
    help_text = "{} does not match app_name's format."

    def __init__(self, error, app_name):
        self.app_name = app_name
        self.help_text = self.help_text.format(app_name)
        return super(AppNameFormatInvalid, self).__init__()

class AppTapsNotFound(AppInstallError):
    help_text = """\
taps of {} does not exist, you can try to install add the \
taps, then install the app again.
"""

    def __init__(self, app_name):
        self.app_name = app_name
        self.help_text = self.help_text.format(app_name)
        return super(AppTapsNotFound, self).__init__()


class AppAlreadyExist(AppInstallError):
    help_text = "{} is already installed before, you can not install it again."

    def __init__(self, app_name):
        self.app_name = app_name
        self.help_text = self.help_text.format(app_name)
        return super(AppAlreadyExist, self).__init__()


class NoProperVersionMatched(AppInstallError):
    help_text = "the version {} you pinned does not have a matched formula."

    def __init__(self, version):
        self.version = version
        self.help_text = self.help_text.format(version)
        return super(NoProperVersionMatched, self).__init__()


class NoValidVersion(AppInstallError):
    help_text = "all formulas inside the taps {} is bad named, the taps is bad."

    def __init__(self, taps_name):
        self.help_text = self.help_text.format(taps_name)
        return super(NoValidVersion, self).__init__()


class AppFormulaNotFound(AppInstallError):
    help_text = "app {} does not have a matched formula in all avalibale taps."

    def __init__(self, app_name):
        self.app_name = app_name
        self.help_text = self.help_text.format(app_name)
        return super(AppFormulaNotFound, self).__init__()


class AppFormulaMalformed(AppInstallError):
    help_text = """\
{}'s formula in taps {} is not a valid yaml, you should submit an issue \
to the owner of the taps.\
"""

    def __init__(self, app_name, taps_name):
        self.app_name = app_name
        self.taps_name = taps_name
        self.help_text = self.help_text.format(app_name, taps_name)
        return super(AppFormulaMalformed, self).__init__()


class AppEntryPointsConflicted(AppInstallError):
    help_text = """\
some entrypoints specified in the app formula are conflicted with the entrypoints\
of installed apps. the conflicted entrypoints are: {}\ 
"""

    def __init__(self, conflicted_aliases):
        self.conflicted_aliases = conflicted_aliases
        self.help_text = self.help_text.format(' '.join(conflicted_aliases))
        return super(AppEntryPointsConflicted, self).__init__()


class AppExecError(Exception):
    pass


class AppExecNotFound(AppExecError):
    help_text = "{} is not installed yet, you need to install it first."

    def __init__(self, app_name):
        self.app_name = name
        self.help_text = self.help_text.format(app_name)
        return super(AppExecNotFound, self).__init__()


class AppUninstallError(Exception):
    pass


class AppUninstallNotFound(AppUninstallError):
    help_text = "you have not installed app {}, no need to uninstall it."

    def __init__(self, app_name):
        self.app_name = app_name
        self.help_text = self.help_text.format(app_name)
        return super(AppUninstallNotFound, self).__init__()