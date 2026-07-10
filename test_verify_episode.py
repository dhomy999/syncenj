"""
تحقق: هل اكتمل ربط الطالب 263189 بالحلقة 4242 بعد batch_register؟
ننتظر قليلاً ثم نجلب طلاب الحلقة ونبحث عنه.
"""
import time, json
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.recitation import RecitationAPI
from enjazi.api.students import StudentsAPI
import config.settings as cfg

EPISODE_ID = 4242
TARGET_ID = 263189
TARGET_NID = "1159952959"
INSTITUTION_ID = cfg.INSTITUTION_ID

print("انتظار 20 ثانية ليكتمل الربط غير المتزامن...")
time.sleep(20)

with EnjaziClient() as client:
    get_valid_token(client)
    rec = RecitationAPI(client)
    stu = StudentsAPI(client)

    # 1) قائمة طلاب الحلقة 4242
    students = rec.get_episode_students(EPISODE_ID, INSTITUTION_ID)
    print(f"\n[1] طلاب الحلقة {EPISODE_ID}: {len(students)} طالب")
    match = [s for s in students
             if s.get("id") == TARGET_ID or str(s.get("username")) == TARGET_NID]
    if match:
        print(f"✅ الطالب {TARGET_NID} (id={TARGET_ID}) موجود في الحلقة {EPISODE_ID}:")
        print(json.dumps(match[0], ensure_ascii=False, indent=2, default=str))
    else:
        print(f"❌ الطالب {TARGET_NID} (id={TARGET_ID}) غير موجود بعد في الحلقة {EPISODE_ID}")
        # أظهر عيّنة من القائمة لمعرفة البنية
        if students:
            print("\n  عيّنة من بنية عنصر طالب:")
            print(json.dumps(students[0], ensure_ascii=False, indent=2, default=str))

print("\n" + "=" * 60)
