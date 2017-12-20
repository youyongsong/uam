class TapsValidiateError(Exception):
    pass


class AliasConflict(TapsValidiateError):
    message = "taps name {} is conflicted with builtin taps."

    def __init__(self, alias):
        self.alias = alias
        self.message = self.message.format(alias)
        return super(AliasConflicted, self).__init__(self.message)


class AddressConflict(TapsValidiateError):
    message = "taps address {} is conflicted with builtin taps."

    def __init__(self, address):
        self.address = address
        self.message = self.message.format(address)
        return super(AddressConflicted, self).__init__(self.address)