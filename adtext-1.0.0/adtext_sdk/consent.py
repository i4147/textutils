import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional
from .http import HttpClient
from .types import ConsentFramework, ConsentRequest

logger = logging.getLogger("adtext_sdk")


class ConsentManager:
    def __init__(self, http: HttpClient):
        self._http = http
        self._user_id: Optional[str] = None
        self._status: str = "unknown"
        self._framework: ConsentFramework = ConsentFramework.NONE
        self._purposes: List[int] = []
        self._gate: asyncio.Future = asyncio.get_event_loop().create_future()

    async def grant(
        self,
        user_id: str,
        framework: ConsentFramework | str = ConsentFramework.GDPR,
        purposes: Optional[List[int]] = None,
        consent_string: Optional[str] = None,
    ) -> "ConsentManager":
        self._user_id = user_id
        self._status = "granted"
        self._framework = ConsentFramework(framework) if isinstance(framework, str) else framework
        self._purposes = purposes or [1, 2, 3, 4]
        req = ConsentRequest(
            user_id=user_id,
            framework=self._framework,
            status="granted",
            purposes=self._purposes,
            consent_string=consent_string,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await self._http.post("/sdk/v1/consent", req.to_dict())
        if not self._gate.done():
            self._gate.set_result("granted")
        return self

    async def deny(
        self,
        user_id: str,
        framework: ConsentFramework | str = ConsentFramework.GDPR,
    ) -> "ConsentManager":
        self._user_id = user_id
        self._status = "denied"
        self._framework = ConsentFramework(framework) if isinstance(framework, str) else framework
        req = ConsentRequest(
            user_id=user_id,
            framework=self._framework,
            status="denied",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await self._http.post("/sdk/v1/consent", req.to_dict())
        if not self._gate.done():
            self._gate.set_result("denied")
        return self

    async def revoke(self, user_id: Optional[str] = None) -> None:
        target = user_id or self._user_id
        if not target:
            raise ValueError("user_id required for consent revocation")
        await self._http.delete(f"/sdk/v1/consent/{target}")
        self._status = "denied"
        logger.info("Consent revoked for user: %s", target)

    async def wait_for_consent(self) -> str:
        return await self._gate

    def bypass(self) -> "ConsentManager":
        self._status = "granted"
        if not self._gate.done():
            self._gate.set_result("granted")
        return self

    def has_consent(self) -> bool:
        return self._status in ("granted", "partial")

    @property
    def status(self) -> str:
        return self._status
