from uam.settings import UamBaseException, ErrorTypes


class RecognizeAppError(UamBaseException):
    type = ErrorTypes.USER_ERROR


class TapsNotFound(RecognizeAppError):
    code = 'taps_not_found'
    type = ErrorTypes.USER_ERROR
    help_text = ("taps {taps_name} is not found, you can try to add it using "
                 "'uam taps add {taps_name}'")

    def __init__(self, name):
        self.help_text = self.help_text.format(taps_name=name)
        return super(TapsNotFound, self).__init__()


class AppNameInvalid(RecognizeAppError):
    code = 'app_name_invalid'
    type = ErrorTypes.USER_ERROR
    help_text = "{} is not a valid app name."

    def __init__(self, name):
        self.help_text = self.help_text.format(name)
        return super(AppNameInvalid, self).__init__()


class AppCreateError(UamBaseException):
    type = ErrorTypes.USER_ERROR


class FormulaMalformed(AppCreateError):
    code = 'app_formula_malformed'
    type = ErrorTypes.USER_ERROR
    help_text = "app's formula is not valid yaml file, error detail: {}"

    def __init__(self, err):
        self.help_text = self.help_text.format(err)
        return super(FormulaMalformed, self).__init__()


class VersionSelectError(UamBaseException):
    type = ErrorTypes.USER_ERROR


class NoValidVersion(VersionSelectError):
    code = 'no_valid_version'
    type = ErrorTypes.USER_ERROR
    help_text = "all versions are not valid."

    def __init__(self):
        return super(VersionSelectError, self).__init__()