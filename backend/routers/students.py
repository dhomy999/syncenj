"""
Students API — يقرأ الطلاب من Supabase (المصدر) مع حالة الربط بإنجازي وحلقاته.

GET /api/students        — قائمة الطلاب + linked + halaqat (+ فلترة اختيارية)

ملاحظة: يستخدم select("*") ليعمل قبل/بعد إضافة عمود enjazi_id (DDL).
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.supabase_client import get_supabase

router = APIRouter()

# الحقول المعروضة في الواجهة
_FIELDS = (
    "id", "student_number", "student_name", "student_national_id",
    "department", "category", "status", "enjazi_id",
)

_PAGE = 1000  # حدّ PostgREST الافتراضي للصفّ الواحد


def _halaqat_by_student(sb, student_ids: list[str]) -> dict[str, list[str]]:
    """خريطة معرّف الطالب → أسماء حلقاته (من جدول enrollments)."""
    out: dict[str, list[str]] = {}
    for i in range(0, len(student_ids), 100):
        chunk = student_ids[i : i + 100]
        offset = 0
        while True:
            rows = (
                sb.table("enrollments")
                .select("student_id,halaqat(halqa_code)")
                .in_("student_id", chunk)
                .range(offset, offset + _PAGE - 1)
                .execute()
                .data
            )
            for r in rows:
                sid = r.get("student_id")
                code = (r.get("halaqat") or {}).get("halqa_code")
                if not sid or not code:
                    continue
                codes = out.setdefault(sid, [])
                if code not in codes:
                    codes.append(code)
            if len(rows) < _PAGE:
                break
            offset += _PAGE
    return out


@router.get("")
def list_students(
    linked: bool | None = Query(None, description="فلترة: مرتبط بإنجازي أم لا"),
    search: str | None = Query(None, description="بحث بالاسم أو رقم الهوية"),
    limit: int = Query(2000, le=5000),
):
    sb = get_supabase()
    q = sb.table("students").select("*")

    if search:
        q = q.or_(f"student_name.ilike.%{search}%,student_national_id.ilike.%{search}%")

    rows = q.order("student_number").limit(limit).execute().data

    out = []
    for s in rows:
        linked_val = s.get("enjazi_id") is not None
        if linked is not None and linked_val != linked:
            continue
        item = {k: s.get(k) for k in _FIELDS}
        item["linked"] = linked_val
        out.append(item)

    halaqat = _halaqat_by_student(sb, [s["id"] for s in out if s.get("id")])
    for item in out:
        item["halaqat"] = sorted(halaqat.get(item["id"], []))

    return {"data": out, "total": len(out)}
