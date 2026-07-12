"""
محرّك المزامنة الشامل: Supabase (quran_recitation) → إنجازي، صفًّا صفًّا وبلا تقييد بتاريخ.

لماذا: teacher_recite كان يمرّ في كل تشغيل على **كل** صفوف اليوم من جديد، ويسأل إنجازي عن
كل طالب ليكتشف أنه مُسجَّل مسبقًا فيتخطّاه. مع الـ rate limit تحوّل هذا إلى ساعات. هنا كل
صف يحمل حالته في Supabase (sync_status)، فالمعالَج لا يُقرأ مرّة أخرى إطلاقًا.

الحالات المُعالَجة لكل صف (بالترتيب):
    1. الطالب غير مسجَّل في إنجازي        ⇒ يُسجَّل (batch_register) ثم يُكتب enjazi_id في Supabase.
    2. الطالب غير موجود في أي حلقة        ⇒ skipped (بسبب واضح).
    3. الطالب في أكثر من حلقة              ⇒ skipped (لا نخمّن الحلقة).
    4. الحلقة مقفلة اليوم                  ⇒ تُفتح (تحضير أول طالب فيها) ثم نُكمل.
    5. الطالب غائب/غير متاح                ⇒ يُحضَّر (attend100) ثم نُكمل.
    6. الركن مُسجَّل مسبقًا في إنجازي        ⇒ يُتخطّى الركن (ويبقى الصف ناجحًا).
    7. لا ركن له نطاق/درجة                 ⇒ skipped (صف فارغ).
    8. أي خطأ آخر                          ⇒ failed + sync_error + sync_attempts++ (يُعاد لاحقًا).

لا يكتب في Supabase إلا: أعمدة المزامنة في quran_recitation، و students.enjazi_id بعد التسجيل.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
from enjazi.api.recitation import RecitationAPI, build_lesson, grade_to_mistakes
from enjazi.teacher_app.client import TeacherAppClient
from enjazi.teacher_app.api import TeacherAPI
from enjazi.utils.logger import logger
from backend.supabase_client import get_supabase
import config.settings as cfg

# من calendar.actions في إنجازي: 4 = ADD_RECITED (إضافة تسميع جديد). لا نستخدم 1 (تعديل).
ACTION_ADD_RECITED = 4
TZ = "Asia/Riyadh"

# رقم الركن في إنجازي → (بادئة حقل Supabase, الاسم)
PILLARS: dict[int, tuple[str, str]] = {
    2: ("lesson", "حفظ"),
    3: ("review", "مراجعة"),
    4: ("side", "تثبيت"),
}
_SKIP_GRADES = {None, "", "لم يسمع"}

# برنامج/مستوى التسجيل (نفس ما تستخدمه مهمة register_students — مؤكَّد من HAR)
PROGRAM_ID = 523
LEVEL_ID = 1744

MAX_ATTEMPTS = 3          # بعدها يبقى الصف failed حتى تُعيد تعيينه يدويًا من صفحة الإحصائيات
DEFAULT_BATCH = 25        # صفوف لكل دورة عامل

_ROW_SELECT = (
    "id,recite_date,sync_status,sync_attempts,"
    "lesson_start_aya,lesson_end_aya,lesson_grade,"
    "review_start_aya,review_end_aya,review_grade,"
    "side_start_aya,side_end_aya,side_grade,"
    "students(id,enjazi_id,student_name,student_national_id),"
    "halaqat(enjazi_id,halqa_code)"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return datetime.now(ZoneInfo(TZ)).date().isoformat()


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


def fetch_pending(sb, limit: int = DEFAULT_BATCH) -> list[dict]:
    """الصفوف المعلّقة (أي تاريخ)، الأقدم أولًا. failed يُعاد حتى MAX_ATTEMPTS."""
    rows = (
        sb.table("quran_recitation")
        .select(_ROW_SELECT)
        .in_("sync_status", ["pending", "failed"])
        .lt("sync_attempts", MAX_ATTEMPTS)
        .order("recite_date")
        .limit(limit)
        .execute()
        .data
    )
    return rows


def _mark(sb, row_id: str, status: str, note: str | None = None, attempts: int | None = None) -> None:
    payload: dict = {"sync_status": status, "last_attempt_at": _now(), "sync_error": note}
    if status in ("synced", "skipped"):
        payload["synced_at"] = _now()
    if attempts is not None:
        payload["sync_attempts"] = attempts
    sb.table("quran_recitation").update(payload).eq("id", row_id).execute()


class _Session:
    """جلسة عمل واحدة: عميلان + خرائط مُخزَّنة، تُعاد استخدامها لكل صفوف الدفعة."""

    def __init__(self, institution_id: str):
        self.institution_id = str(institution_id)
        self.inst = EnjaziClient()
        get_valid_token(self.inst)
        self.stu_api = StudentsAPI(self.inst)
        self.rec_api = RecitationAPI(self.inst)
        self.teacher = TeacherAppClient()
        self.teacher.get_valid_token()
        self.tapi = TeacherAPI(self.teacher)
        self._episode_map: dict[int, list[int]] | None = None
        self._opened: set[int] = set()          # حلقات فُتحت في هذه الدورة
        self._levels: dict[tuple[int, int], int | None] = {}   # (sid,eid) → std_level_id

    def std_level_id(self, sid: int, eid: int) -> int | None:
        key = (sid, eid)
        if key not in self._levels:
            plan = self.rec_api.get_plan(sid, eid)
            self._levels[key] = ((plan.get("program") or {}).get("level") or {}).get("std_level_id")
        return self._levels[key]

    def close(self) -> None:
        self.inst.close()
        self.teacher.close()

    def episode_map(self, refresh: bool = False) -> dict[int, list[int]]:
        """enjazi_id للطالب → حلقاته الحقيقية من لوحة المنشأة (المصدر الموثوق للحلقة)."""
        if self._episode_map is None or refresh:
            students = self.stu_api.list_by_institution(self.institution_id, limit=5000)
            m: dict[int, list[int]] = {}
            for s in students:
                sid = s.get("id")
                eps = [e.get("id") for e in (s.get("episodes_list") or []) if e.get("id")]
                if sid:
                    m[int(sid)] = [int(x) for x in eps]
            self._episode_map = m
            logger.info(f"recite_sync: خريطة الحلقات جاهزة ({len(m)} طالب)")
        return self._episode_map

    def register_student(self, sb, row: dict) -> int | None:
        """يسجّل طالبًا غير موجود في إنجازي ثم يعيد enjazi_id ويكتبه في Supabase."""
        stu = row["students"]
        hal = row["halaqat"]
        nid = str(stu.get("student_national_id") or "").strip()
        name = str(stu.get("student_name") or "").strip()
        episode_id = hal.get("enjazi_id")
        if not nid or not episode_id:
            return None

        payload = [{
            "id": 0,
            "name": name,
            "user_is_changed": True,
            "username": nid,
            "episode_id": int(episode_id),
            "program_id": PROGRAM_ID,
            "level_id": LEVEL_ID,
            "original_username": nid,
        }]
        self.stu_api.batch_register(payload, self.institution_id)
        logger.info(f"[{name}] سُجِّل في إنجازي (حلقة {episode_id})")

        # استخراج enjazi_id الجديد بمطابقة رقم الهوية (username) ثم كتابته في Supabase
        enjazi_id = None
        for s in self.stu_api.list_by_institution(self.institution_id, limit=5000):
            if str(s.get("username") or "").strip() == nid:
                enjazi_id = int(s["id"])
                break
        if enjazi_id:
            sb.table("students").update({"enjazi_id": enjazi_id}).eq("id", stu["id"]).execute()
            self.episode_map(refresh=True)
        return enjazi_id

    def ensure_episode_open(self, eid: int) -> None:
        """يفتح الحلقة إن كانت مقفلة اليوم (بتحضير أول طالب فيها) — مرة واحدة لكل دورة."""
        if eid in self._opened:
            return
        data = self.tapi.get_episode_students(eid)
        if data.get("attended_today"):
            self._opened.add(eid)
            return
        items = data.get("items") or []
        if not items:
            raise RuntimeError(f"الحلقة {eid} بلا طلاب — تعذّر فتحها")
        first = items[0].get("id")
        self.tapi.submit_attendance(eid, [{"student_id": first, "attend_type": "attend"}])
        self._opened.add(eid)
        logger.info(f"فُتحت الحلقة {eid} (عبر الطالب {first})")


def _process_row(s: _Session, sb, row: dict, result: dict, dry_run: bool) -> None:
    stu = row.get("students") or {}
    hal = row.get("halaqat") or {}
    name = stu.get("student_name") or "?"
    attempts = int(row.get("sync_attempts") or 0)
    date = row.get("recite_date")

    # (1) الطالب غير مسجَّل في إنجازي ⇒ سجّله
    sid = stu.get("enjazi_id")
    if not sid:
        if not hal.get("enjazi_id"):
            _mark(sb, row["id"], "skipped", "حلقة الطالب غير مربوطة بإنجازي")
            result["skipped_no_halqa_link"] += 1
            return
        if dry_run:
            result["would_register"] += 1
            return
        sid = s.register_student(sb, row)
        if not sid:
            _mark(sb, row["id"], "failed", "تعذّر تسجيل الطالب في إنجازي", attempts + 1)
            result["failed"] += 1
            return
        result["registered"] += 1
    sid = int(sid)

    # (2/3) الحلقة الحقيقية من إنجازي
    eps = s.episode_map().get(sid, [])
    if not eps:
        _mark(sb, row["id"], "skipped", "الطالب غير موجود في أي حلقة في إنجازي")
        result["skipped_no_episode"] += 1
        return
    if len(eps) > 1:
        _mark(sb, row["id"], "skipped", f"الطالب في {len(eps)} حلقات ({eps}) — لا نخمّن الحلقة")
        result["skipped_multiple_episodes"] += 1
        return
    eid = eps[0]

    # الأركان المطلوبة من هذا الصف
    wanted = {p: rng for p in PILLARS if (rng := _pillar_range(row, p)) is not None}
    if not wanted:
        _mark(sb, row["id"], "skipped", "لا ركن مُسمَّع في الصف")
        result["skipped_empty"] += 1
        return

    if dry_run:
        result["would_recite"] += len(wanted)
        return

    # مسار التاريخ الماضي: تطبيق المعلّم يسجّل على **درس اليوم فقط** (recite/change_starting بلا
    # تاريخ)، فاستخدامه لصف قديم سيكتب التسميع على اليوم — خطأ. لذا نمرّ عبر لوحة المنشأة
    # (change-recite بـ date_of) التي تقبل تاريخًا صريحًا.
    if date != _today():
        _process_past_row(s, sb, row, result, sid, eid)
        return

    # (4) الحلقة مقفلة ⇒ افتحها
    s.ensure_episode_open(eid)

    # (5) الطالب غائب/غير متاح ⇒ حضّره
    try:
        lessons_data = s.tapi.get_student_lessons(sid, eid)
    except Exception as exc:
        if "غير متاح" not in str(exc):
            raise
        lessons_data = None

    attendece = (lessons_data or {}).get("attendece")
    present = bool(lessons_data) and lessons_data.get("has_lessons") and attendece not in ("absent", "not-attend", None)
    if not present:
        s.rec_api.change_recite(sid, eid, date, lessons=[], attend_type="attend100")
        result["attended"] += 1
        logger.info(f"[{name}] حُضِّر (attend100) — حلقة {eid}")
        lessons_data = s.tapi.get_student_lessons(sid, eid)

    if not lessons_data or not lessons_data.get("has_lessons"):
        _mark(sb, row["id"], "skipped", "لا دروس مجدولة للطالب في هذا اليوم")
        result["skipped_not_scheduled"] += 1
        return

    scheduled = {L.get("pillar_id"): L for L in lessons_data.get("lessons", [])}

    recited = 0
    for pillar, (frm, to) in wanted.items():
        pname = PILLARS[pillar][1]
        L = scheduled.get(pillar)
        if not L:
            result["skipped_not_scheduled_pillar"] += 1
            continue
        if L.get("done"):                       # (6) مُسجَّل مسبقًا في إنجازي
            result["skipped_already_done"] += 1
            continue
        s.tapi.change_starting(sid, eid, pillar, frm)
        s.tapi.recite(sid, eid, pillar)
        end = _recited_end(s.tapi, sid, eid, pillar)
        if end is not None and end < to:
            s.tapi.extra_recite(sid, eid, pillar, end + 1, to)
        recited += 1
        result["pillars_recited"] += 1
        logger.info(f"[{name}] {pname}: سُجِّل {frm}→{to} ✅ ({date})")

    _mark(sb, row["id"], "synced", None if recited else "كل الأركان مُسجَّلة مسبقًا في إنجازي")
    result["synced"] += 1


def _process_past_row(s: _Session, sb, row: dict, result: dict, sid: int, eid: int) -> None:
    """صف بتاريخ ماضٍ ⇒ لوحة المنشأة (change-recite بـ date_of) لا تطبيق المعلّم."""
    date = row["recite_date"]
    name = (row.get("students") or {}).get("student_name") or str(sid)

    # مُسجَّل مسبقًا في إنجازي لذلك اليوم ⇒ لا نلمس القائم
    hist = s.rec_api.get_history_lessons(sid, eid, date)
    existing = ((hist.get("levels") or [{}])[0] or {}).get("lessons") or []
    if existing:
        _mark(sb, row["id"], "synced", "موجود مسبقًا في إنجازي")
        result["skipped_already_done"] += 1
        return

    level_id = s.std_level_id(sid, eid)
    if not level_id:
        _mark(sb, row["id"], "skipped", "الطالب غير مُهيّأ في الحلقة (لا خطة/مستوى)")
        result["skipped_not_configured"] += 1
        return

    lessons = []
    for pillar, (pref, _pname) in PILLARS.items():
        mistakes = grade_to_mistakes(row.get(f"{pref}_grade"))
        start, end = row.get(f"{pref}_start_aya"), row.get(f"{pref}_end_aya")
        if mistakes is None or start is None or end is None:
            continue
        lessons.append(build_lesson(
            lesson_id=0,
            pillar_id=pillar,
            std_level_id=int(level_id),
            from_verse_id=int(start),
            to_verse_id=int(end),
            error=mistakes["error"],
            mention=mistakes["mention"],
            tajweed=mistakes["tajweed"],
            action=ACTION_ADD_RECITED,
        ))
    if not lessons:
        _mark(sb, row["id"], "skipped", "لا ركن مُسمَّع في الصف")
        result["skipped_empty"] += 1
        return

    s.rec_api.change_recite(sid, eid, date, lessons, attend_type="attend")
    result["pillars_recited"] += len(lessons)
    result["synced"] += 1
    result["past_rows"] += 1
    _mark(sb, row["id"], "synced")
    logger.info(f"[{name}] ({date}) أُضيف {len(lessons)} ركن عبر لوحة المنشأة ✅")


def _recited_end(api: TeacherAPI, sid: int, eid: int, pillar: int) -> int | None:
    """نهاية الركن كما سجّلها إنجازي بعد recite (قد تقلّ عن المطلوب فنُمدّدها)."""
    try:
        data = api.get_student_lessons(sid, eid)
        for L in data.get("lessons", []):
            if L.get("pillar_id") == pillar:
                return (L.get("to") or {}).get("verse_id")
    except Exception:
        pass
    return None


def process_pending(limit: int = DEFAULT_BATCH, dry_run: bool = False) -> dict:
    """يعالج دفعة من الصفوف المعلّقة (أي تاريخ). يُستدعى من العامل أو يدويًا."""
    sb = get_supabase()
    rows = fetch_pending(sb, limit)

    result = {
        "dry_run": dry_run,
        "picked": len(rows),
        "synced": 0,
        "pillars_recited": 0,
        "registered": 0,
        "attended": 0,
        "skipped_no_halqa_link": 0,
        "skipped_no_episode": 0,
        "skipped_multiple_episodes": 0,
        "skipped_empty": 0,
        "skipped_not_scheduled": 0,
        "skipped_not_scheduled_pillar": 0,
        "skipped_already_done": 0,
        "skipped_not_configured": 0,
        "past_rows": 0,          # صفوف بتاريخ ماضٍ (مسار لوحة المنشأة)
        "failed": 0,
        "would_register": 0,
        "would_recite": 0,
    }
    if not rows:
        return result

    logger.info(f"recite_sync: دفعة {len(rows)} صف معلّق (dry_run={dry_run})")
    s = _Session(cfg.INSTITUTION_ID)
    try:
        for row in rows:
            try:
                _process_row(s, sb, row, result, dry_run)
            except Exception as exc:
                attempts = int(row.get("sync_attempts") or 0) + 1
                name = (row.get("students") or {}).get("student_name") or "?"
                if not dry_run:
                    _mark(sb, row["id"], "failed", f"{type(exc).__name__}: {exc}", attempts)
                result["failed"] += 1
                logger.error(f"[{name}] فشل الصف {row['id']} (محاولة {attempts}): {exc}")
    finally:
        s.close()

    logger.info(
        f"recite_sync: مُزامَن={result['synced']} أركان={result['pillars_recited']} "
        f"مسجَّلون={result['registered']} حُضِّروا={result['attended']} فشل={result['failed']}"
    )
    return result


def stats() -> dict:
    """إحصائيات دقيقة: ماذا زُومن وماذا بقي (لصفحة الإحصائيات)."""
    sb = get_supabase()
    counts: dict[str, int] = {}
    for status in ("pending", "synced", "skipped", "failed"):
        r = (
            sb.table("quran_recitation")
            .select("id", count="exact")
            .eq("sync_status", status)
            .limit(1)
            .execute()
        )
        counts[status] = r.count or 0
    counts["total"] = sum(counts.values())
    counts["stuck"] = (
        sb.table("quran_recitation")
        .select("id", count="exact")
        .eq("sync_status", "failed")
        .gte("sync_attempts", MAX_ATTEMPTS)
        .limit(1)
        .execute()
        .count or 0
    )
    return counts
