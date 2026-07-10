"""
Students API — يقرأ الطلاب من Supabase (المصدر) مع حالة الربط بإنجازي.

GET /api/students        — قائمة الطلاب + linked (+ فلترة اختيارية)

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

    return {"data": out, "total": len(out)}
