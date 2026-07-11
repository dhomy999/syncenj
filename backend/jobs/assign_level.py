"""
مهمة: إسناد مستوى موحّد للطلاب غير المُهيّئين (بلا خطة/سلسلة تسميع) في إنجازي.

المشكلة: كثير من الطلاب ليس لهم خطة تسميع في الحلقة، فتفشل قراءة/كتابة التسميع
    بخطأ خادم إنجازي «Attempt to read property "chain_id" on null».

الحل (مؤكَّد من التقاط حقيقي — chenge_levl.md): طلب كتابة واحد يُنشئ الخطة تلقائياً:
    POST /institution_panel/students/{sid}/change-level
    body = {episode_id, student_id, level_id, curriculum_id}

السياسة:
    - قيمة المستوى موحّدة لكل الطلاب (level_id افتراضي 1745، curriculum_id=null).
    - only_missing=True (افتراضي): لا يُلمَس إلا الطالب الذي **لا خطة له**؛ من عنده خطة/مستوى
      حالي يُتخطّى (حتى لا نغيّر مستوى صحيحًا موجودًا).
    - dry_run=True افتراضياً: يطبع ما سيُرسَل بلا إرسال فعلي.

المعاملات (params):
    dry_run            — True (افتراضي) محاكاة؛ False إرسال فعلي.
    level_id           — المستوى الموحّد (افتراضي 1745).
    curriculum_id      — افتراضي None.
    only_missing       — True (افتراضي) لا يسند إلا لمن بلا خطة.
    limit              — أقصى عدد إسنادات فعلية (للاختبار: 1).
    institution_id     — فلتر المنشأة (اختياري).
    student_enjazi_id  — (مع episode_id) لاستهداف طالب واحد بعينه.
    episode_id         — رقم حلقة إنجازي للطالب المستهدف.
    scan_limit         — أقصى صفوف تُمسح من Supabase لاستخراج الأزواج (افتراضي 5000).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.recitation import RecitationAPI
from enjazi.api.students import StudentsAPI
from enjazi.utils.logger import logger
from backend.supabase_client import get_supabase

DEFAULT_LEVEL_ID = 1745

# علامات تدل على أن الطالب غير مُهيّأ في الحلقة (لا خطة/سلسلة) — خطأ خادم إنجازي.
_NOT_CONFIGURED_SIGNS = ("chain_id", "on null", "std_level_id")


def _is_not_configured(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(sign.lower() in msg for sign in _NOT_CONFIGURED_SIGNS)


def _collect_pairs(sb, scan_limit: int = 5000) -> list[tuple[int, int, str]]:
    """أزواج (student_enjazi_id, episode_enjazi_id, name) الفريدة لطلاب مربوطين من quran_recitation."""
    pairs: dict[tuple[int, int], str] = {}
    page = 1000
    offset = 0
    while offset < scan_limit:
        rows = (
            sb.table("quran_recitation")
            .select("students(enjazi_id,student_name),halaqat(enjazi_id,halqa_code)")
            .range(offset, offset + page - 1)
            .execute()
            .data
        )
        if not rows:
            break
        for r in rows:
            stu = r.get("students") or {}
            hal = r.get("halaqat") or {}
            sid, eid = stu.get("enjazi_id"), hal.get("enjazi_id")
            if sid and eid:
                key = (int(sid), int(eid))
                pairs.setdefault(key, stu.get("student_name") or str(sid))
        if len(rows) < page:
            break
        offset += page
    return [(sid, eid, name) for (sid, eid), name in pairs.items()]


def _has_plan(rec_api: RecitationAPI, sid: int, eid: int) -> bool | None:
    """
    هل للطالب خطة/مستوى حالي في الحلقة؟
        True  = عنده خطة (std_level_id موجود) ⇒ يُتخطّى.
        False = بلا خطة (فارغ أو خطأ chain_id) ⇒ يُسنَد.
        None  = خطأ آخر غير متوقّع ⇒ يُعامَل كفشل قراءة.
    """
    try:
        plan = rec_api.get_plan(sid, eid)
        std = ((plan.get("program") or {}).get("level") or {}).get("std_level_id")
        return bool(std)
    except Exception as exc:
        if _is_not_configured(exc):
            return False
        logger.warning(f"تعذّرت قراءة plan للطالب {sid}/حلقة {eid}: {exc}")
        return None


async def run(params: dict, log_id: int, db: Session) -> dict:
    dry_run = bool(params.get("dry_run", True))
    level_id = int(params.get("level_id", DEFAULT_LEVEL_ID))
    curriculum_id = params.get("curriculum_id")  # None افتراضياً
    only_missing = bool(params.get("only_missing", True))
    limit = params.get("limit")
    institution_id = params.get("institution_id")
    one_sid = params.get("student_enjazi_id")
    one_eid = params.get("episode_id")
    scan_limit = int(params.get("scan_limit", 5000))

    sb = get_supabase()

    if one_sid and one_eid:
        pairs = [(int(one_sid), int(one_eid), str(one_sid))]
    else:
        pairs = _collect_pairs(sb, scan_limit)

    logger.info(
        f"assign_level: أزواج مرشّحة={len(pairs)} | level_id={level_id} | "
        f"only_missing={only_missing} | dry_run={dry_run} | limit={limit}"
    )

    result = {
        "dry_run": dry_run,
        "level_id": level_id,
        "candidates": len(pairs),
        "assigned": 0,
        "skipped_has_plan": 0,
        "read_failed": 0,
        "failed": 0,
        "details": [],
    }
    if not pairs:
        return result

    with EnjaziClient() as client:
        get_valid_token(client)
        rec_api = RecitationAPI(client)
        stu_api = StudentsAPI(client)

        for sid, eid, name in pairs:
            if limit and result["assigned"] >= int(limit):
                break
            detail = {"student": name, "sid": sid, "eid": eid}

            if only_missing:
                has = _has_plan(rec_api, sid, eid)
                if has is True:
                    detail["action"] = "skipped_has_plan"
                    result["skipped_has_plan"] += 1
                    result["details"].append(detail)
                    continue
                if has is None:
                    detail["action"] = "read_failed"
                    result["read_failed"] += 1
                    result["details"].append(detail)
                    continue

            try:
                if dry_run:
                    detail["action"] = "dry_run"
                    detail["payload"] = {
                        "episode_id": str(eid), "student_id": str(sid),
                        "level_id": level_id, "curriculum_id": curriculum_id,
                    }
                    logger.info(f"[DRY-RUN] [{name}] سيُسنَد المستوى {level_id} — حلقة {eid}")
                else:
                    stu_api.change_level(sid, eid, level_id, curriculum_id, institution_id)
                    detail["action"] = "assigned"
                    result["assigned"] += 1
                    logger.info(f"[{name}] أُسنِد المستوى {level_id} ✅ — حلقة {eid}")
            except Exception as exc:
                detail["action"] = "failed"
                detail["error"] = str(exc)
                result["failed"] += 1
                logger.error(f"[{name}] فشل إسناد المستوى — حلقة {eid}: {exc}")

            result["details"].append(detail)

    logger.info(
        f"assign_level: أُسنِد={result['assigned']} | تخطٍّ(له خطة)={result['skipped_has_plan']} | "
        f"فشل قراءة={result['read_failed']} | فشل={result['failed']} (dry_run={dry_run})"
    )
    return result
