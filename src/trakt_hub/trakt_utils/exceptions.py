class ConnectionException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class ExecutorException(BaseException):
    def __init__(Self, *args):
        super().__init__(*args)


class FileException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class ConfigException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class ParserException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class CHException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class THException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class CLIException(BaseException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
