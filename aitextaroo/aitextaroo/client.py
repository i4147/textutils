from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from aitextaroo.models import (
    ConnectedEvent,
    ErrorEvent,
    EventType,
    InboundMessage,
    StreamEvent,
)

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.aitextaroo.com"
DEFAULT_RECONNECT_DELAY = 3.0
MAX_RECONNECT_DELAY = 60.0
RECONNECT_BACKOFF_FACTOR = 2.0


class TextarooError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 0):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"{code}: {message}")


def _parse_json_response(response: httpx.Response, fallback_message: str) -> dict:
    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        raise TextarooError(
            code="http_error" if response.status_code != 200 else "invalid_response",
            message=f"{fallback_message} (HTTP {response.status_code})",
            status_code=response.status_code,
        ) from exc

    if response.status_code != 200:
        error = data.get("error") if isinstance(data, dict) else None
        if not isinstance(error, dict):
            error = {}
        raise TextarooError(
            code=error.get("code", "unknown"),
            message=error.get("message", fallback_message),
            status_code=response.status_code,
        )

    if not isinstance(data, dict):
        raise TextarooError(
            code="invalid_response",
            message=f"{fallback_message}: expected JSON object (HTTP {response.status_code})",
            status_code=response.status_code,
        )

    return data


class TextarooClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._client: httpx.AsyncClient | None = None
        self._last_event_id: str | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=self._headers,
                timeout=self._timeout,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @staticmethod
    async def request_verification(
        phone: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            response = await client.post(
                "/v1/auth/verify",
                json={"phone": phone},
            )
            return _parse_json_response(response, "Verification request failed")

    @staticmethod
    async def confirm_verification(
        phone: str,
        code: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            response = await client.post(
                "/v1/auth/confirm",
                json={"phone": phone, "code": code},
            )
            return _parse_json_response(response, "Verification failed")

    async def send(self, text: str) -> str:
        client = await self._get_client()
        response = await client.post("/v1/send", json={"text": text})
        data = _parse_json_response(response, "Send failed")
        message_id = data.get("message_id")
        if not isinstance(message_id, str) or not message_id:
            raise TextarooError(
                code="invalid_response",
                message="Missing or invalid message_id in send response",
                status_code=response.status_code,
            )
        return message_id

    async def account(self) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get("/v1/account")
        return _parse_json_response(response, "Account lookup failed")

    async def listen(self, *, auto_reconnect: bool = True) -> AsyncIterator[InboundMessage]:
        delay = DEFAULT_RECONNECT_DELAY

        while True:
            try:
                async for event in self._stream_events():
                    if event.type == EventType.CONNECTED:
                        logger.info("Stream connected: %s", event.connected)
                        delay = DEFAULT_RECONNECT_DELAY

                    elif event.type == EventType.MESSAGE and event.message:
                        yield event.message

                    elif event.type == EventType.ERROR and event.error:
                        logger.warning("Stream error: %s", event.error)
                        if event.error.retry_after:
                            delay = float(event.error.retry_after)

            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError) as exc:
                logger.warning("Stream disconnected: %s", type(exc).__name__)

            except httpx.HTTPStatusError as exc:
                logger.error("Stream HTTP error: %d", exc.response.status_code)
                if exc.response.status_code == 401:
                    raise TextarooError(
                        code="unauthorized",
                        message="Invalid API key",
                        status_code=401,
                    ) from exc

            if not auto_reconnect:
                return

            logger.info("Reconnecting in %.1fs (Last-Event-ID: %s)", delay, self._last_event_id)
            await _async_sleep(delay)
            delay = min(delay * RECONNECT_BACKOFF_FACTOR, MAX_RECONNECT_DELAY)

    async def _stream_events(self) -> AsyncIterator[StreamEvent]:
        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }
        if self._last_event_id:
            headers["Last-Event-ID"] = self._last_event_id

        client = await self._get_client()

        async with client.stream(
            "GET",
            "/v1/stream",
            headers=headers,
            timeout=None,
        ) as response:
            response.raise_for_status()

            event_type: str | None = None
            event_id: str | None = None
            data_lines: list[str] = []

            async for raw_line in response.aiter_lines():
                line = raw_line.rstrip("\n\r")

                if line.startswith(":"):
                    continue

                if not line:
                    if data_lines:
                        event = _parse_event(event_type, event_id, data_lines)
                        if event:
                            if event_id:
                                self._last_event_id = event_id
                            yield event

                    event_type = None
                    event_id = None
                    data_lines = []
                    continue

                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data_lines.append(line[5:].strip())
                elif line.startswith("id:"):
                    event_id = line[3:].strip()
                elif line.startswith("retry:"):
                    pass


def _parse_event(
    event_type: str | None,
    event_id: str | None,
    data_lines: list[str],
) -> StreamEvent | None:
    if not data_lines:
        return None

    raw_data = "\n".join(data_lines)

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        logger.warning("Failed to parse SSE data: %s", raw_data[:100])
        return None

    if event_type == "connected":
        return StreamEvent(
            type=EventType.CONNECTED,
            connected=ConnectedEvent(
                user_id=data.get("user_id", ""),
                assigned_number=data.get("assigned_number", ""),
                server_time=data.get("server_time", ""),
            ),
        )

    if event_type == "message":
        return StreamEvent(
            type=EventType.MESSAGE,
            message=InboundMessage(
                id=data.get("id", ""),
                text=data.get("text", ""),
                received_at=data.get("received_at", ""),
                channel=data.get("channel", "sms"),
                trust_level=data.get("trust_level", "low"),
                has_pin=data.get("has_pin", False),
            ),
        )

    if event_type == "error":
        return StreamEvent(
            type=EventType.ERROR,
            error=ErrorEvent(
                code=data.get("code", "unknown"),
                message=data.get("message", ""),
                retry_after=data.get("retry_after"),
            ),
        )

    logger.debug("Unknown event type: %s", event_type)
    return None


async def _async_sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)
