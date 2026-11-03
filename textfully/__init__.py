from enum import Enum
from typing import Any, Dict, List, Optional
import requests
from .exceptions import APIError, AuthenticationError, TextfullyError
from .version import __version__

api_key: Optional[str] = None
_base_url = "https://api.textfully.dev/v1"
_default_timeout = 30
TEXTFULLY_ERROR_CODES = {
    "missing_required_field": 422,
    "invalid_access": 422,
    "invalid_parameter": 422,
    "invalid_region": 422,
    "rate_limit_exceeded": 429,
    "missing_api_key": 401,
    "invalid_api_key": 403,
    "invalid_from_address": 403,
    "validation_error": 403,
    "not_found": 404,
    "method_not_allowed": 405,
    "application_error": 500,
    "internal_server_error": 500,
}


class MessageService(str, Enum):
    SMS = "sms"
    IMESSAGE = "imessage"


class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


def _get_headers() -> dict[str, str]:
    if not api_key:
        msg = "No API key provided. Set your API key using textfully.api_key = 'tx_apikey'"
        raise AuthenticationError(msg)
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": f"textfully-python/{__version__}",
        "Accept": "application/json",
    }


def _handle_response(response: requests.Response) -> dict[str, Any]:
    try:
        response_data = response.json()
    except ValueError:
        msg = f"Invalid JSON response from API: {response.text}"
        raise APIError(msg)
    if not 200 <= response.status_code < 300:
        error_message = response_data.get("error", {}).get("message", "Unknown error")
        error_type = response_data.get("error", {}).get("type", "api_error")
        if response.status_code == 401:
            msg = f"Authentication failed: {error_message}"
            raise AuthenticationError(msg)
        elif response.status_code == 400:
            msg = f"Bad request: {error_message}"
            raise APIError(msg)
        else:
            msg = f"API request failed: {error_message} (Type: {error_type})"
            raise APIError(msg)
    return response_data


def send(to: str, text: str, service: Optional[MessageService] = None) -> dict[str, Any]:
    if not to:
        msg = "Invalid phone number format. Must be in E.164 format (e.g., +16175555555)"
        raise ValueError(msg)
    if not to.startswith("+") or to.count("+") > 1:
        msg = "Invalid phone number format. Must be in E.164 format (e.g., +16175555555)"
        raise ValueError(msg)
    digits = to[1:]
    if not digits.isdigit() or len(digits) < 10 or len(digits) > 15 or digits.startswith("0"):
        msg = "Invalid phone number format. Must be in E.164 format (e.g., +16175555555)"
        raise ValueError(msg)
    payload = {"to": to, "text": text}
    if service:
        payload["service"] = service.value
    try:
        response = requests.post(
            f"{_base_url}/messages",
            json=payload,
            headers=_get_headers(),
            timeout=_default_timeout,
        )
        return _handle_response(response)
    except requests.exceptions.Timeout:
        msg = "Request timed out. Please try again."
        raise APIError(msg)
    except requests.exceptions.RequestException as e:
        msg = f"Request failed: {e!s}"
        raise APIError(msg)
