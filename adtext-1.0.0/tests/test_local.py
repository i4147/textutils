import asyncio
import logging
from adtext_sdk import AdtextSDK

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG)


async def test_local_sdk():
    # Note: Use a real test API key if you have one, or a placeholder if the server is in dev mode
    # For now, using a common test key format.
    TEST_API_KEY = "ak_test_01234567890123456789012345678901"

    sdk = AdtextSDK()
    print("\n--- Initializing SDK against Localhost ---")
    try:
        await sdk.init_sdk(
            api_key=TEST_API_KEY,
            env="local",
            user_id="local_test_user",
            session_id="local_test_sess",
            bypass_consent=True,
        )
        print("✅ SDK Initialized Successfully")

        print("\n--- Fetching Ad ---")
        ad = await sdk.get_ad("homepage_sidebar")
        if ad:
            print(f"✅ Ad Received: {ad.get('adId')}")
            print(f"   Headline: {ad.get('creative', {}).get('headline')}")

            print("\n--- Tracking Impression ---")
            sdk.track_impression(ad["adId"])
            print("✅ Impression queued")

            # Small sleep to allow background tasks to process if needed (though track is buffered)
            await asyncio.sleep(1)
        else:
            print("❌ No ad received (204 No Content or error)")

    except Exception as e:
        print(f"❌ SDK Test Failed: {type(e).__name__}: {e}")
    finally:
        await sdk.destroy()
        print("\n--- SDK Destroyed ---")


if __name__ == "__main__":
    asyncio.run(test_local_sdk())
