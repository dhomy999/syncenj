"""
غلاف CLI لاختبار مهمة إسناد المستوى (backend/jobs/assign_level.py) يدويًا.

آمن افتراضيًا: dry_run (محاكاة) وحد أقصى إسناد واحد — لاختبار طالب واحد أولًا.

التشغيل:
    python assign_level_individual.py                      # محاكاة، طالب واحد (لا إرسال)
    python assign_level_individual.py --go                 # إرسال فعلي، طالب واحد
    python assign_level_individual.py --go --limit 5       # إرسال فعلي، 5 طلاب
    python assign_level_individual.py --student 86842 --episode 11640 --go   # طالب بعينه
    python assign_level_individual.py --level 1745         # مستوى مخصّص
    python assign_level_individual.py --limit all          # محاكاة كل الطلاب
    python assign_level_individual.py --limit all --scan 50000 --go   # إرسال للكل
"""
from __future__ import annotations

import sys
import io
import json
import asyncio

# إخراج UTF-8 على ويندوز حتى تظهر الأسماء العربية سليمة
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from backend.jobs.assign_level import run, DEFAULT_LEVEL_ID


def _arg(flag: str, default=None):
    """يقرأ قيمة بعد علم مثل --limit 5."""
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def main() -> None:
    go = "--go" in sys.argv                       # بدونه = محاكاة (dry_run)
    limit_arg = str(_arg("--limit", 1)).lower()
    limit = None if limit_arg == "all" else int(limit_arg)
    params: dict = {
        "dry_run": not go,
        "level_id": int(_arg("--level", DEFAULT_LEVEL_ID)),
        "limit": limit,
        "scan_limit": int(_arg("--scan", 5000)),
    }
    student = _arg("--student")
    episode = _arg("--episode")
    if student and episode:
        params["student_enjazi_id"] = int(student)
        params["episode_id"] = int(episode)

    mode = "إرسال فعلي ✍️" if go else "محاكاة (dry-run) 🧪"
    limit_show = "الكل" if params["limit"] is None else params["limit"]
    print(f"الوضع: {mode} | المستوى: {params['level_id']} | الحد: {limit_show}")
    if student and episode:
        print(f"مستهدف: طالب {student} / حلقة {episode}")
    print("-" * 60)

    result = asyncio.run(run(params, log_id=0, db=None))

    print("-" * 60)
    print("النتيجة:")
    print(f"  مرشّحون          : {result['candidates']}")
    print(f"  أُسنِد            : {result['assigned']}")
    print(f"  تخطٍّ (له خطة)    : {result['skipped_has_plan']}")
    print(f"  فشل قراءة        : {result['read_failed']}")
    print(f"  فشل              : {result['failed']}")

    # تفاصيل أول عنصر (مفيد في المحاكاة لرؤية الـ payload)
    if result["details"]:
        print("\nتفاصيل:")
        for d in result["details"]:
            print("  " + json.dumps(d, ensure_ascii=False))

    if not go and result["details"]:
        print("\n💡 راجع الـ payload أعلاه. للإرسال الفعلي أضف --go")


if __name__ == "__main__":
    main()
