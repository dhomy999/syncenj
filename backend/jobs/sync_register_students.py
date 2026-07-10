"""
مهمة: مزامنة أحادية Supabase → إنجازي (تسجيل الطلاب الجدد).

الاتجاه: Supabase هو المصدر. تُجدوَل يومياً الساعة 1 صباحاً (توقيت الرياض) فتلتقط
الطلاب المسجّلين في **اليوم السابق فقط** (تسجيل نشط في حلقة مربوطة)، تسجّلهم في إنجازي،
ثم تكتب enjazi_id فوراً في Supabaze (مطابقة بالرقم الوطني).

تُوحّد خطوتي «التسجيل» و«الكتابة» في دورة واحدة (idempotent وآمنة للتكرار).

المعاملات (params):
    days_back     — نافذة الأيام للخلف (افتراضي 1 = أمس فقط).
    batch_size    — عدد الطلاب في طلب تسجيل واحد (افتراضي 10).
    program_id    — رقم البرنامج (افتراضي 523 = حفظ حسب خطة التسميع).
    level_id      — رقم المستوى (افتراضي 1744 = الالتزام حال الحضور).
    sync_program  — تفعيل البرنامج للمنشأة قبل البدء (افتراضي True).
    date_field    — حقل تاريخ الفلترة: "enrollment" (افتراضي) أو "student".
    timezone      — المنطقة الزمنية لحساب النافذة (افتراضي Asia/Riyadh).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
from enjazi.utils.logger import logger
from backend.supabase_client import get_supabase
# إعادة استخدام مساعدات مهمة التسجيل الجماعي (DRY)
from backend.jobs.register_students import _to_payload, _chunks, _ACTIVE

import config.settings as cfg

PROGRAM_ID = 523   # حفظ حسب خطة التسميع
LEVEL_ID = 1744    # الالتزام حال الحضور


def _yesterday_window(tz_name: str, days_back: int = 1) -> tuple[str, str]:
    """نافذة ISO (start, end) بتوقيت المنطقة للطلاب المسجّلين في (اليوم - days_back)."""
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = today_start
    start = today_start - timedelta(days=days_back)
    return start.isoformat(), end.isoformat()


def _collect_eligible(sb, window_start: str, window_end: str, date_field: str) -> list[dict]:
    """
    يجمع الطلاب المؤهّلين للتسجيل ضمن النافذة الزمنية:
      - status == "نشط"
      - الطالب enjazi_id IS NULL (لم يُسجّل في إنجازي بعد)
      - الحلقة مربوطة (halaqat.enjazi_id IS NOT NULL)
      - التاريخ ضمن النافذة (enrollments.created_at افتراضياً)
    بلا تكرار برقم الهوية الوطنية.
    """
    base_select = (
        "created_at,status,"
        "students(id,student_national_id,student_name,enjazi_id,created_at),"
        "halaqat(halqa_code,enjazi_id)"
    )

    if date_field == "student":
        # فلترة على تاريخ إنشاء سجل الطالب: نأخذ معرّفات الطلاب ضمن النافذة أولاً
        sb_rows = (
            sb.table("students")
            .select("id")
            .gte("created_at", window_start)
            .lt("created_at", window_end)
            .execute()
            .data
        )
        student_ids = [r["id"] for r in sb_rows if r.get("id")]
        if not student_ids:
            return []
        rows = (
            sb.table("enrollments")
            .select(base_select)
            .eq("status", _ACTIVE)
            .in_("student_id", student_ids)
            .execute()
            .data
        )
    else:
        # افتراضي: فلترة على تاريخ التسجيل في الحلقة (enrollments.created_at)
        rows = (
            sb.table("enrollments")
            .select(base_select)
            .eq("status", _ACTIVE)
            .gte("created_at", window_start)
            .lt("created_at", window_end)
            .execute()
            .data
        )

    by_nid: dict[str, dict] = {}
    for r in rows:
        stu = r.get("students") or {}
        hal = r.get("halaqat") or {}
        nid = str(stu.get("student_national_id") or "").strip()
        episode_id = hal.get("enjazi_id")

        if not nid:
            continue
        if stu.get("enjazi_id") is not None:      # مربوط أصلًا في إنجازي
            continue
        if episode_id is None:                    # حلقته غير مربوطة
            continue
        if nid in by_nid:                         # سُجّل من حلقة أخرى
            continue

        by_nid[nid] = {
            "username": nid,
            "name": str(stu.get("student_name") or "").strip(),
            "episode_id": int(episode_id),
            "halqa_code": hal.get("halqa_code"),
        }
    return list(by_nid.values())


def _writeback_enjazi_ids(succeeded: list[dict], client) -> int:
    """يكتب enjazi_id في Supabase للمسجّلين بنجاح (مطابقة بالرقم الوطني)."""
    if not succeeded:
        return 0

    # خريطة الرقم الوطني → معرّف إنجازي (قراءة واحدة)
    enjazi_students = StudentsAPI(client).list_all(limit=5000)
    nid_to_id: dict[str, int] = {}
    for s in enjazi_students:
        u = str(s.get("username") or "").strip()
        if u:
            nid_to_id[u] = s.get("id")

    sb = get_supabase()
    updated = 0
    for e in succeeded:
        enjazi_id = nid_to_id.get(e["username"])
        if enjazi_id is None:
            logger.warning(f"writeback: لم يُعثر على معرّف إنجازي للطالب {e['username']}")
            continue
        try:
            sb.table("students").update({"enjazi_id": enjazi_id}).eq(
                "student_national_id", e["username"]
            ).execute()
            updated += 1
        except Exception as exc:
            logger.warning(f"writeback فشل للطالب {e['username']}: {exc}")
    return updated


async def run(params: dict, log_id: int, db: Session) -> dict:
    sb = get_supabase()
    tz_name = params.get("timezone", "Asia/Riyadh")
    days_back = int(params.get("days_back", 1))
    batch_size = int(params.get("batch_size", 10))
    program_id = int(params.get("program_id", PROGRAM_ID))
    level_id = int(params.get("level_id", LEVEL_ID))
    sync_program = params.get("sync_program", True)
    date_field = params.get("date_field", "enrollment")
    institution_id = cfg.INSTITUTION_ID

    window_start, window_end = _yesterday_window(tz_name, days_back)
    logger.info(
        f"sync_register_students: نافذة {window_start} ← {window_end} "
        f"(date_field={date_field}, tz={tz_name})"
    )

    eligible = _collect_eligible(sb, window_start, window_end, date_field)
    total_eligible = len(eligible)
    logger.info(f"sync_register_students: {total_eligible} طالب مؤهّل ضمن النافذة")

    if not eligible:
        result = {
            "window_start": window_start,
            "window_end": window_end,
            "date_field": date_field,
            "total_eligible": 0,
            "attempted": 0,
            "registered": 0,
            "failed": 0,
            "enjazi_ids_written": 0,
        }
        logger.info("sync_register_students: لا يوجد طلاب جدد ضمن النافذة")
        return result

    results: list[dict] = []
    succeeded: list[dict] = []  # المسجّلون بنجاح (لكتابة enjazi_id لاحقاً)

    with EnjaziClient() as client:
        get_valid_token(client)
        api = StudentsAPI(client)

        if sync_program:
            try:
                api.sync_program_selection(program_id, institution_id)
                logger.info(f"sync_register_students: فُعِّل البرنامج {program_id} للمنشأة")
            except Exception as exc:
                logger.warning(f"sync-programs-selections فشل (نتابع): {exc}")

        batches = list(_chunks(eligible, batch_size))
        for bi, chunk in enumerate(batches, 1):
            usernames = [e["username"] for e in chunk]
            logger.info(f"[دفعة {bi}/{len(batches)}] تسجيل {len(chunk)} طالب: {usernames}")

            # فحص أرقام الهوية (best-effort — لا يوقف التسجيل)
            try:
                api.batch_check_usernames(usernames, institution_id)
            except Exception as exc:
                logger.warning(f"check-usernames فشل (نتابع): {exc}")

            payload = [_to_payload(e, program_id, level_id) for e in chunk]
            try:
                resp = api.batch_register(payload, institution_id)
                ok = isinstance(resp, dict) and resp.get("success", True)
                status = "success" if ok else "failed"
                err = None if ok else str(resp)
            except Exception as exc:
                status, err = "failed", str(exc)
                logger.error(f"batch_register فشل: {err}")

            for e in chunk:
                row = {
                    "username": e["username"], "name": e["name"],
                    "halqa_code": e["halqa_code"], "episode_id": e["episode_id"],
                    "status": status, "error": err,
                }
                results.append(row)
                if status == "success":
                    succeeded.append(e)

        # كتابة enjazi_id للمسجّلين بنجاح فوراً (idempotent)
        written = _writeback_enjazi_ids(succeeded, client)

    registered = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    result = {
        "window_start": window_start,
        "window_end": window_end,
        "date_field": date_field,
        "total_eligible": total_eligible,
        "attempted": len(results),
        "registered": registered,
        "failed": failed,
        "enjazi_ids_written": written,
        "results": results,
    }
    logger.info(
        f"sync_register_students: {registered} سُجّل، {failed} فشل، "
        f"{written} كُتب enjazi_id (من {len(results)})"
    )
    return result
