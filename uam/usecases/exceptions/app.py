from uam.settings import UamBaseException


class AppNameFormatInvalid(UamBaseException):
    help_text = "{} does not match app_name's format."

    def __init__(self, app_name):
        self.app_name = app_name
        self.help_text = self.help_text.format(app_name)
        super(AppNameFormatInvalid, self).__init__()

class AppTapsNotFound(UamBaseException):
    help_text = """\
taps of {} does not exist, you can try to install add the \
taps, then install the app again.
"""

    def __init__(self, app_name):
        self.app_name = app_name
        self.help_text = self.help_text.format(app_name)
        super(AppTapsNotFound, self).__init__()


class AppAlreadyExist(UamBaseException):
    help_text = "{} is already installed before, you can not install it again."

    def __init__(self, app_name):
        self.app_name = app_name
        self.help_text = self.help_text.format(app_name)
        super(AppAlreadyExist, self).__init__()


class NoProperVersionMatched(UamBaseException):
    help_text = "the version {} you pinned does not have a matched formula."

    def __init__(self, version):
        self.version = version
        self.help_text = self.help_text.format(version)
        super(NoProperVersionMatched, self).__init__()


class NoValidVersion(UamBaseException):
    help_text = "all formulas inside the taps {} is bad named, the taps is bad."

    def __init__(self, taps_name):
        self.help_text = self.help_text.format(taps_name)
        super(NoValidVersion, self).__init__()


class AppFormulaNotFound(UamBaseException):
    help_text = "app {} does not have a matched formula in all avalibale taps."

    def __init__(self, app_name):
        self.app_name = app_name
        self.help_text = self.help_text.format(app_name)
        super(AppFormulaNotFound, self).__init__()


class AppFormulaMalformed(UamBaseException):
    help_text = """\
{}'s formula in taps {} is not a valid yaml, you should submit an issue \
to the owner of the taps.\
"""

    def __init__(self, app_name, taps_name):
        self.app_name = app_name
        self.taps_name = taps_name
        self.help_text = self.help_text.format(app_name, taps_name)
        super(AppFormulaMalformed, self).__init__()


class AppEntryPointsConflicted(UamBaseException):
    help_text = """\
some entrypoints specified in the app formula are conflicted with the entrypoints\
of installed apps. the conflicted entrypoints are: {}\ 
"""

    def __init__(self, conflicted_aliases):
        self.conflicted_aliases = conflicted_aliases
        self.help_text = self.help_text.format(' '.join(conflicted_aliases))
        super(AppEntryPointsConflicted, self).__init__()


class AppNotInstalled(UamBaseException):
    help_text = "{} is not installed yet, you need to install it first."

    def __init__(self, app_name, pinned_version=None):
        self.app_name = app_name
        self.pinned_version = pinned_version
        if not pinned_version:
            display_name = app_name
        else:
            display_name = f"{app_name}📌 {pinned_version}"
        self.help_text = self.help_text.format(display_name)
        super(AppNotInstalled, self).__init__()


class UpdateLocalTapApp(UamBaseException):
    help_text = ("{} is installed from from local tap, local tap app does not"
                 "support update function now.")

    def __init__(self, app_name):
        self.app_name = app_name
        self.help_text = self.help_text.format(app_name)
        super(UpdateLocalTapApp, self).__init__()


class NoNewVersionFound(UamBaseException):
    help_text = "current version {} is already the newest one, no need to upgrade."

    def __init__(self, version):
        self.version = version
        self.help_text = self.help_text.format(version)
        super(NoNewVersionFound, self).__init__()