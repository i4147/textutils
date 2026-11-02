import asyncio
import logging
import time
from typing import Callable, Optional
from .http import HttpClient
from .types import JwtResponse

logger = logging.getLogger("adtext_sdk")


class TokenManager:
    def __init__(
        self,
        api_key: str,
        env: str,
        http: HttpClient,
        refresh_threshold_pct: int = 20,
        on_refresh: Optional[Callable[[str], None]] = None,
    ):
        self._api_key = api_key
        self._env = env
        self._http = http
        self._refresh_threshold_pct = refresh_threshold_pct
        self._on_refresh = on_refresh
        self._token: Optional[str] = None
        self._expires_at: float = 0.0
        self._refresh_task: Optional[asyncio.Task] = None
        self._refresh_in_flight: Optional[asyncio.Future] = None

    async def initialize(self) -> str:
        data = await self._http.get(
            "/sdk/v1/auth/jwt",
            params={"apiKey": self._api_key, "env": self._env},
        )
        resp = JwtResponse.from_dict(data)
        self._store(resp.token, resp.expires_in)
        return resp.token

    def get_token(self) -> Optional[str]:
        return self._token

    def is_valid(self) -> bool:
        return self._token is not None and time.time() < self._expires_at

    async def ensure_valid(self) -> Optional[str]:
        if self.is_valid():
            return self._token
        if self._refresh_in_flight is not None:
            return await self._refresh_in_flight
        loop = asyncio.get_event_loop()
        self._refresh_in_flight = loop.create_future()
        try:
            data = await self._http.post("/sdk/v1/auth/refresh")
            resp = JwtResponse.from_dict(data)
            self._store(resp.token, resp.expires_in)
            if self._on_refresh:
                self._on_refresh(resp.token)
            self._refresh_in_flight.set_result(self._token)
            return self._token
        except Exception as e:
            self._refresh_in_flight.set_exception(e)
            raise
        finally:
            self._refresh_in_flight = None

    async def revoke(self) -> None:
        self._cancel_refresh()
        self._refresh_in_flight = None
        try:
            await self._http.delete("/sdk/v1/auth/session")
        except Exception as e:
            logger.debug("Token revocation error (non-fatal): %s", e)
        finally:
            self._token = None
            self._expires_at = 0.0

    def _store(self, token: str, expires_in_seconds: int) -> None:
        self._token = token
        self._expires_at = time.time() + expires_in_seconds
        self._schedule_refresh(expires_in_seconds)

    def _schedule_refresh(self, expires_in_seconds: int) -> None:
        self._cancel_refresh()
        threshold = expires_in_seconds * (self._refresh_threshold_pct / 100)
        delay = expires_in_seconds - threshold

        async def _refresh():
            await asyncio.sleep(delay)
            try:
                await self.ensure_valid()
                logger.debug("JWT refreshed")
            except Exception as e:
                logger.warning("Scheduled token refresh failed: %s", e)

        self._refresh_task = asyncio.ensure_future(_refresh())

    def _cancel_refresh(self) -> None:
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
        self._refresh_task = None
