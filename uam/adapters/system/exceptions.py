from uam.settings import UamBaseException, ErrorTypes


class SystemError(UamBaseException):
    type = ErrorTypes.SYSTEM_ERROR


class YamlFileNotExist(SystemError):
    code = 'yaml_not_found'
    type = ErrorTypes.USER_ERROR
    help_text = "yaml file '{}' not found in file system."

    def __init__(self, path):
        self.help_text = self.help_text.format(path)
        return super(YamlFileNotExist, self).__init__()
