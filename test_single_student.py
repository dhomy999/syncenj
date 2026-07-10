"""
بحث تطبيقي عن طالب واحد + اختبار check-username في إنجازي.
الهدف: معرفة بيانات الطالب 1159952959 وما إذا كان مسجلاً في إنجازي.
"""
import json
from backend.supabase_client import get_supabase
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
import config.settings as cfg

NID = "1159952959"
INSTITUTION_ID = cfg.INSTITUTION_ID

print("=" * 70)
print(f"الطالب المستهدف: رقم الهوية {NID}")
print("=" * 70)

# ── 1) سجل الطالب الكامل من Supabase ─────────────────────────────────────────
sb = get_supabase()
stu_rows = (
    sb.table("students")
    .select("*")
    .eq("student_national_id", NID)
    .execute()
    .data
)
print(f"\n[1] سجل الطالب في Supabase (students): {len(stu_rows)} صف")
if stu_rows:
    print(json.dumps(stu_rows[0], ensure_ascii=False, indent=2, default=str))
    student_id_sb = stu_rows[0].get("id")
else:
    print("⚠️  لم يُعثر على الطالب برقم الهوية هذا في Supabase.")
    student_id_sb = None

# ── 2) تسجيلات الطالب + حلقاتها ──────────────────────────────────────────────
print(f"\n[2] تسجيلات الطالب (enrollments + halaqat):")
if student_id_sb:
    enr_rows = (
        sb.table("enrollments")
        .select("status, halaqat(halqa_code, enjazi_id)")
        .eq("student_id", student_id_sb)
        .execute()
        .data
    )
    print(json.dumps(enr_rows, ensure_ascii=False, indent=2, default=str))
else:
    enr_rows = []
    print("(متخطّى)")

# ── 3) اختبار check-username في إنجازي ───────────────────────────────────────
print(f"\n[3] check-username في إنجازي (institute {INSTITUTION_ID}):")
print("    استجابة فعلية للطلب POST add-user-requests/check-username:")
try:
    with EnjaziClient() as client:
        get_valid_token(client)
        api = StudentsAPI(client)
        resp = api.check_username(NID, INSTITUTION_ID)
        print(json.dumps(resp, ensure_ascii=False, indent=2, default=str))
except Exception as exc:
    print(f"❌ خطأ: {exc}")

print("\n" + "=" * 70)
print("انتهى الفحص")
print("=" * 70)
