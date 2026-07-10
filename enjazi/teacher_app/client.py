"""
TeacherAppClient — عميل HTTP لتطبيق المعلم (https://api.injaazy.com/apps/v1).

مستقل عن EnjaziClient (لوحة المنشأة): رابط أساسي مختلف، بلا ترويسات x-behalf-*،
تسجيل دخول يُرجع data.access_token، وترويسة x-episode-id تُمرَّر لكل نقاط الحلقة/الطالب.
يحافظ على انتحال بصمة Chrome لتجاوز Cloudflare، ويعيد استخدام محدّد المعدّل وأخطاء المشروع.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import config.settings as cfg
from enjazi.exceptions import AuthenticationError, raise_for_response, NetworkError
from enjazi.utils.logger import logger
from enjazi.utils.rate_limiter import RateLimiter

try:
    from curl_cffi import requests as cf_requests
    _USE_CURL_CFFI = True
except ImportError:
    import requests as cf_requests  # type: ignore
    _USE_CURL_CFFI = False
    logger.warning("curl_cffi not available — using requests (no Chrome TLS fingerprint)")


class TeacherAppClient:
    """عميل تطبيق المعلم مع إدارة توكن مؤقت خاص به."""

    def __init__(self):
        self._rate_limiter = RateLimiter(base_delay=cfg.REQUEST_DELAY)
        self._token: str | None = None
        self._session = self._build_session()

    def _build_session(self):
        if _USE_CURL_CFFI:
            session = cf_requests.Session(impersonate="chrome124")
        else:
            session = cf_requests.Session()
        session.headers.update({
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": cfg.USER_AGENT,
        })
        return session

    # ------------------------------------------------------------------
    # Token
    # ------------------------------------------------------------------

    def set_token(self, token: str) -> None:
        self._token = token
        self._session.headers["authorization"] = f"Bearer {token}"

    def _save_token(self, token: str) -> None:
        data = {"token": token, "acquired_at": datetime.now().isoformat()}
        cfg.TEACHER_TOKEN_CACHE_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(f"Teacher token saved >> {cfg.TEACHER_TOKEN_CACHE_PATH}")

    def _load_token(self) -> dict | None:
        path = cfg.TEACHER_TOKEN_CACHE_PATH
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning(f"Cannot read teacher token cache: {exc}")
            return None

    @staticmethod
    def _is_valid(data: dict) -> bool:
        try:
            acquired_at = datetime.fromisoformat(data["acquired_at"])
            return datetime.now() < acquired_at + timedelta(hours=cfg.TOKEN_TTL_HOURS)
        except Exception:
            return False

    def login(self, username: str | None = None, password: str | None = None) -> str:
        """POST apps/v1/auth/login {username, password, country_id} → data.access_token."""
        username = username or cfg.TEACHER_USERNAME
        password = password or cfg.TEACHER_PASSWORD
        if not username or not password:
            raise AuthenticationError(
                "No teacher credentials. Set ENJAZI_TEACHER_USERNAME and ENJAZI_TEACHER_PASSWORD in .env"
            )

        url = f"{cfg.TEACHER_APP_BASE_URL}/auth/login"
        logger.info(f"Teacher login as {username} >> {url}")
        resp = self._request_raw("POST", url, json={
            "username": username,
            "password": password,
            "country_id": cfg.COUNTRY_ID,
        })
        data = resp.get("data", {}) if isinstance(resp, dict) else {}
        token = data.get("access_token") or data.get("token")
        if not token:
            logger.error(f"Teacher login response: {resp}")
            raise AuthenticationError("Teacher login succeeded but no token found.")
        self._save_token(token)
        self.set_token(token)
        logger.success("Teacher logged in.")
        return token

    def get_valid_token(self) -> str:
        """توكن صالح: من الكاش إن لم ينتهِ، وإلا تسجيل دخول جديد."""
        cached = self._load_token()
        if cached and self._is_valid(cached):
            token = cached["token"]
            logger.info("Using cached teacher token.")
            self.set_token(token)
            return token
        logger.info("No valid cached teacher token — logging in.")
        return self.login()

    # ------------------------------------------------------------------
    # Request dispatch
    # ------------------------------------------------------------------

    def _request_raw(
        self, method: str, url: str, *,
        json: Any = None, params: dict | None = None,
        episode_id: int | str | None = None,
    ) -> Any:
        self._rate_limiter.wait()
        headers = {}
        if episode_id is not None:
            headers["x-episode-id"] = str(episode_id)

        try:
            response = self._session.request(
                method=method.upper(), url=url,
                json=json, params=params, headers=headers,
                timeout=cfg.REQUEST_TIMEOUT,
            )
        except Exception as exc:
            raise NetworkError(f"Network error: {exc}", url=url) from exc

        try:
            body = response.json()
        except Exception:
            body = response.text

        if not response.ok:
            raise_for_response(response.status_code, body, url)
        return body

    def get(self, path: str, params: dict | None = None, episode_id: int | str | None = None) -> Any:
        return self._request_raw("GET", self._url(path), params=params, episode_id=episode_id)

    def post(self, path: str, json: Any = None, episode_id: int | str | None = None) -> Any:
        return self._request_raw("POST", self._url(path), json=json, episode_id=episode_id)

    @staticmethod
    def _url(path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        return f"{cfg.TEACHER_APP_BASE_URL}{path}"

    def close(self) -> None:
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
