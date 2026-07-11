"""
مهمة: إدخال تسميع اليوم لكل طالب عبر **تطبيق المعلّم** (apps/v1)، بمصدر Supabase.

بديل مسار لوحة المنشأة (change-recite الذي يتطلب خطة/سلسلة وكان يفشل). تطبيق المعلّم
يسجّل التسميع على جدول المعلّم مباشرة. الوصفة مؤكَّدة بتجربة حيّة:
    1) change-starting(pillar, from=البداية)   — ينقل بداية الركن، ويحسب نهاية مبدئية.
    2) recite(pillar)                           — يسجّل من البداية للنهاية المحسوبة (درجة ممتاز تلقائيًا).
    3) إن كانت النهاية المحسوبة < المطلوبة: extra-recite(pillar, من النهاية+1, إلى المطلوبة).

السياسة (باعتماد المستخدم):
    - الدرجة «ممتاز» للكل حاليًا (recite يحتسبها تلقائيًا؛ لا نمرّر أخطاء).
    - الشرط: الطالب محضَّر اليوم (has_lessons=true). غير المحضَّر يُتخطّى.
    - يُسجَّل فقط الركن **المجدول اليوم** والذي له نطاق ودرجة ≠ «لم يسمع».
    - idempotent: الركن الذي done=true في التطبيق يُتخطّى (لا يُعاد).
    - dry_run=True افتراضيًا.

المعاملات (params):
    date               — "YYYY-MM-DD" (افتراضي اليوم بتوقيت الرياض).
    dry_run            — True (افتراضي) محاكاة؛ False إرسال فعلي.
    limit              — أقصى عدد طلاب (للاختبار).
    pillars            — قائمة أركان [2,3,4] (افتراضي الثلاثة).
    student_enjazi_id  — (مع episode_id) لاستهداف طالب واحد.
    episode_id         — رقم حلقة إنجازي للطالب المستهدف.
    timezone           — لحساب «اليوم».
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from enjazi.teacher_app.client import TeacherAppClient
from enjazi.teacher_app.api import TeacherAPI
from enjazi.utils.logger import logger
from backend.supabase_client import get_supabase

# رقم الركن في إنجازي → (بادئة حقل Supabase, الاسم)
PILLARS: dict[int, tuple[str, str]] = {
    2: ("lesson", "حفظ"),
    3: ("review", "مراجعة"),
    4: ("side", "تثبيت"),
}
DEFAULT_PILLARS = [2, 3, 4]
_SKIP_GRADES = {None, "", "لم يسمع"}


def _today(tz_name: str) -> str:
    return datetime.now(ZoneInfo(tz_name)).date().isoformat()


def _collect_rows(sb, target_date: str) -> list[dict]:
    """صفوف تسميع اليوم لطلاب مربوطين (student+halqa لهما enjazi_id)."""
    rows = (
        sb.table("quran_recitation")
        .select(
            "id,recite_date,"
            "lesson_start_aya,lesson_end_aya,lesson_grade,"
            "review_start_aya,review_end_aya,review_grade,"
            "side_start_aya,side_end_aya,side_grade,"
            "students(enjazi_id,student_name),halaqat(enjazi_id,halqa_code)"
        )
        .eq("recite_date", target_date)
        .execute()
        .data
    )
    out = []
    for r in rows:
        stu = r.get("students") or {}
        hal = r.get("halaqat") or {}
        if stu.get("enjazi_id") and hal.get("enjazi_id"):
            out.append(r)
    return out


def _pillar_range(row: dict, pillar: int) -> tuple[int, int] | None:
    """نطاق الركن من Supabase مطبّعًا (from=الأصغر, to=الأكبر)، أو None إن لم يُسمَّع."""
    pref, _ = PILLARS[pillar]
    grade = row.get(f"{pref}_grade")
    start = row.get(f"{pref}_start_aya")
    end = row.get(f"{pref}_end_aya")
    if grade in _SKIP_GRADES or start is None or end is None:
        return None
    a, b = int(start), int(end)
    return (min(a, b), max(a, b))


def _pillar_lesson(api: TeacherAPI, sid: int, eid: int, pillar: int) -> dict | None:
    """درس الركن المجدول اليوم (أو None إن لم يكن مجدولًا)."""
    data = api.get_student_lessons(sid, eid)
    if not data.get("has_lessons"):
        return {"_not_attended": True}
    for L in data.get("lessons", []):
        if L.get("pillar_id") == pillar:
            return L
    return None


async def run(params: dict, log_id: int, db: Session) -> dict:
    tz_name = params.get("timezone", "Asia/Riyadh")
    target_date = params.get("date") or _today(tz_name)
    dry_run = bool(params.get("dry_run", True))
    limit = params.get("limit")
    pillars = [int(p) for p in (params.get("pillars") or DEFAULT_PILLARS)]
    one_sid = params.get("student_enjazi_id")
    one_eid = params.get("episode_id")

    sb = get_supabase()
    rows = _collect_rows(sb, target_date)
    if one_sid and one_eid:
        rows = [
            r for r in rows
            if (r["students"]["enjazi_id"] == int(one_sid)
                and r["halaqat"]["enjazi_id"] == int(one_eid))
        ]
    if limit:
        rows = rows[: int(limit)]

    logger.info(
        f"teacher_recite: التاريخ={target_date} | طلاب={len(rows)} | أركان={pillars} | dry_run={dry_run}"
    )

    result = {
        "date": target_date,
        "dry_run": dry_run,
        "students": len(rows),
        "pillars_recited": 0,
        "skipped_not_attended": 0,
        "skipped_not_available": 0,   # «الطالب غير متاح حاليا» من التطبيق
        "skipped_already_done": 0,
        "skipped_no_range": 0,
        "skipped_not_scheduled": 0,
        "failed": 0,
        "details": [],
    }
    if not rows:
        return result

    with TeacherAppClient() as client:
        client.get_valid_token()
        api = TeacherAPI(client)

        for row in rows:
            sid = int(row["students"]["enjazi_id"])
            eid = int(row["halaqat"]["enjazi_id"])
            name = row["students"].get("student_name") or str(sid)

            # درس اليوم المجدول (مرة واحدة للطالب) — للتحقق من الحضور والأركان المجدولة
            try:
                lessons_data = api.get_student_lessons(sid, eid)
            except Exception as exc:
                # «الطالب غير متاح حاليا» = غير محضَّر/متاح اليوم ⇒ تخطٍّ نظيف لا فشل.
                if "غير متاح" in str(exc):
                    result["skipped_not_available"] += 1
                    result["details"].append({"student": name, "sid": sid, "action": "not_available"})
                    logger.info(f"[{name}] غير متاح اليوم في التطبيق — تخطٍّ")
                    continue
                result["failed"] += 1
                result["details"].append({"student": name, "sid": sid, "eid": eid, "error": str(exc)})
                logger.error(f"[{name}] تعذّر جلب الدروس: {exc}")
                continue

            if not lessons_data.get("has_lessons"):
                result["skipped_not_attended"] += 1
                result["details"].append({"student": name, "sid": sid, "action": "not_attended"})
                logger.info(f"[{name}] غير محضَّر اليوم — تخطٍّ")
                continue

            scheduled = {L.get("pillar_id"): L for L in lessons_data.get("lessons", [])}

            for pillar in pillars:
                pname = PILLARS[pillar][1]
                rng = _pillar_range(row, pillar)
                if rng is None:
                    result["skipped_no_range"] += 1
                    continue
                frm, to = rng

                L = scheduled.get(pillar)
                if not L:
                    result["skipped_not_scheduled"] += 1
                    continue
                if L.get("done"):
                    result["skipped_already_done"] += 1
                    continue

                detail = {"student": name, "sid": sid, "eid": eid, "pillar": pillar,
                          "pillar_name": pname, "from": frm, "to": to}
                try:
                    if dry_run:
                        detail["action"] = "dry_run"
                        logger.info(f"[DRY-RUN] [{name}] {pname}: {frm}→{to}")
                    else:
                        # 1) ضبط البداية  2) تسجيل  3) تمديد للنهاية المطلوبة
                        api.change_starting(sid, eid, pillar, frm)
                        api.recite(sid, eid, pillar)
                        computed_end = _recited_end(api, sid, eid, pillar)
                        if computed_end is not None and computed_end < to:
                            api.extra_recite(sid, eid, pillar, computed_end + 1, to)
                            detail["extra"] = [computed_end + 1, to]
                        detail["action"] = "recited"
                        detail["recited_end"] = computed_end
                        result["pillars_recited"] += 1
                        logger.info(f"[{name}] {pname}: سُجِّل {frm}→{to} ✅")
                    result["details"].append(detail)
                except Exception as exc:
                    result["failed"] += 1
                    detail["action"] = "failed"
                    detail["error"] = str(exc)
                    result["details"].append(detail)
                    logger.error(f"[{name}] {pname}: فشل — {exc}")

    logger.info(
        f"teacher_recite: أركان مُسجَّلة={result['pillars_recited']} | غير محضَّر={result['skipped_not_attended']} | "
        f"غير متاح={result['skipped_not_available']} | مسجَّل مسبقًا={result['skipped_already_done']} | "
        f"بلا نطاق={result['skipped_no_range']} | غير مجدول={result['skipped_not_scheduled']} | "
        f"فشل={result['failed']} (dry_run={dry_run})"
    )
    return result


def _recited_end(api: TeacherAPI, sid: int, eid: int, pillar: int) -> int | None:
    """يقرأ نهاية الركن المسجَّلة بعد recite (من درس اليوم المحدّث)."""
    try:
        data = api.get_student_lessons(sid, eid)
        for L in data.get("lessons", []):
            if L.get("pillar_id") == pillar:
                return (L.get("to") or {}).get("verse_id")
    except Exception:
        pass
    return None
