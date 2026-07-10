from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import config.settings as cfg
from enjazi.exceptions import AuthenticationError
from enjazi.utils.logger import logger

if TYPE_CHECKING:
    from enjazi.client import EnjaziClient


# ------------------------------------------------------------------
# Token persistence
# ------------------------------------------------------------------

def save_token(token: str, user_id: int | None = None, user_name: str = "") -> None:
    data = {
        "token": token,
        "user_id": user_id,
        "user_name": user_name,
        "acquired_at": datetime.now().isoformat(),
    }
    cfg.TOKEN_CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Token saved >> {str(cfg.TOKEN_CACHE_PATH)}")


def load_token() -> dict | None:
    path: Path = cfg.TOKEN_CACHE_PATH
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"Cannot read token cache: {exc}")
        return None


def is_token_valid(data: dict) -> bool:
    """Sanctum PATs don't expire server-side, but we re-login after TOKEN_TTL_HOURS as safety."""
    try:
        acquired_at = datetime.fromisoformat(data["acquired_at"])
        return datetime.now() < acquired_at + timedelta(hours=cfg.TOKEN_TTL_HOURS)
    except Exception:
        return False


def delete_token() -> None:
    cfg.TOKEN_CACHE_PATH.unlink(missing_ok=True)
    logger.debug("Token cache deleted.")


# ------------------------------------------------------------------
# Login
# ------------------------------------------------------------------

def login(client: "EnjaziClient", username: str | None = None, password: str | None = None) -> str:
    """
    POST /login
    Body: { username, password, country_id }
    Response: { data: { token, user: { id, name, ... } } }
    """
    username = username or cfg.USERNAME
    password = password or cfg.PASSWORD

    if not username or not password:
        raise AuthenticationError("No credentials provided. Set ENJAZI_USERNAME and ENJAZI_PASSWORD in .env")

    url = cfg.api_url("/login")
    logger.info(f"Logging in as {username} >> {url}")

    response = client.post(url, json={
        "username": username,
        "password": password,
        "country_id": cfg.COUNTRY_ID,
    })

    # Extract token from Injazi response structure
    data = response.get("data", {}) if isinstance(response, dict) else {}
    token = data.get("access_token") or data.get("token")
    if not token:
        logger.error(f"Login response: {response}")
        raise AuthenticationError("Login succeeded but no token found in response.")

    # user info lives directly in data (not nested under a 'user' key)
    user_id = data.get("id")
    user_name = data.get("name", "")
    logger.success(f"Logged in as: {user_name} (ID: {user_id})")

    save_token(token, user_id=user_id, user_name=user_name)
    client.set_token(token)
    return token


# ------------------------------------------------------------------
# get_valid_token — the main entry point
# ------------------------------------------------------------------

def get_valid_token(client: "EnjaziClient") -> str:
    """
    Return a valid Bearer token, re-logging in only if cache is expired/missing.
    """
    cached = load_token()
    if cached and is_token_valid(cached):
        token = cached["token"]
        logger.info(f"Using cached token for: {cached.get('user_name', '?')}")
        client.set_token(token)
        return token

    logger.info("No valid cached token — logging in.")
    return login(client)
