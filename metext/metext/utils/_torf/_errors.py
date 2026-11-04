class TorfError(Exception):
    def __init__(self, msg, *posargs, **kwargs):
        super().__init__(msg)
        self.posargs = posargs
        self.kwargs = kwargs


class URLError(TorfError):
    def __init__(self, url):
        self._url = url
        super().__init__("{url}: Invalid URL".format(url=url), url)

    @property
    def url(self):
        return self._url


class MagnetError(TorfError):
    def __init__(self, uri, reason=None):
        self._uri = uri
        self._reason = reason
        if reason is not None:
            super().__init__("{uri}: {reason}".format(uri=uri, reason=reason), uri, reason=reason)
        else:
            super().__init__("{uri}: Invalid magnet URI".format(uri=uri), uri)

    @property
    def uri(self):
        return self._uri

    @property
    def reason(self):
        return self._reason
