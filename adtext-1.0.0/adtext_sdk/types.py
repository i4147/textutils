import dataclasses
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def _serialize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Message):
        return value.to_dict()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            _snake_to_camel(f.name): _serialize(getattr(value, f.name))
            for f in dataclasses.fields(value)
            if getattr(value, f.name) is not None
        }
    if isinstance(value, list):
        return [_serialize(v) for v in value if v is not None]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items() if v is not None}
    return value


@dataclass
class Message:
    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for f in dataclasses.fields(self):
            value = getattr(self, f.name)
            serialized = _serialize(value)
            if serialized is not None:
                result[_snake_to_camel(f.name)] = serialized
        return result


class PrivacyTier(str, Enum):
    FULL = "full"
    LIMITED = "limited"
    NONE = "none"


class TurnRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConsentFramework(str, Enum):
    GDPR = "gdpr"
    CCPA = "ccpa"
    NONE = "none"


class AgeBracket(str, Enum):
    UNDER_18 = "13-17"
    AGE_18_24 = "18-24"
    AGE_25_34 = "25-34"
    AGE_35_44 = "35-44"
    AGE_45_54 = "45-54"
    AGE_55_64 = "55-64"
    AGE_65_PLUS = "65+"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class DeviceType(str, Enum):
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"
    CONNECTED_TV = "ctv"


class OperatingSystem(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class Intent(str, Enum):
    INFORMATIONAL = "informational"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class UserProfile(Message):
    user_id: Optional[str] = None
    age_group: Optional[AgeBracket] = None
    gender: Optional[Gender] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    interests: Optional[List[str]] = None
    custom_attributes: Optional[Dict[str, str]] = None
    subscription_tier: Optional[SubscriptionTier] = None
    device_type: Optional[DeviceType] = None
    os: Optional[OperatingSystem] = None


@dataclass
class UserContext(Message):
    id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class AdContext(Message):
    url: Optional[str] = None
    text: Optional[str] = None
    keywords: Optional[List[str]] = None
    iab_category: Optional[str] = None


@dataclass
class ContextSessionRequest(Message):
    session_id: Optional[str] = None
    privacy_tier: Optional[PrivacyTier] = None
    user_profile: Optional[UserProfile] = None


@dataclass
class TurnAppendRequest(Message):
    role: TurnRole
    content: str
    privacy_tier: Optional[PrivacyTier] = None


@dataclass
class AdFetchRequest(Message):
    placement_id: str
    context_session_id: Optional[str] = None
    context: Optional[AdContext] = None
    privacy_tier: Optional[PrivacyTier] = None
    user: Optional[UserContext] = None
    container_width: Optional[int] = None
    container_height: Optional[int] = None


@dataclass
class MeasurementEvent(Message):
    event_type: str
    ad_id: str
    campaign_id: Optional[str] = None
    placement_id: Optional[str] = None
    session_id: Optional[str] = None
    page_url: Optional[str] = None
    audience_token: Optional[str] = None
    id: Optional[str] = None
    timestamp: Optional[int] = None


@dataclass
class BatchRequest(Message):
    events: List[MeasurementEvent]
    sdk_version: str


@dataclass
class ConversionRequest(Message):
    ad_id: str
    conversion_url: str
    campaign_id: Optional[str] = None
    conversion_pixel_id: Optional[str] = None
    value: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[int] = None


@dataclass
class ConsentRequest(Message):
    user_id: str
    framework: ConsentFramework
    status: str
    purposes: Optional[List[int]] = None
    consent_string: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class JwtResponse:
    token: str
    expires_in: int
    env: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JwtResponse":
        return cls(
            token=data["token"],
            expires_in=data["expiresIn"],
            env=data.get("env", "production"),
        )


@dataclass
class SdkConfigResponse:
    min_sdk_version: Optional[str]
    max_prefetch_ads: int
    prefetch_enabled: bool
    consent_required: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SdkConfigResponse":
        return cls(
            min_sdk_version=data.get("minSdkVersion"),
            max_prefetch_ads=data.get("maxPrefetchAds", 3),
            prefetch_enabled=data.get("prefetchEnabled", False),
            consent_required=data.get("consentRequired", False),
        )


@dataclass
class ContextSessionResponse:
    session_id: str
    ttl_seconds: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextSessionResponse":
        return cls(
            session_id=data["sessionId"],
            ttl_seconds=data.get("ttlSeconds", 1800),
        )


@dataclass
class TurnAppendResponse:
    session_id: str
    turn_index: int
    ttl_seconds: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TurnAppendResponse":
        return cls(
            session_id=data.get("sessionId", ""),
            turn_index=data.get("turnIndex", 0),
            ttl_seconds=data.get("ttlSeconds", 1800),
        )


@dataclass
class AdResponse:
    ad_id: str
    placement_id: str
    campaign_id: Optional[str] = None
    creative_id: Optional[str] = None
    headline: Optional[str] = None
    description: Optional[str] = None
    adtext: Optional[str] = None
    click_url: Optional[str] = None
    impression_pixel_url: Optional[str] = None
    format: Optional[str] = None
    media_type: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdResponse":
        return cls(
            ad_id=data["adId"],
            placement_id=data.get("placementId", ""),
            campaign_id=data.get("campaignId"),
            creative_id=data.get("creativeId"),
            headline=data.get("headline"),
            description=data.get("description"),
            adtext=data.get("adtext"),
            click_url=data.get("clickUrl"),
            impression_pixel_url=data.get("impressionPixelUrl"),
            format=data.get("format"),
            media_type=data.get("mediaType"),
        )
