class AdtextError(Exception):
    pass


class AdtextHttpError(AdtextError):
    def __init__(self, status: int, code: str, message: str, request_id: str | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.request_id = request_id

    def __repr__(self):
        return f"AdtextHttpError(status={self.status}, code={self.code!r}, message={str(self)!r})"


class AdtextTimeoutError(AdtextError):
    pass


class AdtextNotInitializedError(AdtextError):
    pass


class AdtextConsentError(AdtextError):
    pass
