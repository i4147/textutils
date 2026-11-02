class TextfullyError(Exception):
    pass


class AuthenticationError(TextfullyError):
    pass


class APIError(TextfullyError):
    pass
