import asyncio
import logging
import random
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set
import aiohttp
from .exceptions import AdtextHttpError, AdtextTimeoutError

logger = logging.getLogger("adtext_sdk")
NO_RETRY_STATUSES: Set[int] = {400, 401, 403, 404, 451}


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, threshold: int = 5, reset_seconds: float = 30.0):
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        if self._state == CircuitState.OPEN:
            import time

            if time.monotonic() - self._last_failure_time > self._reset_seconds:
                self._state = CircuitState.HALF_OPEN
                return False
            return True
        return False

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        import time

        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._threshold:
            self._state = CircuitState.OPEN

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count


class HttpClient:
    def __init__(
        self,
        base_url: str,
        timeout_ms: int = 2000,
        get_token: Optional[Callable[[], Optional[str]]] = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout_ms / 1000)
        self._get_token = get_token
        self._session: Optional[aiohttp.ClientSession] = None
        self._circuit = CircuitBreaker(threshold=5, reset_seconds=30.0)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        token = self._get_token() if self._get_token else None
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def get(self, path: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Any:
        url = self._base_url + path
        clean_params = {k: str(v) for k, v in (params or {}).items() if v is not None}
        return await self._request("GET", url, params=clean_params, headers=headers)

    async def post(self, path: str, body: Optional[Dict] = None, headers: Optional[Dict] = None) -> Any:
        return await self._request("POST", self._base_url + path, json=body, headers=headers)

    async def post_with_retry(
        self,
        path: str,
        body: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        max_attempts: int = 3,
        base_delay_ms: float = 1000.0,
    ) -> Any:
        for attempt in range(1, max_attempts + 1):
            try:
                return await self._request("POST", self._base_url + path, json=body, headers=headers)
            except AdtextHttpError as e:
                is_last = attempt == max_attempts
                is_permanent = e.status in NO_RETRY_STATUSES
                if is_permanent or is_last:
                    raise
                delay = (base_delay_ms / 1000) * (2 ** (attempt - 1))
                jitter = random.uniform(0, 0.2)
                logger.debug("Retry %d/%d after %.2fs", attempt, max_attempts, delay + jitter)
                await asyncio.sleep(delay + jitter)
            except AdtextTimeoutError:
                if attempt == max_attempts:
                    raise
                await asyncio.sleep(base_delay_ms / 1000)

    async def delete(self, path: str, headers: Optional[Dict] = None) -> Any:
        return await self._request("DELETE", self._base_url + path, headers=headers)

    async def _request(self, method: str, url: str, headers: Optional[Dict] = None, **kwargs) -> Any:
        if self._circuit.is_open:
            raise AdtextHttpError(
                503,
                "CIRCUIT_OPEN",
                f"Ad server unavailable. Circuit open after {self._circuit.failure_count} failures.",
            )
        display_url = url
        params = kwargs.get("params")
        if params:
            from yarl import URL

            display_url = str(URL(url).with_query(params))
        logger.debug("SDK Request: %s %s", method, display_url)
        full_headers = self._headers()
        if headers:
            full_headers.update(headers)
        session = await self._get_session()
        try:
            async with session.request(method, url, headers=full_headers, **kwargs) as resp:
                if resp.status == 204:
                    self._circuit.record_success()
                    return None
                body: Dict = {}
                try:
                    body = await resp.json()
                except Exception:
                    pass
                if not resp.ok:
                    if resp.status >= 500:
                        self._circuit.record_failure()
                    raise AdtextHttpError(
                        status=resp.status,
                        code=body.get("code", "HTTP_ERROR"),
                        message=body.get("message", f"HTTP {resp.status}"),
                        request_id=body.get("requestId"),
                    )
                self._circuit.record_success()
                return body
        except asyncio.TimeoutError:
            self._circuit.record_failure()
            raise AdtextTimeoutError(f"Request timed out: {method} {url}")
        except AdtextHttpError:
            raise
        except aiohttp.ClientError as e:
            self._circuit.record_failure()
            raise AdtextHttpError(0, "CONNECTION_ERROR", str(e))

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    @property
    def circuit(self) -> CircuitBreaker:
        return self._circuit
