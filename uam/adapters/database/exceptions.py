from uam.settings import UamBaseException, ErrorTypes


class DatabaseError(UamBaseException):
    type = ErrorTypes.SYSTEM_ERROR


class AppNotExist(DatabaseError):
    code = 'app_not_found'
    type = ErrorTypes.USER_ERROR
    help_text = "app {} not found in database."

    def __init__(self, name):
        self.help_text = self.help_text.format(name)
        return super(AppNotExist, self).__init__()


class TapsAliasConflict(Exception):
    message = "{} is already existed in database."

    def __init__(self, alias):
        self.alias = alias
        self.message = self.message.format(alias)
        return super(TapsAliasConflict, self).__init__(self.message)


class TapsAddressConflict(Exception):
    message = "{} is already existed in database."

    def __init__(self, address):
        self.address = address
        self.message = self.message.format(address)
        return super(TapsAddressConflict, self).__init__(self.message)