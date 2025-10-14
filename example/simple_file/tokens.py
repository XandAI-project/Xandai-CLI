import hashlib
import secrets
import time
from typing import Optional, Tuple

# In-memory storage for demo purposes - in production you'd use a database
_api_keys = {}


def generate_api_key() -> str:
    """
    Generate a secure API key using secrets.token_urlsafe()

    Returns:
        str: A securely generated API key
    """
    return secrets.token_urlsafe(32)


def create_api_key(user_id: str, expiry_days: int = 30) -> str:
    """
    Create a new API key for a user

    Args:
        user_id (str): The ID of the user requesting the key
        expiry_days (int): Number of days until the key expires (default: 30)

    Returns:
        str: The generated API key
    """
    api_key = generate_api_key()

    # Store key with metadata
    _api_keys[api_key] = {
        "user_id": user_id,
        "created_at": time.time(),
        "expires_at": time.time() + (expiry_days * 24 * 60 * 60) if expiry_days > 0 else None,
    }

    return api_key


def validate_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an API key

    Args:
        api_key (str): The API key to validate

    Returns:
        tuple: (is_valid: bool, user_id: str or None)
    """
    if not api_key or api_key not in _api_keys:
        return False, None

    key_data = _api_keys[api_key]

    # Check expiration
    if key_data["expires_at"] and time.time() > key_data["expires_at"]:
        # Key has expired - remove it
        del _api_keys[api_key]
        return False, None

    return True, key_data["user_id"]


def revoke_api_key(api_key: str) -> bool:
    """
    Revoke an API key (remove it from storage)

    Args:
        api_key (str): The API key to revoke

    Returns:
        bool: True if key was revoked, False if not found
    """
    if api_key in _api_keys:
        del _api_keys[api_key]
        return True
    return False


def get_user_keys(user_id: str) -> list:
    """
    Get all active API keys for a user

    Args:
        user_id (str): The user ID to look up

    Returns:
        list: List of API keys belonging to the user
    """
    return [key for key, data in _api_keys.items() if data["user_id"] == user_id]


def is_key_expired(api_key: str) -> bool:
    """
    Check if an API key has expired

    Args:
        api_key (str): The API key to check

    Returns:
        bool: True if the key has expired, False otherwise
    """
    if api_key not in _api_keys:
        return True

    key_data = _api_keys[api_key]
    if key_data["expires_at"] is None:
        return False

    return time.time() > key_data["expires_at"]


# Example usage (uncomment to test):
if __name__ == "__main__":
    # Create a new API key for user "user123"
    key = create_api_key("user123", expiry_days=7)
    print(f"Generated API Key: {key}")

    # Validate the key
    is_valid, user_id = validate_api_key(key)
    print(f"Key valid: {is_valid}, User ID: {user_id}")

    # Try to validate an invalid key
    is_valid, user_id = validate_api_key("invalid-key")
    print(f"Invalid key valid: {is_valid}")
