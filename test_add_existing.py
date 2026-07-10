"""
تجربة إضافة الطالب 1159952959 (الموجود مسبقاً في إنجازي برقم 263189)
إلى حلقة منشأتنا عبر مسار الطالب الواحد: add_existing (POST /students/{id}/add).

الطالب مسجّل في حلقتين: M351→4242 و A351→3508. نجرّب M351 (4242).
"""
import json
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI, NewStudent
import config.settings as cfg

NID = "1159952959"
ENJAZI_USER_ID = 263189       # من check-username
INSTITUTION_ID = cfg.INSTITUTION_ID

student = NewStudent(
    username      = NID,
    name          = "عبدالملك معاذ صالح المحيسن",
    date_of_birth = "2012-05-05",   # من birth_date في Supabase
    episode_id    = 4242,           # M351
    program       = 523,
    level_id      = 1744,           # مؤكَّد من HAR للمنشأة 539
    gender_id     = 1,              # ذكر
    phone         = "554356611",    # بدون الصفر البادئ + رمز الدولة 966 افتراضياً
    guardian_phone = "554356611",
)

print("=" * 70)
print(f"محاولة add_existing: الطالب {NID} (enjazi id={ENJAZI_USER_ID})")
print(f"  → الحلقة {student.episode_id} | program={student.program} | level={student.level_id}")
print("=" * 70)

with EnjaziClient() as client:
    get_valid_token(client)
    api = StudentsAPI(client)
    try:
        resp = api.add_existing(ENJAZI_USER_ID, student, INSTITUTION_ID)
        print("\n✅ استجابة add_existing (POST /students/263189/add):")
        print(json.dumps(resp, ensure_ascii=False, indent=2, default=str))
    except Exception as exc:
        print(f"\n❌ خطأ: {exc}")

print("\n" + "=" * 70)
print("انتهت المحاولة")
print("=" * 70)
