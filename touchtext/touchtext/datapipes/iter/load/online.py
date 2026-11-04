import warnings
import requests
import urllib

from typing import Any, Dict, Iterator, Optional, Tuple
from torch.utils.data import functional_datapipe, IterDataPipe
from torch.utils.data.datapipes.utils.common import StreamWrapper


def _get_proxies() -> Optional[Dict[str, str]]:
    import os

    if os.name == "nt":
        proxies = urllib.request.getproxies()
        address = proxies.get("https")
        if address and address.startswith("https"):
            address = "http" + address[5:]
            proxies["https"] = address
            return proxies
    return None


def _get_response_from_http(
    url: str, *, timeout: Optional[float], **query_params: Optional[Dict[str, Any]]
) -> Tuple[str, StreamWrapper]:
    with requests.Session() as session:
        proxies = _get_proxies()
        r = session.get(url, timeout=timeout, proxies=proxies, stream=True, **query_params)
    r.raise_for_status()
    return url, StreamWrapper(r.raw)


@functional_datapipe("read_from_http")
class HTTPReaderIterDataPipe(IterDataPipe[Tuple[str, StreamWrapper]]):
    def __init__(
        self,
        source_datapipe: IterDataPipe[str],
        timeout: Optional[float] = None,
        skip_on_error: bool = False,
        **kwargs: Optional[Dict[str, Any]],
    ) -> None:
        self.source_datapipe: IterDataPipe[str] = source_datapipe
        self.timeout = timeout
        self.skip_on_error = skip_on_error
        self.query_params = kwargs

    def __iter__(self) -> Iterator[Tuple[str, StreamWrapper]]:
        for url in self.source_datapipe:
            try:
                yield _get_response_from_http(url, timeout=self.timeout, **self.query_params)
            except Exception as e:
                if self.skip_on_error:
                    warnings.warn(f"{e}, skipping...")
                else:
                    raise

    def __len__(self) -> int:
        return len(self.source_datapipe)
