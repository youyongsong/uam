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
