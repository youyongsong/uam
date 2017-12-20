from uam.settings import UamBaseException, ErrorTypes

class TapsAddError(UamBaseException):
    pass

class TapsAddConflict(TapsAddError):
    type = ErrorTypes.USER_ERROR
    help_text = "{} is conflicted with existed taps."

    def __init__(self, taps):
        self.taps = taps
        self.help_text = self.help_text.format(taps)
        return super(TapsAddConflict, self).__init__()


class TapsRemoveError(UamBaseException):
    pass


class TapsRemoveBuiltin(TapsRemoveError):
    help_text = "{} is builtin taps, can not be removed."

    def __init__(self, alias):
        self.alias = alias
        self.help_text = self.help_text.format(alias)
        return super(TapsRemoveBuiltin, self).__init__()


class TapsRemoveNotFond(UamBaseException):
    help_text = "{} not found in database."

    def __init__(self, alias):
        self.alias = alias
        self.help_text = self.help_text.format(alias)
        return super()


class TapsUpdateError(UamBaseException):
    pass