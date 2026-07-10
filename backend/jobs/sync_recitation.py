"""
مهمة: مزامنة أحادية Supabase → إنجازي لتسميع **يوم واحد** (اليوم افتراضياً).

الاتجاه: Supabase هو المصدر. السياسة (باعتماد المستخدم):
    - يهمّنا تسميع اليوم فقط (لا الـ backlog التاريخي).
    - إن كان للطالب تسميع **مسجّل مسبقاً في إنجازي** لذلك اليوم ⇒ **يُتخطّى** (لا نلمس القائم).
    - وإلا ⇒ **يُضاف** التسميع من Supabase (ADD_RECITED).
    ⇒ لا نُجري أي تعديل (MODIFY) إطلاقاً — إضافةٌ عند الغياب فقط.

الخريطة (من RECITATION_INVESTIGATION.md — مؤكَّدة بفحص حيّ):
    recite_date              → date_of
    students.enjazi_id       → student_id (في المسار وفي الـ body)
    halaqat.enjazi_id        → episode_id
    {lesson,review,side}_start_aya / _end_aya → from_verse_id / to_verse_id (رقم كوني، بلا تحويل)
    {lesson,review,side}_grade → mistakes (عبر grade_to_mistakes)
    std_level_id             → من plan الحالي للطالب

⚠️ نقطة واحدة قيد التأكيد النهائي: شكل payload التسميع **الجديد** بالضبط (action=4 / lesson_id=0).
    الاختبار الحيّ أثبت أن action=1 = تعديل (يُرفض لدرس غير موجود). الفرضية: action=4 = ADD_RECITED.
    لذلك dry_run = True افتراضياً (يطبع الـ payload بلا إرسال). لا تُفعّل الإرسال إلا بعد تأكيد
    الـ payload من HAR لعملية «إضافة تسميع» حقيقية.

المعاملات (params):
    date        — التاريخ المستهدف "YYYY-MM-DD" (افتراضي: اليوم بتوقيت الرياض).
    dry_run     — True (افتراضي) يطبع الـ payloads بلا إرسال؛ False يُرسل فعلياً.
    timezone    — لحساب "اليوم" (افتراضي Asia/Riyadh).
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.recitation import (
    RecitationAPI, build_lesson, grade_to_mistakes,
    PILLAR_LESSON, PILLAR_REVIEW, PILLAR_SIDE,
)
from enjazi.utils.logger import logger
from backend.supabase_client import get_supabase

# من calendar.actions في إنجازي: 1=MODIFY_RECITE، 2=CANCEL_RECITE، 3=ADD_NON_RECITE، 4=ADD_RECITED.
# نستخدم 4 فقط (إضافة تسميع جديد). لا نستخدم 1 (تعديل) إطلاقاً حسب السياسة.
ACTION_ADD_RECITED = 4

# (بادئة حقل Supabase, رقم الركن في إنجازي)
_PILLARS: list[tuple[str, int]] = [
    ("lesson", PILLAR_LESSON),   # 2 = الحفظ
    ("review", PILLAR_REVIEW),   # 3 = المراجعة
    ("side",   PILLAR_SIDE),     # 4 = التثبيت (الجانبي)
]


def _today(tz_name: str) -> str:
    return datetime.now(ZoneInfo(tz_name)).date().isoformat()


def _collect_rows(sb, target_date: str) -> list[dict]:
    """صفوف تسميع اليوم المستهدف، لطلاب مربوطين (student+halqa لهما enjazi_id)، غير مُزامَنة."""
    rows = (
        sb.table("quran_recitation")
        .select(
            "id,recite_date,synced_at,"
            "lesson_start_aya,lesson_end_aya,lesson_grade,"
            "review_start_aya,review_end_aya,review_grade,"
            "side_start_aya,side_end_aya,side_grade,"
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


def _build_lessons(row: dict, std_level_id: int) -> tuple[list[dict], list[str]]:
    """يبني عناصر lessons[] للأركان المُسمَّعة؛ يُرجع (الدروس، أسباب التخطّي)."""
    lessons: list[dict] = []
    skipped: list[str] = []
    for name, pillar in _PILLARS:
        grade = row.get(f"{name}_grade")
        start = row.get(f"{name}_start_aya")
        end = row.get(f"{name}_end_aya")
        mistakes = grade_to_mistakes(grade)
        if mistakes is None:                       # لم يسمع / null / درجة غير معروفة
            skipped.append(f"{name}:{grade or 'null'}")
            continue
        if start is None or end is None:
            skipped.append(f"{name}:no-range")
            continue
        # القيم تُنقل كما هي (الاتجاه المعاكس في المراجعة مقصود: start>end طبيعي).
        lessons.append(build_lesson(
            lesson_id=0,
            pillar_id=pillar,
            std_level_id=std_level_id,
            from_verse_id=int(start),
            to_verse_id=int(end),
            error=mistakes["error"],
            mention=mistakes["mention"],
            tajweed=mistakes["tajweed"],
            action=ACTION_ADD_RECITED,
        ))
    return lessons, skipped


def _mark_synced(sb, row_id: str, note: str | None = None) -> None:
    payload = {"synced_at": datetime.utcnow().isoformat()}
    if note:
        payload["sync_error"] = note      # نستخدم الحقل لتدوين ملاحظة (تخطٍّ) لا خطأ فعلي
    sb.table("quran_recitation").update(payload).eq("id", row_id).execute()


def _mark_error(sb, row_id: str, error: str) -> None:
    sb.table("quran_recitation").update({"sync_error": error[:1000]}).eq("id", row_id).execute()


async def run(params: dict, log_id: int, db: Session) -> dict:
    sb = get_supabase()
    tz_name = params.get("timezone", "Asia/Riyadh")
    target_date = params.get("date") or _today(tz_name)
    dry_run = bool(params.get("dry_run", True))

    rows = _collect_rows(sb, target_date)
    logger.info(
        f"sync_recitation: التاريخ={target_date} | صفوف مؤهّلة={len(rows)} | "
        f"dry_run={dry_run}"
    )

    result = {
        "date": target_date,
        "dry_run": dry_run,
        "eligible": len(rows),
        "added": 0,
        "skipped_existing": 0,   # للطالب تسميع مسجّل مسبقاً في إنجازي
        "skipped_empty": 0,      # لا ركن مُسمَّع (كل الأركان "لم يسمع"/بلا مدى)
        "failed": 0,
        "details": [],
    }
    if not rows:
        logger.info("sync_recitation: لا صفوف مؤهّلة لهذا اليوم")
        return result

    with EnjaziClient() as client:
        get_valid_token(client)
        api = RecitationAPI(client)
        level_cache: dict[tuple[int, int], int | None] = {}

        for row in rows:
            stu = row["students"]
            hal = row["halaqat"]
            sid = int(stu["enjazi_id"])
            eid = int(hal["enjazi_id"])
            name = stu.get("student_name") or str(sid)
            detail = {"student": name, "sid": sid, "eid": eid, "row_id": row["id"]}

            try:
                # (1) هل للطالب تسميع مسجّل مسبقاً في إنجازي لهذا اليوم؟ ⇒ تخطٍّ (لا نلمس القائم)
                hist = api.get_history_lessons(sid, eid, target_date)
                existing = ((hist.get("levels") or [{}])[0] or {}).get("lessons") or []
                if existing:
                    detail["action"] = "skipped_existing"
                    result["skipped_existing"] += 1
                    if not dry_run:
                        _mark_synced(sb, row["id"], note="skipped: موجود مسبقاً في إنجازي")
                    result["details"].append(detail)
                    logger.info(f"[{name}] تسميع موجود مسبقاً في إنجازي ({len(existing)} درس) — تخطٍّ")
                    continue

                # (2) std_level_id الحالي من plan (مع تخزين مؤقت لكل طالب/حلقة)
                key = (sid, eid)
                if key not in level_cache:
                    plan = api.get_plan(sid, eid)
                    level_cache[key] = (
                        ((plan.get("program") or {}).get("level") or {}).get("std_level_id")
                    )
                std_level_id = level_cache[key]
                if not std_level_id:
                    raise ValueError("تعذّر جلب std_level_id من plan")

                # (3) بناء الدروس
                lessons, why_skipped = _build_lessons(row, int(std_level_id))
                if not lessons:
                    detail["action"] = "skipped_empty"
                    detail["reason"] = why_skipped
                    result["skipped_empty"] += 1
                    if not dry_run:
                        _mark_synced(sb, row["id"], note=f"لا ركن مُسمَّع ({','.join(why_skipped)})")
                    result["details"].append(detail)
                    continue

                detail["pillars"] = len(lessons)
                detail["std_level_id"] = std_level_id

                # (4) إرسال أو محاكاة
                if dry_run:
                    detail["action"] = "dry_run"
                    detail["payload"] = {
                        "episode_id": eid, "student_id": sid,
                        "attend_type": "attend", "date_of": target_date,
                        "lessons": lessons,
                    }
                    logger.info(f"[DRY-RUN] [{name}] سيُرسَل {len(lessons)} ركن — {why_skipped and 'تخطّى: '+','.join(why_skipped) or ''}")
                else:
                    api.change_recite(sid, eid, target_date, lessons)
                    _mark_synced(sb, row["id"])
                    detail["action"] = "added"
                    result["added"] += 1
                    logger.info(f"[{name}] أُضيف {len(lessons)} ركن ✅")

                result["details"].append(detail)

            except Exception as exc:
                result["failed"] += 1
                detail["action"] = "failed"
                detail["error"] = str(exc)
                result["details"].append(detail)
                logger.error(f"[{name}] فشل: {exc}")
                if not dry_run:
                    try:
                        _mark_error(sb, row["id"], str(exc))
                    except Exception:
                        pass

    logger.info(
        f"sync_recitation: أُضيف={result['added']} | تخطٍّ(موجود)={result['skipped_existing']} | "
        f"تخطٍّ(فارغ)={result['skipped_empty']} | فشل={result['failed']} (dry_run={dry_run})"
    )
    return result
