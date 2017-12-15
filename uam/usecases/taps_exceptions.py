from uam.settings import UamBaseException, ErrorTypes


class TapsAddError(UamBaseException):
    type = ErrorTypes.USER_ERROR


class TapsRemoveError(UamBaseException):
    type = ErrorTypes.USER_ERROR


class TapsListError(UamBaseException):
    type = ErrorTypes.USER_ERROR


class TapsUpdateError(UamBaseException):
    type = ErrorTypes.USER_ERROR
