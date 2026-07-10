"""
مهمة: تعليم من له سجل تسميع اليوم في Supabase كـ «حاضر» في إنجازي (العملية 3).
تعمل كل ساعة من 5 صباحًا إلى 10 مساءً.

المنطق (المبسّط — بلا تفاصيل آيات/درجات):
    لكل صف quran_recitation بتاريخ اليوم، طالبه وحلقته مربوطان (enjazi_id)، و synced_at IS NULL:
        PUT /institution_panel/students/{enjazi_id}/change-recite
        body = {episode_id, student_id, attend_type: "attend100", date_of: اليوم, lessons: []}
    عند النجاح (200): synced_at = now()
    عند الفشل (مثلاً 422): تُكتب sync_error، ويُعاد المحاولة الساعة التالية (synced_at يبقى NULL).
    الإعادة محدودة تلقائيًا باليوم: غدًا يخرج الصف من فلتر recite_date == اليوم.

القيمة attend100 مؤكَّدة 200 من HAR (NEWTSME3.txt) بحمولة lessons فارغة.
هذا الملف مستقل عن sync_recitation.py (المزامنة الكاملة المؤجّلة).
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.recitation import RecitationAPI
from enjazi.utils.logger import logger
from backend.supabase_client import get_supabase

ATTEND_TYPE = "attend100"


def _today(tz_name: str) -> str:
    return datetime.now(ZoneInfo(tz_name)).date().isoformat()


def _collect_rows(sb, target_date: str) -> list[dict]:
    """صفوف تسميع اليوم لطلاب مربوطين (student+halqa لهما enjazi_id)، غير مُزامَنة."""
    rows = (
        sb.table("quran_recitation")
        .select(
            "id,recite_date,synced_at,"
            "students(enjazi_id,student_name),halaqat(enjazi_id,halqa_code)"
        )
        .eq("recite_date", target_date)
        .is_("synced_at", "null")
        .execute()
        .data
    )
    out: list[dict] = []
    for r in rows:
        stu = r.get("students") or {}
        hal = r.get("halaqat") or {}
        if stu.get("enjazi_id") and hal.get("enjazi_id"):
            out.append(r)
    return out


def _mark_synced(sb, row_id: str) -> None:
    sb.table("quran_recitation").update(
        {"synced_at": datetime.utcnow().isoformat()}
    ).eq("id", row_id).execute()


def _mark_error(sb, row_id: str, error: str) -> None:
    sb.table("quran_recitation").update({"sync_error": error[:1000]}).eq("id", row_id).execute()


async def run(params: dict, log_id: int, db: Session) -> dict:
    """
    params:
        date     — التاريخ المستهدف "YYYY-MM-DD" (افتراضي: اليوم بتوقيت الرياض).
        dry_run  — True (افتراضي): محاكاة بلا إرسال.
        limit    — عدد أقصى للصفوف (اختياري، للاختبار).
        timezone — لحساب «اليوم» (افتراضي Asia/Riyadh).
    """
    sb = get_supabase()
    tz_name = params.get("timezone", "Asia/Riyadh")
    target_date = params.get("date") or _today(tz_name)
    dry_run = bool(params.get("dry_run", True))
    limit = params.get("limit")

    rows = _collect_rows(sb, target_date)
    if limit:
        rows = rows[: int(limit)]

    logger.info(
        f"sync_attend100: التاريخ={target_date} | صفوف مؤهّلة={len(rows)} | dry_run={dry_run}"
    )

    result = {
        "date": target_date,
        "dry_run": dry_run,
        "eligible": len(rows),
        "attended": 0,
        "failed": 0,
        "details": [],
    }
    if not rows:
        return result

    with EnjaziClient() as client:
        get_valid_token(client)
        api = RecitationAPI(client)

        for row in rows:
            stu = row["students"]
            hal = row["halaqat"]
            sid = int(stu["enjazi_id"])
            eid = int(hal["enjazi_id"])
            name = stu.get("student_name") or str(sid)
            detail = {"student": name, "sid": sid, "eid": eid, "row_id": row["id"]}

            try:
                if dry_run:
                    detail["action"] = "dry_run"
                    detail["payload"] = {
                        "episode_id": eid, "student_id": sid,
                        "attend_type": ATTEND_TYPE, "date_of": target_date, "lessons": [],
                    }
                    logger.info(f"[DRY-RUN] [{name}] سيُعلَّم حاضرًا (attend100) — حلقة {eid}")
                else:
                    api.change_recite(sid, eid, target_date, lessons=[], attend_type=ATTEND_TYPE)
                    _mark_synced(sb, row["id"])
                    detail["action"] = "attended"
                    result["attended"] += 1
                    logger.info(f"[{name}] عُلِّم حاضرًا (attend100) ✅ — حلقة {eid}")
            except Exception as exc:
                detail["action"] = "failed"
                detail["error"] = f"{type(exc).__name__}: {exc}"
                result["failed"] += 1
                if not dry_run:
                    _mark_error(sb, row["id"], detail["error"])
                logger.error(f"[{name}] فشل attend100 — حلقة {eid}: {exc}")

            result["details"].append(detail)

    logger.info(f"sync_attend100: حاضر={result['attended']} فشل={result['failed']}")
    return result
