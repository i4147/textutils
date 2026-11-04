class ImproperlyConfigured(Exception):
    pass


class DependencyError(Exception):
    pass


class ConnectionError(Exception):
    pass


class OTPCodeError(Exception):
    pass


class SQLRemoveError(Exception):
    pass


class ExecutionError(Exception):
    pass


class ValidationError(Exception):
    pass


class APIError(Exception):
    pass
