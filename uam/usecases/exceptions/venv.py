from uam.settings import UamBaseException


class VenvAlreadyActived(UamBaseException):
    help_text = "venv {} is already actived, can not active it again."

    def __init__(self, venv_name):
        self.venv_name = venv_name
        self.help_text = self.help_text.format(venv_name)
        super(VenvAlreadyActived, self).__init__()


class VenvNotExist(UamBaseException):
    help_text = ("venv {venv_name} does not exist yet, you may need to create venv "
                 "using 'uam venv create {venv_name}'")

    def __init__(self, venv_name):
        self.venv_name = venv_name
        self.help_text = self.help_text.format(venv_name=venv_name)
        super(VenvNotExist, self).__init__()