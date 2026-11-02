"""
tests/test_sdk.py
Unit tests for Adtext Python SDK using pytest-asyncio + aioresponses.
"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from aioresponses import aioresponses

from adtext_sdk import AdtextSDK
from adtext_sdk.exceptions import AdtextNotInitializedError, AdtextHttpError

TEST_API_KEY = "ak_test_y-nRG4PxqYzfTVPFmoII7C5kPQcwJ2BU"
TEST_BASE_URL = "https://localhost:8080"

JWT_RESPONSE = {"token": "test.jwt.token", "expiresIn": 900, "env": "test"}
SDK_CONFIG_RESPONSE = {
    "env": "test",
    "heartbeatInterval": 60,
    "prefetchEnabled": True,
    "maxPrefetchAds": 3,
    "adRequestTimeoutMs": 2000,
    "logLevel": "DEBUG",
    "enableDebugMode": True,
    "consentRequired": False,
    "frequencyCapEnabled": True,
    "tokenRefreshThresholdPct": 20,
}
AD_RESPONSE = {
    "adId": "ad_381293",
    "campaignId": "e3082df5-1cbb-4b7e-94fd-f0d3213fdddc",
    "advertiserId": "596e53f1-784d-4132-9e6a-d846993021a0",
    "type": "native",
    "creative": {
        "headline": "Walt Disney World Spring Break 2026",
        "description": "Experience the magic of theme parks",
        "imageUrl": "https://cdn.ads.example.com/disney_1.jpg",
        "buttonLabel": "Apply Now",
        "disclaimerText": "Terms apply.",
    },
    "clickUrl": "https://ads.adtext.ai/click/ad_381293",
    "impressionUrl": "https://ads.adtext.ai/impression/ad_381293",
    "remainingFrequencyCap": 5,
}


async def make_sdk(m: aioresponses, bypass_consent=True) -> AdtextSDK:
    """Helper: create and initialize SDK with mocked responses."""
    m.get(f"{TEST_BASE_URL}/sdk/v1/auth/jwt", payload=JWT_RESPONSE)
    m.get(f"{TEST_BASE_URL}/sdk/v1/sdk/config", payload=SDK_CONFIG_RESPONSE)

    sdk = AdtextSDK()
    await sdk.init_sdk(
        api_key=TEST_API_KEY,
        env="test",
        user_id="user_849213",
        session_id="sess_28391",
        bypass_consent=bypass_consent,
    )
    return sdk


# ─── init_sdk ────────────────────────────────────────────────────────────────


class TestInitSdk:
    async def test_raises_without_api_key(self):
        sdk = AdtextSDK()
        with pytest.raises(ValueError, match="api_key is required"):
            await sdk.init_sdk(api_key="")

    async def test_raises_on_invalid_env(self):
        sdk = AdtextSDK()
        with pytest.raises(ValueError, match="Invalid env"):
            await sdk.init_sdk(api_key=TEST_API_KEY, env="staging")

    async def test_exchanges_api_key_for_jwt(self):
        with aioresponses() as m:
            m.get(f"{TEST_BASE_URL}/sdk/v1/auth/jwt", payload=JWT_RESPONSE)
            m.get(f"{TEST_BASE_URL}/sdk/v1/sdk/config", payload=SDK_CONFIG_RESPONSE)

            sdk = AdtextSDK()
            await sdk.init_sdk(api_key=TEST_API_KEY, env="test", bypass_consent=True)

            assert sdk._token_manager.get_token() == "test.jwt.token"

    async def test_idempotent_double_init(self):
        with aioresponses() as m:
            sdk = await make_sdk(m)
            call_count_before = len(m.requests)

            # Second call should be a no-op
            await sdk.init_sdk(api_key=TEST_API_KEY, env="test")
            assert len(m.requests) == call_count_before


# ─── get_ad ──────────────────────────────────────────────────────────────────


class TestGetAd:
    async def test_raises_before_init(self):
        sdk = AdtextSDK()
        with pytest.raises(AdtextNotInitializedError):
            await sdk.get_ad("homepage_sidebar")

    async def test_returns_ad_for_valid_placement(self):
        with aioresponses() as m:
            sdk = await make_sdk(m)
            m.post(f"{TEST_BASE_URL}/sdk/v1/ads/fetch", payload=AD_RESPONSE)

            ad = await sdk.get_ad("homepage_sidebar")

            assert ad is not None
            assert ad["adId"] == "ad_381293"
            assert ad["type"] == "native"
            assert ad["creative"]["headline"] == "Walt Disney World Spring Break 2026"

    async def test_returns_none_on_no_fill(self):
        with aioresponses() as m:
            sdk = await make_sdk(m)
            m.post(f"{TEST_BASE_URL}/sdk/v1/ads/fetch", status=204, payload=None)

            ad = await sdk.get_ad("homepage_sidebar")
            assert ad is None

    async def test_returns_none_on_451_consent_blocked(self):
        with aioresponses() as m:
            sdk = await make_sdk(m)
            m.post(
                f"{TEST_BASE_URL}/sdk/v1/ads/fetch",
                status=451,
                payload={"code": "CONSENT_REQUIRED", "message": "Consent required"},
            )

            ad = await sdk.get_ad("homepage_sidebar")
            assert ad is None

    async def test_passes_user_context(self):
        with aioresponses() as m:
            sdk = await make_sdk(m)
            m.post(f"{TEST_BASE_URL}/sdk/v1/ads/fetch", payload=AD_RESPONSE)

            await sdk.get_ad("homepage_sidebar")

            post_calls = m.requests.get(("POST", f"{TEST_BASE_URL}/sdk/v1/ads/fetch"))
            assert post_calls is not None
            body = post_calls[0].kwargs["json"]
            assert body["user"]["id"] == "user_849213"
            assert body["user"]["sessionId"] == "sess_28391"


# ─── track_impression / track_click ──────────────────────────────────────────


class TestTracking:
    async def test_track_impression_enqueues_without_http(self):
        with aioresponses() as m:
            sdk = await make_sdk(m)
            call_count = len(m.requests)

            sdk.track_impression("ad_381293", placement_id="homepage_sidebar")

            # No immediate HTTP call — buffered
            assert len(m.requests) == call_count
            assert sdk._event_queue.size == 1

    async def test_track_click_enqueues_without_http(self):
        with aioresponses() as m:
            sdk = await make_sdk(m)
            sdk.track_click("ad_381293")
            assert sdk._event_queue.size == 1

    async def test_raises_before_init(self):
        sdk = AdtextSDK()
        with pytest.raises(AdtextNotInitializedError):
            sdk.track_impression("ad_381293")

    async def test_track_conversion_fires_immediately(self):
        with aioresponses() as m:
            sdk = await make_sdk(m)
            m.post(
                f"{TEST_BASE_URL}/sdk/v1/measure/conversion",
                payload={
                    "conversionId": "conv_7f8a9b1c2d",
                    "campaignId": "e3082df5-1cbb-4b7e-94fd-f0d3213fdddc",
                    "attributed": True,
                    "attributionModel": "last_click",
                },
            )

            result = await sdk.track_conversion(
                ad_id="ad_381293",
                conversion_url="https://disney.com/thank-you",
                value=149.99,
            )

            assert result["attributed"] is True
            assert result["conversionId"].startswith("conv_")


# ─── consent ─────────────────────────────────────────────────────────────────


class TestConsent:
    async def test_consent_manager_accessible(self):
        with aioresponses() as m:
            sdk = await make_sdk(m)
            assert sdk.consent is not None
            assert hasattr(sdk.consent, "grant")
            assert hasattr(sdk.consent, "deny")
            assert hasattr(sdk.consent, "revoke")

    async def test_bypass_consent_allows_get_ad(self):
        with aioresponses() as m:
            # SDK config with consentRequired=True
            m.get(f"{TEST_BASE_URL}/sdk/v1/auth/jwt", payload=JWT_RESPONSE)
            m.get(
                f"{TEST_BASE_URL}/sdk/v1/sdk/config",
                payload={**SDK_CONFIG_RESPONSE, "consentRequired": True},
            )

            sdk = AdtextSDK()
            await sdk.init_sdk(api_key=TEST_API_KEY, env="test", bypass_consent=True)

            m.post(f"{TEST_BASE_URL}/sdk/v1/ads/fetch", payload=AD_RESPONSE)
            ad = await sdk.get_ad("homepage_sidebar")
            assert ad is not None


if __name__ == "__main__":
    print("Running Python SDK Tests")
    x = TestInitSdk()
    x.test_exchanges_api_key_for_jwt()
