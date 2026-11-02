import asyncio
import threading
from typing import Any, Callable, Dict, Optional
from .sdk import AdtextSDK
from .consent import ConsentManager


class _SyncConsentManager:
    def __init__(self, async_cm: ConsentManager, loop: asyncio.AbstractEventLoop):
        self._cm = async_cm
        self._loop = loop

    def grant(self, user_id: str, framework: str = "gdpr", purposes=None, consent_string: Optional[str] = None):
        future = asyncio.run_coroutine_threadsafe(
            self._cm.grant(user_id, framework, purposes, consent_string), self._loop
        )
        return future.result(timeout=10)

    def deny(self, user_id: str, framework: str = "gdpr"):
        future = asyncio.run_coroutine_threadsafe(self._cm.deny(user_id, framework), self._loop)
        return future.result(timeout=10)

    def revoke(self, user_id: Optional[str] = None):
        future = asyncio.run_coroutine_threadsafe(self._cm.revoke(user_id), self._loop)
        return future.result(timeout=10)

    def bypass(self):
        self._cm.bypass()
        return self

    @property
    def status(self) -> str:
        return self._cm.status


class AdtextSDKSync:
    def __init__(self):
        self._sdk = AdtextSDK()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._consent_facade: Optional[_SyncConsentManager] = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or not self._loop.is_running():
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._loop.run_forever,
                daemon=True,
                name="adtext-sdk-loop",
            )
            self._thread.start()
        return self._loop

    def _run(self, coro) -> Any:
        future = asyncio.run_coroutine_threadsafe(coro, self._get_loop())
        return future.result(timeout=30)

    def init_sdk(
        self,
        api_key: str,
        env: str = "production",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        timeout_ms: int = 2000,
        bypass_consent: bool = False,
        on_error: Optional[Callable[[Dict], None]] = None,
    ) -> "AdtextSDKSync":
        self._run(
            self._sdk.init_sdk(
                api_key=api_key,
                env=env,
                user_id=user_id,
                session_id=session_id,
                timeout_ms=timeout_ms,
                bypass_consent=bypass_consent,
                on_error=on_error,
            )
        )
        self._consent_facade = _SyncConsentManager(self._sdk.consent, self._get_loop())
        return self

    def get_ad(
        self,
        placement_id: str,
        context: Optional[Dict] = None,
        container_width: Optional[int] = None,
        container_height: Optional[int] = None,
    ) -> Optional[Dict]:
        return self._run(self._sdk.get_ad(placement_id, context, container_width, container_height))

    def track_impression(
        self, ad_id: str, placement_id: Optional[str] = None, campaign_id: Optional[str] = None
    ) -> None:
        self._sdk.track_impression(ad_id, placement_id, campaign_id)

    def track_click(self, ad_id: str, placement_id: Optional[str] = None, campaign_id: Optional[str] = None) -> None:
        self._sdk.track_click(ad_id, placement_id, campaign_id)

    def track_conversion(
        self,
        ad_id: str,
        conversion_url: str,
        conversion_pixel_id: Optional[str] = None,
        value: Optional[float] = None,
        campaign_id: Optional[str] = None,
    ) -> Optional[Dict]:
        return self._run(self._sdk.track_conversion(ad_id, conversion_url, conversion_pixel_id, value, campaign_id))

    @property
    def consent(self) -> _SyncConsentManager:
        if self._consent_facade is None:
            raise RuntimeError("Call init_sdk() first")
        return self._consent_facade

    def on_error(self, handler: Callable[[Dict], None]) -> "AdtextSDKSync":
        self._sdk.on_error(handler)
        return self

    def destroy(self) -> None:
        self._run(self._sdk.destroy())
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=5)
        self._loop = None
        self._thread = None
