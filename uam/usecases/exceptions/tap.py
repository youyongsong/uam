from uam.settings import UamBaseException, ErrorTypes


class TapAddError(UamBaseException):
    pass


class TapAddConflict(TapAddError):
    help_text = "{} is conflicted with existed taps."

    def __init__(self, tap):
        self.tap = tap
        self.help_text = self.help_text.format(tap)
        super(TapAddConflict, self).__init__()


class TapRemoveError(UamBaseException):
    pass


class TapRemoveBuiltin(TapRemoveError):
    help_text = "{} is builtin tap, can not be removed."

    def __init__(self, alias):
        self.alias = alias
        self.help_text = self.help_text.format(alias)
        super(TapRemoveBuiltin, self).__init__()


class TapRemoveNotFound(UamBaseException):
    help_text = "{} not found in database."

    def __init__(self, alias):
        self.alias = alias
        self.help_text = self.help_text.format(alias)
        super(TapRemoveNotFound, self).__init__()


class TapUpdateError(UamBaseException):
    pass