class RecognizeAppError(ValueError):
    pass


class TapsNotFound(RecognizeAppError):
    pass


class AppNameInvalid(RecognizeAppError):
    pass


class AppCreateError(Exception):
    pass


class FormulaMalformed(AppCreateError):
    pass


class VersionSelectError(Exception):
    pass


class NoValidVersion(VersionSelectError):
    pass


class PinnedVersionNotExist(VersionSelectError):
    pass