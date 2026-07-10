import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env", override=False)

# --- Core ---
BASE_URL: str = os.getenv("ENJAZI_BASE_URL", "https://api.injaazy.com/front_app_api/v1").rstrip("/")

# --- Credentials ---
USERNAME: str = os.getenv("ENJAZI_USERNAME", "")
PASSWORD: str = os.getenv("ENJAZI_PASSWORD", "")
COUNTRY_ID: int = int(os.getenv("ENJAZI_COUNTRY_ID", "1"))

# --- IDs (fixed for this account) ---
CORPORATION_ID: str = os.getenv("ENJAZI_CORPORATION_ID", "118")   # جمعية الوحيين
CENTER_ID: str = os.getenv("ENJAZI_CENTER_ID", "171")             # الفرع الرجالي
INSTITUTION_ID: str = os.getenv("ENJAZI_INSTITUTION_ID", "1740")  # المنشأة الافتراضية

# --- Token ---
TOKEN_CACHE_PATH: Path = Path(os.getenv("TOKEN_CACHE_PATH", ".token_cache.json"))
TOKEN_TTL_HOURS: int = int(os.getenv("TOKEN_TTL_HOURS", "720"))

# --- Teacher mobile-app API (apps/v1) ---
# نظام مستقل عن لوحة المنشأة: رابط أساسي مختلف، تسجيل دخول مختلف، وترويسة x-episode-id.
# يُستخدم لفتح الحلقات من جهة المعلم (العملية 2). حساب معلم إشرافي واحد يرى كل حلقات المنشأة.
TEACHER_APP_BASE_URL: str = os.getenv("ENJAZI_TEACHER_APP_BASE_URL", "https://api.injaazy.com/apps/v1").rstrip("/")
TEACHER_USERNAME: str = os.getenv("ENJAZI_TEACHER_USERNAME", "")
TEACHER_PASSWORD: str = os.getenv("ENJAZI_TEACHER_PASSWORD", "")
TEACHER_TOKEN_CACHE_PATH: Path = Path(os.getenv("TEACHER_TOKEN_CACHE_PATH", ".teacher_token_cache.json"))

# --- HTTP ---
REQUEST_TIMEOUT: int = 30
REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "5.0"))

USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/146.0.0.0 Safari/537.36"
)

BASE_HEADERS: dict = {
    "accept": "*/*",
    "accept-language": "ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7",
    "origin": "https://dashboard.injaazy.com",
    "referer": "https://dashboard.injaazy.com/",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": USER_AGENT,
    "x-requested-with": "XMLHttpRequest",
}


CONTEXT_HEADERS: dict = {
    "x-behalf-id":      os.getenv("ENJAZI_BEHALF_ID", ""),
    "x-behalf-on":      os.getenv("ENJAZI_BEHALF_ON", "institution"),
    "x-current-role":   os.getenv("ENJAZI_CURRENT_ROLE", "7"),
    "x-institution-id": os.getenv("ENJAZI_INSTITUTION_ID", ""),
}


def corporation_headers() -> dict:
    """Headers for /corporation_panel/* endpoints."""
    return {"x-corporation-id": CORPORATION_ID, "x-current-role": "3"}


def center_headers(center_id: str | None = None) -> dict:
    """Headers for /center_panel/* endpoints."""
    return {
        "x-behalf-id": center_id or CENTER_ID,
        "x-behalf-on": "center",
        "x-center-id": CORPORATION_ID,
        "x-current-role": "3",
    }


def institution_headers(institution_id: str | None = None) -> dict:
    """Headers for /institution_panel/* endpoints (institution-level scope)."""
    iid = institution_id or INSTITUTION_ID
    return {
        "x-behalf-id": iid,
        "x-behalf-on": "institution",
        "x-institution-id": iid,
        "x-current-role": os.getenv("ENJAZI_CURRENT_ROLE", "7"),
    }


# --- Supabase (مصدر البيانات) ---
# Supabase هو المصدر: نقرأ منه (students, halaqat, quran_recitation) ونعكسه في إنجازي.
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def api_url(path: str) -> str:
    path = path if path.startswith("/") else f"/{path}"
    return f"{BASE_URL}{path}"


def validate() -> None:
    missing = [k for k, v in {"USERNAME": USERNAME, "PASSWORD": PASSWORD}.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")
