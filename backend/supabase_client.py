"""
عميل Supabase للاستخدام داخل الـ backend.

Supabase هو مصدر البيانات (students, halaqat, quran_recitation, ...).
نقرأ منه ونعكس البيانات في إنجازي. نستخدم مفتاح service_role للقراءة والكتابة.

الاستخدام:
    from backend.supabase_client import get_supabase
    sb = get_supabase()
    rows = sb.table("students").select("*").limit(10).execute().data
"""
from __future__ import annotations

from functools import lru_cache

import config.settings as cfg

try:
    from supabase import create_client, Client
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "مكتبة supabase غير مثبتة. ثبّتها: pip install supabase>=2.0.0"
    ) from exc


@lru_cache(maxsize=1)
def get_supabase() -> "Client":
    """يُرجع عميل Supabase (singleton) بمفتاح service_role."""
    if not cfg.SUPABASE_URL or not cfg.SUPABASE_SERVICE_ROLE_KEY:
        raise EnvironmentError(
            "بيانات Supabase مفقودة. أضف إلى .env:\n"
            "  SUPABASE_URL=https://your-host\n"
            "  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key"
        )
    return create_client(cfg.SUPABASE_URL, cfg.SUPABASE_SERVICE_ROLE_KEY)
