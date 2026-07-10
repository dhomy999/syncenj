"""
Halaqat API — يقرأ الحلقات من Supabase (المصدر) مع اسم المعلّم وحالة الربط بإنجازي.

GET   /api/halaqat            — قائمة الحلقات + teacher_name + linked
PATCH /api/halaqat/{id}/link  — ربط حلقة بمعرّف إنجازي (halaqat.enjazi_id)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.supabase_client import get_supabase

router = APIRouter()

# كاش بسيط في الذاكرة لحلقات إنجازي (تجنّبًا لمحدّد المعدل عند كل فتح)
_episodes_cache: list[dict] = []


class LinkBody(BaseModel):
    enjazi_id: int | None  # None لإلغاء الربط


@router.get("")
def list_halaqat():
    sb = get_supabase()
    halaqat = sb.table("halaqat").select("*").order("halqa_code").execute().data

    # خريطة رقم الموظف → اسم المعلّم
    emp_nos = sorted({h["teacher_emp_no"] for h in halaqat if h.get("teacher_emp_no")})
    teachers: dict = {}
    if emp_nos:
        rows = (
            sb.table("employees")
            .select("emp_number, name")
            .in_("emp_number", emp_nos)
            .execute()
            .data
        )
        teachers = {r["emp_number"]: r["name"] for r in rows}

    for h in halaqat:
        h["teacher_name"] = teachers.get(h.get("teacher_emp_no"))
        h["linked"] = h.get("enjazi_id") is not None

    return {"data": halaqat, "total": len(halaqat)}


@router.get("/enjazi-episodes")
def enjazi_episodes(refresh: bool = Query(False, description="إعادة الجلب من إنجازي")):
    """قائمة حلقات إنجازي (id, name, teacher_name) للاختيار عند الربط — مع كاش."""
    global _episodes_cache
    if _episodes_cache and not refresh:
        return {"data": _episodes_cache, "total": len(_episodes_cache), "cached": True}

    from enjazi.client import EnjaziClient
    from enjazi.auth import get_valid_token
    from enjazi.api.episodes import EpisodesAPI

    with EnjaziClient() as client:
        get_valid_token(client)
        eps = EpisodesAPI(client).list_all()

    _episodes_cache = [
        {"id": e.get("id"), "name": e.get("name"), "teacher_name": e.get("teacher_name")}
        for e in eps
    ]
    _episodes_cache.sort(key=lambda x: x["name"] or "")
    return {"data": _episodes_cache, "total": len(_episodes_cache), "cached": False}


@router.patch("/{halqa_id}/link")
def link_halqa(halqa_id: str, body: LinkBody):
    sb = get_supabase()
    res = (
        sb.table("halaqat")
        .update({"enjazi_id": body.enjazi_id})
        .eq("id", halqa_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(404, f"halqa '{halqa_id}' غير موجودة")
    return {"ok": True, "halqa": res.data[0]}
