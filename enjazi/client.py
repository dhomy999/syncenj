from __future__ import annotations

from typing import Any

import config.settings as cfg
from enjazi.exceptions import raise_for_response, NetworkError
from enjazi.utils.logger import logger
from enjazi.utils.rate_limiter import RateLimiter

try:
    from curl_cffi import requests as cf_requests
    _USE_CURL_CFFI = True
except ImportError:
    import requests as cf_requests  # type: ignore
    _USE_CURL_CFFI = False
    logger.warning("curl_cffi not available — using requests (no Chrome TLS fingerprint)")


class EnjaziClient:
    """
    Core HTTP client for api.injaazy.com

    - Impersonates Chrome 146 TLS fingerprint via curl_cffi (bypasses Cloudflare bot detection)
    - Sends all required browser headers on every request
    - Attaches context headers (x-behalf-id, x-behalf-on, etc.) for API scope
    - Rate-limits all requests automatically
    """

    def __init__(self, include_context_headers: bool = True):
        self._rate_limiter = RateLimiter(base_delay=cfg.REQUEST_DELAY)
        self._token: str | None = None
        self._include_context = include_context_headers
        self._session = self._build_session()

    def _build_session(self):
        if _USE_CURL_CFFI:
            session = cf_requests.Session(impersonate="chrome124")
        else:
            session = cf_requests.Session()
        session.headers.update(cfg.BASE_HEADERS)
        return session

    # ------------------------------------------------------------------
    # Token / Auth
    # ------------------------------------------------------------------

    def set_token(self, token: str) -> None:
        self._token = token
        self._session.headers["authorization"] = f"Bearer {token}"
        logger.debug("Bearer token applied to session.")

    def clear_token(self) -> None:
        self._token = None
        self._session.headers.pop("authorization", None)

    @property
    def is_authenticated(self) -> bool:
        return self._token is not None

    # ------------------------------------------------------------------
    # Context headers (x-behalf-*, x-current-role, x-institution-id)
    # ------------------------------------------------------------------

    def _context_headers(self, override: dict | None = None) -> dict:
        """Return context headers, optionally overriding defaults from settings."""
        if not self._include_context:
            return override or {}
        headers = {k: v for k, v in cfg.CONTEXT_HEADERS.items() if v}
        if override:
            headers.update(override)
        return headers

    # ------------------------------------------------------------------
    # Request dispatch
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        url: str,
        *,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        multipart: Any = None,
        params: dict | None = None,
        extra_headers: dict | None = None,
        context: bool = True,
    ) -> Any:
        self._rate_limiter.wait()

        headers = self._context_headers(extra_headers) if context else (extra_headers or {})

        logger.debug(f">> {method.upper()} {url}")

        # curl_cffi يستخدم multipart= (CurlMime) للنماذج متعددة الأجزاء بدل files=
        extra = {"multipart": multipart} if multipart is not None else {}
        try:
            response = self._session.request(
                method=method.upper(),
                url=url,
                json=json,
                data=data,
                files=files,
                params=params,
                headers=headers,
                timeout=cfg.REQUEST_TIMEOUT,
                **extra,
            )
        except Exception as exc:
            raise NetworkError(f"Network error: {exc}", url=url) from exc

        logger.debug(f"<< {response.status_code} {url}")

        try:
            body = response.json()
        except Exception:
            body = response.text

        if not response.ok:
            raise_for_response(response.status_code, body, url)

        return body

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def get(self, url: str, params: dict | None = None, **kw) -> Any:
        return self.request("GET", url, params=params, **kw)

    def post(self, url: str, json: Any = None, data: Any = None, files: Any = None,
             multipart: Any = None, **kw) -> Any:
        return self.request("POST", url, json=json, data=data, files=files, multipart=multipart, **kw)

    def put(self, url: str, json: Any = None, **kw) -> Any:
        return self.request("PUT", url, json=json, **kw)

    def patch(self, url: str, json: Any = None, **kw) -> Any:
        return self.request("PATCH", url, json=json, **kw)

    def delete(self, url: str, **kw) -> Any:
        return self.request("DELETE", url, **kw)

    def close(self) -> None:
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
