"""
اختبار إدخال تسميع فردي لطالب واحد عبر **تطبيق المعلّم** (apps/v1)، بمصدر Supabase.

الفكرة: نترك مسار لوحة المنشأة (change-recite الذي يتطلب خطة/سلسلة) ونستخدم تطبيق
المعلّم الذي يسجّل التسميع على جدول المعلّم مباشرة. الشرط: الطالب محضَّر اليوم.

آمن افتراضيًا: تشخيص فقط (لا إرسال). يعرض:
    (أ) ما يقوله Supabase (النطاق المطلوب لكل ركن)
    (ب) ما جدوله تطبيق المعلّم اليوم لهذا الطالب (from/to + الحالة)
مع --go: يسجّل الركن المختار فعليًا ثم يعرض السجل الناتج (history-lessons).

التشغيل (على سيرفر Dokploy — يحتاج بيانات دخول المعلّم في البيئة):
    python teacher_recite_individual.py --student 30364 --episode 4339            # تشخيص
    python teacher_recite_individual.py --student 30364 --episode 4339 --go       # تسجيل حفظ (ركن 2)
    python teacher_recite_individual.py --student 30364 --episode 4339 --pillar 3 --start 5105 --go
    python teacher_recite_individual.py --student 30364 --episode 4339 --date 2026-07-11

الأركان: 2=حفظ (بدايته مقفلة على الخطة) | 3=مراجعة | 4=تثبيت
"""
from __future__ import annotations

import sys
import io
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# إخراج UTF-8 على ويندوز
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from enjazi.teacher_app.client import TeacherAppClient
from enjazi.teacher_app.api import TeacherAPI
from backend.supabase_client import get_supabase

# (بادئة حقل Supabase, رقم الركن في إنجازي, الاسم)
PILLARS = {2: ("lesson", "حفظ"), 3: ("review", "مراجعة"), 4: ("side", "تثبيت")}


def _arg(flag: str, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def _today() -> str:
    return datetime.now(ZoneInfo("Asia/Riyadh")).date().isoformat()


def _fetch_supabase_row(sb, student_enjazi: int, episode_enjazi: int, date_of: str) -> dict | None:
    """صف تسميع اليوم لطالب/حلقة (بالمطابقة على enjazi_id بعد الجلب)."""
    rows = (
        sb.table("quran_recitation")
        .select(
            "id,recite_date,synced_at,"
            "lesson_start_aya,lesson_end_aya,lesson_grade,"
            "review_start_aya,review_end_aya,review_grade,"
            "side_start_aya,side_end_aya,side_grade,"
            "students(enjazi_id,student_name),halaqat(enjazi_id,halqa_code)"
        )
        .eq("recite_date", date_of)
        .execute()
        .data
    )
    for r in rows:
        stu = r.get("students") or {}
        hal = r.get("halaqat") or {}
        if stu.get("enjazi_id") == student_enjazi and hal.get("enjazi_id") == episode_enjazi:
            return r
    return None


def _print_supabase_target(row: dict) -> None:
    print("── ما يقوله Supabase (المطلوب) ──")
    stu = row.get("students") or {}
    print(f"  الطالب: {stu.get('student_name')}  | التاريخ: {row.get('recite_date')}"
          f"  | synced_at: {row.get('synced_at')}")
    for pid, (pref, name) in PILLARS.items():
        s, e, g = row.get(f"{pref}_start_aya"), row.get(f"{pref}_end_aya"), row.get(f"{pref}_grade")
        print(f"  ركن {pid} ({name}): من {s} إلى {e} | الدرجة: {g}")


def main() -> None:
    student = _arg("--student")
    episode = _arg("--episode")
    if not student or not episode:
        print("لازم --student <enjazi_id> و --episode <enjazi_id>")
        sys.exit(1)
    student, episode = int(student), int(episode)
    date_of = _arg("--date", _today())
    pillar = int(_arg("--pillar", 2))
    start = _arg("--start")  # اختياري: نقل البداية (لغير الحفظ)
    go = "--go" in sys.argv

    print(f"طالب {student} | حلقة {episode} | تاريخ {date_of} | ركن {pillar} "
          f"({PILLARS.get(pillar, ('', '?'))[1]}) | {'إرسال ✍️' if go else 'تشخيص 🧪'}")
    print("=" * 64)

    sb = get_supabase()
    row = _fetch_supabase_row(sb, student, episode, date_of)
    if not row:
        print(f"⚠️ لا يوجد صف في quran_recitation لهذا الطالب/الحلقة بتاريخ {date_of}.")
        sys.exit(1)
    _print_supabase_target(row)

    print("\n── تطبيق المعلّم ──")
    with TeacherAppClient() as client:
        client.get_valid_token()
        api = TeacherAPI(client)

        # (أ) درس اليوم المجدول للطالب
        try:
            lessons = api.get_student_lessons(student, episode)
            print("  درس اليوم المجدول (lessons):")
            print("  " + json.dumps(lessons, ensure_ascii=False)[:1500])
        except Exception as exc:
            print(f"  ❌ تعذّر جلب lessons: {exc}")
            print("  (غالبًا الطالب غير محضَّر اليوم — التحضير شرط لتفعيل has_lessons)")
            if not go:
                return

        if not go:
            print("\n💡 راجع المقارنة أعلاه. للتسجيل الفعلي أضف --go")
            return

        # (ب) تسجيل فعلي
        pref, pname = PILLARS.get(pillar, ("lesson", "؟"))
        try:
            if start and pillar != 2:
                print(f"\n  → change-starting: ركن {pillar} إلى الآية {start}")
                r1 = api.change_starting(student, episode, pillar, int(start))
                print("    " + json.dumps(r1, ensure_ascii=False)[:600])

            print(f"\n  → recite: ركن {pillar} ({pname})")
            r2 = api.recite(student, episode, pillar)
            print("    " + json.dumps(r2, ensure_ascii=False)[:600])
        except Exception as exc:
            print(f"  ❌ فشل التسجيل: {exc}")
            return

        # (ج) التحقق من الناتج
        try:
            print("\n  → التحقق (history-lessons):")
            hist = api.get_history_lessons(student, episode, date_of)
            print("    " + json.dumps(hist, ensure_ascii=False)[:1500])
        except Exception as exc:
            print(f"  ⚠️ تعذّر التحقق: {exc}")

    print("\n✅ انتهى. قارن النطاق المسجَّل مع المطلوب من Supabase.")


if __name__ == "__main__":
    main()
