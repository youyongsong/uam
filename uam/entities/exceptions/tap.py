class TapValidiateError(Exception):
    pass


class AliasConflict(TapValidiateError):
    message = "tap name {} is conflicted with builtin taps."

    def __init__(self, alias):
        self.alias = alias
        self.message = self.message.format(alias)
        super(AliasConflict, self).__init__(self.message)


class AddressConflict(TapValidiateError):
    message = "tap address {} is conflicted with builtin taps."

    def __init__(self, address):
        self.address = address
        self.message = self.message.format(address)
        super(AddressConflict, self).__init__(self.address)