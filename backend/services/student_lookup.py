"""
Student lookup service.

سابقاً كان يعتمد على Google Sheets. الآن عبارة عن stub بانتظار الترحيل إلى Supabase.

TODO(Supabase): تنفيذ resolve_sub_url() و list_all_students() على جداول Supabase
التي ستحتوي على:
  - ربط الطلاب (sub_url -> enjazi_student_id, episode_id, institution_id)
  - بيانات الطلاب الشخصية (name, id_number, nationality, gender, phone, ...)

الواجهة مطابقة لما كان في sheets_lookup حتى لا تتأثر الـ routers.
"""
from __future__ import annotations

from dataclasses import dataclass

from enjazi.utils.logger import logger


@dataclass
class StudentLookup:
    """نتيجة تحليل sub_url إلى بيانات طالب."""
    sub_url: str
    enjazi_student_id: int       # رقم النظام → student_id في Enjazi API
    sheet_student_id: str        # رقم الطالب في النظام (مفتاح بحث سابق)
    episode_id: int              # الحلقة
    institution_id: int          # المنشأة (behalf_id)
    # بيانات شخصية
    name: str = ""
    id_number: str = ""
    nationality: str = ""
    gender: str = ""
    phone: str = ""
    institution_name: str = ""
    teacher_name: str = ""


def resolve_sub_url(sub_url: str) -> StudentLookup | None:
    """
    تحليل sub_url إلى بيانات طالب.

    TODO(Supabase): التنفيذ ضد Supabase. يُرجع None حتى ذلك الحين.
    """
    logger.warning(
        f"student_lookup.resolve_sub_url('{sub_url}'): غير مُنفّذ بعد "
        f"(بانتظار الترحيل إلى Supabase). سيُرجع None."
    )
    return None


def list_all_students() -> list[dict]:
    """
    إرجاع كل الطلاب الذين لديهم sub_url مدموجين بأسمائهم.

    TODO(Supabase): التنفيذ ضد Supabase. يُرجع [] حتى ذلك الحين.
    """
    logger.warning(
        "student_lookup.list_all_students(): غير مُنفّذ بعد "
        "(بانتظار الترحيل إلى Supabase). سيُرجع []."
    )
    return []
