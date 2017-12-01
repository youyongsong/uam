class EntryPointConflict(Exception):

    def __init__(self, entrypoints):
        self.conflicted_entrypoints = entrypoints
        super(EntryPointConflict, self).__init__('The fllowing entrypoints '
                                                 'already existed: {}'.format(entrypoints))


class AppSourceNotExist(Exception):

    def __init__(self, source_path):
        self.source_path = source_path
        super(AppSourceNotExist, self).__init__('App {} not exist: {}'.format(source_path))


class MainfestInvalidYaml(Exception):

    def __init__(self):
        super(MainfestInvalidYaml, self).__init__("App's mainfest is not valid yaml format.")


class AppAlreadyExist(Exception):

    def __init__(self):
        super(AppAlreadyExist, self).__init__("App alredy existed.")
