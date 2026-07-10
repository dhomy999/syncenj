"""
تجربة ربط طالب موجود مسبقاً في إنجازي عبر نقطة لوحة إنجازي الصحيحة
(batch-operations/register-students) بقائمة من عنصر واحد، حيث id = المعرّف الفعلي.

الطالب 1159952959 موجود برقم 263189. نرسله إلى الحلقة 4242 (M351).
"""
import json
import enjazi.api.students as sm

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
import config.settings as cfg

NID = "1159952959"
ENJAZI_USER_ID = 263189
EPISODE_ID = 4242
PROGRAM_ID = 523
LEVEL_ID = 1744
INSTITUTION_ID = cfg.INSTITUTION_ID

# عنصر واحد في القائمة، id = المعرّف الفعلي (طالب موجود)
single_existing = [{
    "id": ENJAZI_USER_ID,
    "name": "عبدالملك معاذ صالح المحيسن",
    "user_is_changed": True,
    "username": NID,
    "episode_id": EPISODE_ID,
    "program_id": PROGRAM_ID,
    "level_id": LEVEL_ID,
    "original_username": NID,
}]

print("=" * 70)
print(f"batch_register بعنصر واحد (طالب موجود id={ENJAZI_USER_ID})")
print(f"  → الحلقة {EPISODE_ID} | program={PROGRAM_ID} | level={LEVEL_ID}")
print("=" * 70)

with EnjaziClient() as client:
    get_valid_token(client)
    api = StudentsAPI(client)

    # تفعيل البرنامج للمنشأة (كما تفعل اللوحة)
    try:
        api.sync_program_selection(PROGRAM_ID, INSTITUTION_ID)
        print("✓ sync_program_selection تم")
    except Exception as exc:
        print(f"⚠ sync_program_selection فشل (نتابع): {exc}")

    # check-usernames (كما تفعل اللوحة)
    try:
        api.batch_check_usernames([NID], INSTITUTION_ID)
        print("✓ batch_check_usernames تم")
    except Exception as exc:
        print(f"⚠ batch_check_usernames فشل (نتابع): {exc}")

    # التسجيل بعنصر واحد
    try:
        resp = api.batch_register(single_existing, INSTITUTION_ID)
        print("\n✅ استجابة batch_register:")
        print(json.dumps(resp, ensure_ascii=False, indent=2, default=str))
    except Exception as exc:
        print(f"\n❌ خطأ: {exc}")

print("\n" + "=" * 70)
print("انتهت المحاولة")
print("=" * 70)
