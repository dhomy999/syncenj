from __future__ import annotations
from typing import TYPE_CHECKING, Any

import config.settings as cfg

if TYPE_CHECKING:
    from enjazi.client import EnjaziClient


class BaseAPI:
    """
    Base class for all API resource modules.

    Each subclass targets one panel (corporation / center / institution)
    and uses the correct headers automatically.
    """

    def __init__(self, client: "EnjaziClient"):
        self.client = client

    def _get(self, path: str, params: dict | None = None, headers: dict | None = None) -> Any:
        return self.client.get(cfg.api_url(path), params=params, extra_headers=headers, context=False)

    def _post(self, path: str, json: Any = None, data: Any = None,
              files: Any = None, multipart: Any = None, headers: dict | None = None) -> Any:
        return self.client.post(cfg.api_url(path), json=json, data=data,
                                files=files, multipart=multipart,
                                extra_headers=headers, context=False)

    def _put(self, path: str, json: Any = None, headers: dict | None = None) -> Any:
        return self.client.put(cfg.api_url(path), json=json, extra_headers=headers, context=False)

    @staticmethod
    def _extract_list(response: Any, key: str = "data") -> list:
        """Safely extract a list from a response dict."""
        if isinstance(response, dict):
            val = response.get(key, [])
            return val if isinstance(val, list) else []
        return []
