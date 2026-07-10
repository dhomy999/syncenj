"""
مهمة: تسجيل طلاب Supabase في إنجازي جماعيًا (Phase 4).

الاتجاه: Supabase هو المصدر. نسجّل الطلاب غير المربوطين (enjazi_id IS NULL) الذين لديهم
تسجيل نشط في حلقة **مربوطة** بإنجازي (halaqat.enjazi_id IS NOT NULL).

يستخدم نقطة التسجيل الجماعي التي تستخدمها لوحة إنجازي (مكتشفة من HAR add.md):
    POST /institution_panel/settings/batch-operations/register-students
مع program_id=523 و level_id=1744 (مؤكَّدان من HAR للمنشأة 539).

بعد التسجيل تُكتب معرّفات إنجازي عبر إعادة تشغيل مهمة sync_students (مطابقة برقم الهوية).

المعاملات (params):
    limit        — حدّ أقصى لعدد الطلاب (للدفعات التجريبية). None = الكل.
    batch_size   — عدد الطلاب في طلب تسجيل واحد (افتراضي 10).
    program_id   — رقم البرنامج (افتراضي 523).
    level_id     — رقم المستوى (افتراضي 1744).
    sync_program — تفعيل البرنامج للمنشأة قبل البدء (افتراضي True).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
from enjazi.utils.logger import logger
from backend.supabase_client import get_supabase

import config.settings as cfg

_ACTIVE = "نشط"
PROGRAM_ID = 523   # حفظ حسب خطة التسميع (مؤكَّد للمنشأة 539)
LEVEL_ID = 1744    # التزام حال الحضور (مؤكَّد من HAR)


def _collect_eligible(sb) -> list[dict]:
    """يجمع الطلاب المؤهّلين للتسجيل، بلا تكرار برقم الهوية."""
    rows = (
        sb.table("enrollments")
        .select(
            "status,"
            "students(student_national_id,student_name,enjazi_id),"
            "halaqat(halqa_code,enjazi_id)"
        )
        .eq("status", _ACTIVE)
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
        if stu.get("enjazi_id") is not None:      # مربوط أصلًا
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


def _to_payload(e: dict, program_id: int, level_id: int) -> dict:
    """يبني عنصر student في body التسجيل الجماعي (كما ترسله اللوحة)."""
    return {
        "id": 0,
        "name": e["name"],
        "user_is_changed": True,
        "username": e["username"],
        "episode_id": e["episode_id"],
        "program_id": program_id,
        "level_id": level_id,
        "original_username": e["username"],
    }


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def run(params: dict, log_id: int, db: Session) -> dict:
    sb = get_supabase()
    limit = params.get("limit")
    batch_size = int(params.get("batch_size", 10))
    program_id = int(params.get("program_id", PROGRAM_ID))
    level_id = int(params.get("level_id", LEVEL_ID))
    sync_program = params.get("sync_program", True)
    institution_id = cfg.INSTITUTION_ID

    eligible = _collect_eligible(sb)
    total_eligible = len(eligible)
    logger.info(f"register_students: {total_eligible} طالب مؤهّل للتسجيل")

    if limit:
        eligible = eligible[: int(limit)]
        logger.info(f"register_students: دفعة محدودة بـ {len(eligible)} (limit={limit})")

    results: list[dict] = []
    with EnjaziClient() as client:
        get_valid_token(client)
        api = StudentsAPI(client)

        if sync_program and eligible:
            try:
                api.sync_program_selection(program_id, institution_id)
                logger.info(f"register_students: فُعِّل البرنامج {program_id} للمنشأة")
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
                results.append({
                    "username": e["username"], "name": e["name"],
                    "halqa_code": e["halqa_code"], "episode_id": e["episode_id"],
                    "status": status, "error": err,
                })

    result = {
        "total_eligible": total_eligible,
        "attempted": len(results),
        "success": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "results": results,
    }
    logger.info(f"register_students: {result['success']} نجح، {result['failed']} فشل (من {result['attempted']})")
    return result
