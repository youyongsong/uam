from uam.settings import UamBaseException, ErrorTypes


class AppInstallError(UamBaseException):
    type = ErrorTypes.USER_ERROR


class AppUninstallError(UamBaseException):
    type = ErrorTypes.USER_ERROR


class AppEntityError(AppInstallError):

    def __init__(self, error):
        self.code = error.code
        self.help_text = error.help_text
        self.type = error.type
        return super(AppEntityError, self).__init__()


class AppExisted(AppInstallError):
    code = 'app_existed'
    type = ErrorTypes.USER_ERROR
    help_text = ("{} is already installed, if you want to force reinstall it, "
                 "you can take a look at 'uam reinstall' command.")

    def __init__(self, app_name):
        self.help_text = self.help_text.format(app_name)
        return super(AppExisted, self).__init__()


class FormulaNotFound(AppInstallError):
    code = 'formula_not_found'
    type = ErrorTypes.USER_ERROR
    help_text = '{} not found in all taps.'

    def __init__(self, app_name):
        self.help_text = self.help_text.format(app_name)
        return super(FormulaNotFound, self).__init__()


class EntryPointsConflicted(AppInstallError):
    code = 'entrypoints_conflicted'
    type = ErrorTypes.USER_ERROR
    help_text = ("the following entrypoints in {} are conflicted with "
                 "installed app:\n {}")

    def __init__(self, app_name, conflicted_aliases):
        self.conflicted_aliases = conflicted_aliases
        self.help_text = self.help_text.format(app_name,
                                               ' '.join(conflicted_aliases))
        return super(EntryPointsConflicted, self).__init__()


class UninstallAppNotFound(AppUninstallError):
    code = 'uninstall_app_not_found'
    help_text = 'app {} does not exist.'

    def __init__(self, app_name):
        self.help_text = self.help_text.format(app_name)
        return super(UninstallAppNotFound, self).__init__()
