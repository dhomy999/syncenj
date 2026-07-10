"""
غلاف CLI فوق مهمة تسجيل الطلاب الفردية (backend/jobs/add_students.py).

المنطق كله في المهمة؛ هذا الملف للتشغيل اليدوي فقط: مخرجات واضحة لكل طالب،
بانر تنبيه بالحالات التي تحتاج مراجعة، وحفظ تقرير مفصّل، مع كتابة enjazi_id عائدًا في Supabase.

التشغيل:
    python add_students_individual.py            # 10 طلاب (افتراضي)
    python add_students_individual.py 25         # عدد مخصّص
    python add_students_individual.py all        # كل المؤهّلين
"""
from __future__ import annotations

import sys
import io
import json

# إخراج UTF-8 على ويندوز حتى تظهر الأسماء العربية سليمة
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
from backend.supabase_client import get_supabase
from backend.jobs.add_students import collect_eligible, process_one, _writeback
import config.settings as cfg


# ── علامات الحالة للعرض ───────────────────────────────────────────────
TAGS = {
    "created":           "✅ [تم الإنشاء]",
    "re_registered":     "♻️ [أُعيد التسجيل]",
    "already_active":    "⏭️  [نشط مسبقًا — تخطّي]",
    "requires_approval": "⚠️  [يتطلب موافقة — لم يُضف]",
    "unknown_code":      "❗ [كود غير معروف — لم يُضف]",
    "failed":            "❌ [فشل]",
    "check_error":       "❌ [فشل فحص الهوية]",
}


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "10"
    process_all = str(arg).lower() == "all"
    limit = None if process_all else int(arg)
    institution_id = cfg.INSTITUTION_ID

    sb = get_supabase()
    eligible = collect_eligible(sb)
    target_list = eligible if process_all else eligible[:limit]
    target = len(target_list)
    print(f"إجمالي المؤهّلين: {len(eligible)} — سنعالج {target} (المنشأة {institution_id})\n")

    results = []

    with EnjaziClient() as client:
        get_valid_token(client)
        api = StudentsAPI(client)

        for i, e in enumerate(target_list, 1):
            head = f"[{i}/{target}] {e['name']}  (هوية {e['username']}, حلقة {e['halqa_code']}→{e['episode_id']})"
            print(head)

            rec = process_one(api, e, institution_id)
            tag = TAGS.get(rec["status"], rec["status"])
            rec["tag"] = tag

            print(f"       فحص الهوية: code={rec['code']}"
                  + (f", id_قائم={rec['enjazi_id']}" if rec.get("enjazi_id") else ""))

            # كتابة enjazi_id عائدًا في Supabase (نفس منطق المهمة)
            if rec.get("enjazi_id") and _writeback(sb, rec["username"], rec["enjazi_id"]):
                rec["writeback"] = True

            line = f"       {tag}"
            if rec.get("enjazi_id"):
                line += f" — enjazi_id={rec['enjazi_id']}"
            if rec.get("error"):
                line += f" — {_short(rec['error'])}"
            print(line + "\n")

            results.append(rec)

    _summary(results)

    out = "add_students_result.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"تقرير مفصّل محفوظ في: {out}")


def _summary(results):
    from collections import Counter
    counts = Counter(r["status"] for r in results)
    print("=" * 64)
    print("ملخّص الحالات:")
    labels = {
        "created": "تم الإنشاء", "re_registered": "أُعيد تسجيلهم",
        "already_active": "نشط مسبقًا (تخطّي)", "requires_approval": "يتطلب موافقة",
        "unknown_code": "كود غير معروف", "failed": "فشل", "check_error": "فشل الفحص",
    }
    for key, label in labels.items():
        if counts.get(key):
            print(f"  {label:<24}: {counts[key]}")
    print(f"  {'الإجمالي':<24}: {len(results)}")

    # ── بانر التنبيه: كل ما يحتاج انتباهك ──
    attention = [r for r in results if r["status"] in
                 ("failed", "check_error", "requires_approval", "unknown_code")]
    if attention:
        print("\n" + "🚨" * 20)
        print("انتبه — الحالات التالية تحتاج مراجعة (انسخها لي لنحلّلها سويًا):")
        print("🚨" * 20)
        for r in attention:
            print(f"\n  {r['tag']}  {r['name']} ({r['username']}) — حلقة {r['halqa_code']}")
            print(f"      code = {r['code']}")
            if r.get("error"):
                print(f"      التفاصيل: {r['error']}")
    else:
        print("\n✔ لا توجد حالات تحتاج انتباهك — كل شيء تم بنجاح.")
    print()


def _short(v, limit: int = 400) -> str:
    try:
        s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    except Exception:
        s = str(v)
    return s if len(s) <= limit else s[:limit] + "…"


if __name__ == "__main__":
    main()
