from __future__ import annotations
from typing import Any


class EnjaziError(Exception):
    """Base exception for all Enjazi client errors."""

    def __init__(self, message: str, status_code: int | None = None, response_body: Any = None, url: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.url = url

    def __str__(self):
        base = super().__str__()
        parts = [base]
        if self.status_code:
            parts.append(f"status={self.status_code}")
        if self.url:
            parts.append(f"url={self.url}")
        return " | ".join(parts)


class AuthenticationError(EnjaziError):
    """401 — invalid credentials or expired token."""


class AuthorizationError(EnjaziError):
    """403 — authenticated but not permitted."""


class RateLimitError(EnjaziError):
    """429 — too many requests."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60, **kwargs):
        kwargs.pop("status_code", None)
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class CloudflareError(EnjaziError):
    """Cloudflare challenge or block (403/503 with CF signature)."""


class CaptchaRequiredError(EnjaziError):
    """422 — server requires reCAPTCHA token."""


class ValidationError(EnjaziError):
    """422 — request failed validation; holds field-level errors."""

    def __init__(self, message: str, errors: dict | None = None, **kwargs):
        kwargs.pop("status_code", None)
        super().__init__(message, status_code=422, **kwargs)
        self.errors = errors or {}


class ResourceNotFoundError(EnjaziError):
    """404 — resource does not exist."""


class ServerError(EnjaziError):
    """5xx — server-side error."""


class NetworkError(EnjaziError):
    """Connection timeout, DNS failure, or other transport error."""


def raise_for_response(status_code: int, body: Any, url: str) -> None:
    """Map HTTP status codes to typed exceptions."""
    kwargs = dict(status_code=status_code, response_body=body, url=url)

    if status_code == 401:
        raise AuthenticationError("Authentication failed — check credentials or token.", **kwargs)

    if status_code == 403:
        # Distinguish Cloudflare blocks from Laravel 403
        body_str = str(body).lower()
        if "cloudflare" in body_str or "cf-ray" in body_str:
            raise CloudflareError("Cloudflare blocked the request.", **kwargs)
        raise AuthorizationError("Access forbidden.", **kwargs)

    if status_code == 404:
        raise ResourceNotFoundError("Resource not found.", **kwargs)

    if status_code == 422:
        # Check if it's a reCAPTCHA error
        errors = body.get("errors", {}) if isinstance(body, dict) else {}
        if "g-recaptcha-response" in errors or "recaptcha" in errors:
            raise CaptchaRequiredError("Server requires reCAPTCHA token.", **kwargs)
        msg = body.get("message", "Validation failed.") if isinstance(body, dict) else "Validation failed."
        raise ValidationError(msg, errors=errors, **kwargs)

    if status_code == 429:
        raise RateLimitError(url=url)

    if status_code == 503:
        body_str = str(body).lower()
        if "cloudflare" in body_str:
            raise CloudflareError("Cloudflare service unavailable / under-attack mode.", **kwargs)
        raise ServerError("Service unavailable.", **kwargs)

    if status_code >= 500:
        raise ServerError(f"Server error {status_code}.", **kwargs)
