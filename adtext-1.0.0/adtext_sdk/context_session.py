import logging
import uuid
from typing import Optional
from .http import HttpClient
from .types import (
    ContextSessionRequest,
    ContextSessionResponse,
    PrivacyTier,
    TurnAppendRequest,
    TurnAppendResponse,
    TurnRole,
    UserProfile,
)

logger = logging.getLogger("adtext_sdk")


class ContextSession:
    def __init__(self, session_id: str, ttl_seconds: int, http: HttpClient):
        self._session_id = session_id
        self._ttl_seconds = ttl_seconds
        self._http = http
        self._turn_index = 0
        self._closed = False

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def ttl_seconds(self) -> int:
        return self._ttl_seconds

    async def push_turn(
        self,
        role: TurnRole | str,
        content: str,
        privacy_tier: Optional[PrivacyTier] = None,
    ) -> int:
        if self._closed:
            raise RuntimeError("push_turn() called on a closed ContextSession")
        req = TurnAppendRequest(
            role=TurnRole(role) if isinstance(role, str) else role,
            content=content,
            privacy_tier=privacy_tier,
        )
        try:
            data = await self._http.post(
                f"/sdk/v1/context/{self._session_id}/turn",
                req.to_dict(),
            )
            if data:
                resp = TurnAppendResponse.from_dict(data)
                self._turn_index = resp.turn_index
                self._ttl_seconds = resp.ttl_seconds
            else:
                self._turn_index += 1
            return self._turn_index
        except Exception as e:
            logger.warning("push_turn failed (non-fatal): %s", e)
            self._turn_index += 1
            return self._turn_index

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self._http.delete(f"/sdk/v1/context/{self._session_id}")
        except Exception as e:
            logger.debug("Context session close error (non-fatal): %s", e)

    async def __aenter__(self) -> "ContextSession":
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()


async def create_context_session(
    http: HttpClient,
    privacy_tier: PrivacyTier = PrivacyTier.LIMITED,
    session_id: Optional[str] = None,
    user_profile: Optional[UserProfile] = None,
) -> ContextSession:
    sid = session_id or str(uuid.uuid4())
    req = ContextSessionRequest(
        session_id=sid,
        privacy_tier=privacy_tier,
        user_profile=user_profile,
    )
    try:
        data = await http.post("/sdk/v1/context/session", req.to_dict())
        resp = ContextSessionResponse.from_dict(data) if data else ContextSessionResponse(sid, 1800)
        return ContextSession(resp.session_id, resp.ttl_seconds, http)
    except Exception as e:
        logger.warning("Failed to create context session on server: %s — using local ID", e)
        return ContextSession(sid, 1800, http)
