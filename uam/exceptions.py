class TapsInvalid(Exception):

    def __init__(self, err_msg):
        self.err_msg = err_msg
        return super(TapsInvalid, self).__init__(err_msg)


class TapsAddError(Exception):

    def __init__(self, err_msg, code):
        self.err_msg = err_msg
        self.code = code
        return super(TapsAddError, self).__init__(err_msg)


class TapsRemoveInvalid(Exception):

    def __init__(self, err_msg):
        self.err_msg = err_msg
        return super(TapsRemoveInvalid, self).__init__(err_msg)


class TapsRemoveError(Exception):

    def __init__(self, err_msg, code):
        self.err_msg = err_msg
        self.code = code
        return super(TapsRemoveError, self).__init__(err_msg)


class TapsUpdateInvalid(Exception):

    def __init__(self, err_msg):
        self.err_msg = err_msg
        return super(TapsUpdateInvalid, self).__init__(err_msg)


class TapsUpdateError(Exception):

    def __init__(self, err_msg, code):
        self.err_msg = err_msg
        self.code = code
        return super(TapsUpdateError, self).__init__(err_msg)


class MultiTapsUpdateError(Exception):

    def __init__(self, errors):
        self.errors = errors
        return super(MultiTapsUpdateError, self).__init__()


class EntryPointConflict(Exception):

    def __init__(self, entrypoints):
        self.conflicted_entrypoints = entrypoints
        return super(EntryPointConflict, self).__init__(
            'The fllowing entrypoints already existed: {}'.format(entrypoints))


class AppSourceNotExist(Exception):

    def __init__(self, source_path):
        self.source_path = source_path
        return super(AppSourceNotExist, self).__init__(
            'App {} not exist: {}'.format(source_path))


class MainfestInvalidYaml(Exception):

    def __init__(self):
        return super(MainfestInvalidYaml, self).__init__(
            "App's mainfest is not valid yaml format.")


class AppAlreadyExist(Exception):

    def __init__(self):
        return super(AppAlreadyExist, self).__init__("App alredy existed.")


class AppNotFound(Exception):

    def __init__(self, app_name):
        return super(AppNotFound, self).__init__(
            "App {} not found".format(app_name))
