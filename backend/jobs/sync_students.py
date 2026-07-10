"""
مهمة: مزامنة/ربط الطلاب بين Supabase وإنجازي.

الاتجاه: Supabase هو المصدر. نجلب طلاب إنجازي ونطابقهم بطلاب Supabase عبر رقم الهوية
الوطنية، ثم نكتب معرّف إنجازي (students.enjazi_id) في Supabase ليُستخدم لاحقًا في مزامنة التسميع.

المطابقة: students.student_national_id (Supabase) == username (إنجازي).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
from enjazi.utils.logger import logger
from backend.supabase_client import get_supabase


def _norm_nid(value) -> str:
    """تطبيع رقم الهوية للمقارنة."""
    return str(value or "").strip()


async def run(params: dict, log_id: int, db: Session) -> dict:
    sb = get_supabase()

    # 1) طلاب Supabase (المصدر)
    sb_students = (
        sb.table("students")
        .select("id, student_national_id, enjazi_id")
        .execute()
        .data
    )
    logger.info(f"sync_students: {len(sb_students)} طالب في Supabase")

    # 2) طلاب إنجازي (لبناء خريطة رقم الهوية → enjazi_id)
    with EnjaziClient() as client:
        get_valid_token(client)
        enjazi_students = StudentsAPI(client).list_all(limit=params.get("limit", 5000))
    logger.info(f"sync_students: {len(enjazi_students)} طالب في إنجازي")

    by_nid: dict[str, int] = {}
    for s in enjazi_students:
        nid = _norm_nid(s.get("username"))
        if nid:
            by_nid[nid] = s.get("id")

    # 3) المطابقة والكتابة في Supabase
    matched = updated = unmatched = 0
    unmatched_samples: list[str] = []

    for r in sb_students:
        nid = _norm_nid(r.get("student_national_id"))
        enjazi_id = by_nid.get(nid)

        if enjazi_id is None:
            unmatched += 1
            if len(unmatched_samples) < 10:
                unmatched_samples.append(nid)
            continue

        matched += 1
        if r.get("enjazi_id") != enjazi_id:
            sb.table("students").update({"enjazi_id": enjazi_id}).eq("id", r["id"]).execute()
            updated += 1

    result = {
        "supabase_students": len(sb_students),
        "enjazi_students": len(enjazi_students),
        "matched": matched,
        "updated": updated,
        "unmatched": unmatched,
        "unmatched_samples": unmatched_samples,
    }
    logger.info(f"sync_students: {result}")
    return result
