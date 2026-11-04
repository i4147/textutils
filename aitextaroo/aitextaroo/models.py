from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    CONNECTED = "connected"
    MESSAGE = "message"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class InboundMessage:
    id: str
    text: str
    received_at: str
    channel: str = "sms"
    trust_level: str = "low"
    has_pin: bool = False


@dataclass(frozen=True, slots=True)
class ConnectedEvent:
    user_id: str
    assigned_number: str
    server_time: str


@dataclass(frozen=True, slots=True)
class ErrorEvent:
    code: str
    message: str
    retry_after: int | None = None


@dataclass(frozen=True, slots=True)
class StreamEvent:
    type: EventType
    connected: ConnectedEvent | None = None
    message: InboundMessage | None = None
    error: ErrorEvent | None = None
