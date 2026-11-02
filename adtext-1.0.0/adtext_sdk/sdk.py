import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from .http import HttpClient
from .token_manager import TokenManager
from .event_queue import EventQueue
from .consent import ConsentManager
from .context_session import ContextSession, create_context_session
from .exceptions import AdtextNotInitializedError, AdtextHttpError
from .privacy import StandardPlugin, EnhancedPrivacyPlugin
from .types import (
    AdContext,
    AdFetchRequest,
    AdResponse,
    AgeBracket,
    ConsentFramework,
    ConversionRequest,
    MeasurementEvent,
    PrivacyTier,
    SdkConfigResponse,
    TurnRole,
    UserContext,
    UserProfile,
)

logger = logging.getLogger("adtext_sdk")
SDK_VERSION = "1.0.0"
ENVIRONMENTS = {
    "production": "https://api.adtext.org",
    "test": "http://localhost:8080",
}


class AdtextSDK:
    def __init__(self):
        self._config: Dict = {}
        self._http: Optional[HttpClient] = None
        self._token_manager: Optional[TokenManager] = None
        self._event_queue: Optional[EventQueue] = None
        self._consent_manager: Optional[ConsentManager] = None
        self._sdk_config: Optional[Dict] = None
        self._initialized = False
        self._prefetch_cache: Dict[str, List[Dict]] = {}
        self._privacy_plugin = None
        self._error_handlers: List[Callable] = []

    async def init_sdk(
        self,
        api_key: str,
        env: str = "production",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        timeout_ms: int = 2000,
        bypass_consent: bool = False,
        on_error: Optional[Callable[[Dict], None]] = None,
        privacy_plugin=None,
    ) -> "AdtextSDK":
        if self._initialized:
            logger.warning("init_sdk() called more than once — ignoring")
            return self
        if not api_key:
            raise ValueError("api_key is required")
        if env not in ENVIRONMENTS:
            raise ValueError(f"Invalid env: {env!r}. Use 'production' or 'test'")
        if on_error:
            self._error_handlers.append(on_error)
        self._config = {
            "api_key": api_key,
            "env": env,
            "user_id": user_id,
            "session_id": session_id,
        }
        if env == "test":
            logging.basicConfig(level=logging.DEBUG)
        self._http = HttpClient(
            base_url=ENVIRONMENTS[env],
            timeout_ms=timeout_ms,
            get_token=lambda: self._token_manager.get_token() if self._token_manager else None,
        )
        self._token_manager = TokenManager(api_key=api_key, env=env, http=self._http)
        await self._token_manager.initialize()
        raw_config = await self._http.get(
            "/sdk/v1/sdk/config",
            {"env": env, "sdkVersion": f"python-{SDK_VERSION}", "platform": "python"},
        )
        self._sdk_config = SdkConfigResponse.from_dict(raw_config) if raw_config else None
        self._check_version_compat()
        self._consent_manager = ConsentManager(http=self._http)
        if bypass_consent:
            self._consent_manager.bypass()
        self._privacy_plugin = privacy_plugin or EnhancedPrivacyPlugin()
        if hasattr(self._privacy_plugin, "init"):
            await self._privacy_plugin.init()
        self._event_queue = EventQueue(http=self._http, sdk_version=f"python-{SDK_VERSION}")
        self._event_queue.start()
        self._initialized = True
        logger.info("Adtext SDK v%s initialized [%s]", SDK_VERSION, env)
        return self

    async def create_context_session(
        self,
        privacy_tier: str = "limited",
        session_id: Optional[str] = None,
        user_profile: Optional[Dict] = None,
    ) -> ContextSession:
        self._assert_initialized("create_context_session")
        return await create_context_session(
            self._http,
            privacy_tier=privacy_tier,
            session_id=session_id,
            user_profile=user_profile,
        )

    async def push_turn(
        self,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        privacy_tier: Optional[str] = None,
    ) -> int:
        self._assert_initialized("push_turn")
        if not session_id:
            raise ValueError("session_id is required for push_turn()")
        dummy_session = ContextSession(session_id, 1800, self._http)
        return await dummy_session.push_turn(role, content, privacy_tier)

    async def get_ad(
        self,
        placement_id: str,
        context: Optional[Dict] = None,
        context_session_id: Optional[str] = None,
        container_width: Optional[int] = None,
        container_height: Optional[int] = None,
    ) -> Optional[Dict]:
        try:
            return await self._get_ad_internal(
                placement_id, context, context_session_id, container_width, container_height
            )
        except Exception as e:
            logger.error("get_ad() failed (non-fatal): %s", e)
            self._emit_error("get_ad", e)
            return None

    async def _get_ad_internal(
        self,
        placement_id: str,
        context: Optional[Dict],
        context_session_id: Optional[str],
        container_width: Optional[int],
        container_height: Optional[int],
    ) -> Optional[Dict]:
        self._assert_initialized("get_ad")
        if self._sdk_config and self._sdk_config.consent_required:
            status = await self._consent_manager.wait_for_consent()
            if status == "denied":
                return None
        cached = self._pop_prefetch(placement_id)
        if cached:
            return cached
        try:
            inline_context: Optional[AdContext] = None
            if not context_session_id:
                raw = context or await self._build_privacy_context()
                inline_context = (
                    AdContext(
                        url=raw.get("url"),
                        text=raw.get("text"),
                        keywords=raw.get("keywords"),
                        iab_category=raw.get("iabCategory"),
                    )
                    if raw
                    else None
                )
            req = AdFetchRequest(
                placement_id=placement_id,
                context_session_id=context_session_id,
                context=inline_context,
                user=UserContext(
                    id=self._config.get("user_id"),
                    session_id=self._config.get("session_id"),
                ),
                container_width=container_width,
                container_height=container_height,
            )
            data = await self._http.post("/sdk/v1/ads/fetch", req.to_dict())
            if not data:
                return None
            ad = AdResponse.from_dict(data)
            if self._sdk_config and self._sdk_config.prefetch_enabled:
                asyncio.ensure_future(self._prefetch(placement_id, context))
            return ad
        except AdtextHttpError as e:
            if e.status == 451:
                logger.warning("get_ad blocked: consent required (451)")
                return None
            raise

    def track_impression(
        self,
        ad_id: str,
        placement_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ) -> None:
        try:
            self._assert_initialized("track_impression")
            self._event_queue.enqueue(
                MeasurementEvent(
                    event_type="impression",
                    ad_id=ad_id,
                    campaign_id=campaign_id,
                    placement_id=placement_id,
                    session_id=self._config.get("session_id"),
                )
            )
        except Exception as e:
            logger.error("track_impression() error: %s", e)

    def track_click(
        self,
        ad_id: str,
        placement_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ) -> None:
        try:
            self._assert_initialized("track_click")
            self._event_queue.enqueue(
                MeasurementEvent(
                    event_type="click",
                    ad_id=ad_id,
                    campaign_id=campaign_id,
                    placement_id=placement_id,
                    session_id=self._config.get("session_id"),
                )
            )
        except Exception as e:
            logger.error("track_click() error: %s", e)

    async def track_conversion(
        self,
        ad_id: str,
        conversion_url: str,
        conversion_pixel_id: Optional[str] = None,
        value: Optional[float] = None,
        campaign_id: Optional[str] = None,
    ) -> Optional[Dict]:
        try:
            self._assert_initialized("track_conversion")
            req = ConversionRequest(
                ad_id=ad_id,
                conversion_url=conversion_url,
                campaign_id=campaign_id,
                conversion_pixel_id=conversion_pixel_id,
                value=value,
                user_id=self._config.get("user_id"),
                session_id=self._config.get("session_id"),
                timestamp=int(time.time() * 1000),
            )
            return await self._http.post("/sdk/v1/measure/conversion", req.to_dict())
        except Exception as e:
            logger.error("track_conversion() error: %s", e)
            self._emit_error("track_conversion", e)
            return None

    def on_error(self, handler: Callable[[Dict], None]) -> "AdtextSDK":
        self._error_handlers.append(handler)
        return self

    @property
    def consent(self) -> ConsentManager:
        self._assert_initialized("consent")
        return self._consent_manager

    async def destroy(self) -> None:
        if not self._initialized:
            return
        try:
            if self._event_queue:
                await self._event_queue.stop()
            if self._token_manager:
                await self._token_manager.revoke()
            if self._http:
                await self._http.close()
        except Exception as e:
            logger.debug("Non-fatal error during destroy: %s", e)
        finally:
            self._initialized = False
            logger.info("Adtext SDK destroyed")

    def _check_version_compat(self) -> None:
        min_version = self._sdk_config.min_sdk_version if self._sdk_config else None
        if not min_version:
            return

        def to_int(v: str) -> int:
            parts = v.split(".")
            return sum(int(p) * (1000 ** (2 - i)) for i, p in enumerate(parts))

        if to_int(SDK_VERSION) < to_int(min_version):
            msg = f"SDK v{SDK_VERSION} below minimum v{min_version}. Run: pip install --upgrade adtext-sdk"
            logger.warning(msg)
            self._emit_error("init_sdk", RuntimeError(msg))

    async def _build_privacy_context(
        self,
        text: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Dict:
        try:
            return await self._privacy_plugin.build_context(text=text, url=url)
        except Exception as e:
            logger.warning("Privacy plugin failed, falling back to ENHANCED: %s", e)
            fallback = EnhancedPrivacyPlugin()
            return await fallback.build_context(text=text, url=url)

    async def _prefetch(self, placement_id: str, context: Optional[Dict]) -> None:
        max_ads = self._sdk_config.max_prefetch_ads if self._sdk_config else 3
        try:
            data = await self._http.post(
                "/sdk/v1/ads/prefetch",
                {
                    "placementId": placement_id,
                    "count": max_ads,
                    "context": context,
                    "user": {
                        "id": self._config.get("user_id"),
                        "sessionId": self._config.get("session_id"),
                    },
                },
            )
            if data and data.get("ads"):
                self._prefetch_cache[placement_id] = data["ads"]
        except Exception as e:
            logger.debug("Prefetch failed for %s: %s", placement_id, e)

    def _pop_prefetch(self, placement_id: str) -> Optional[Dict]:
        ads = self._prefetch_cache.get(placement_id)
        if not ads:
            return None
        ad = ads.pop(0)
        if not ads:
            del self._prefetch_cache[placement_id]
        return ad

    def _assert_initialized(self, method: str) -> None:
        if not self._initialized:
            raise AdtextNotInitializedError(f"{method}() called before init_sdk().")

    def _emit_error(self, method: str, error: Exception) -> None:
        for handler in self._error_handlers:
            try:
                handler({"method": method, "error": error})
            except Exception:
                pass


def create_sdk() -> AdtextSDK:
    return AdtextSDK()
