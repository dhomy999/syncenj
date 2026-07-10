"""
اختبار حاسم: تسجيل طالب فشل سابقاً (87414 / 1174838704)
ببرنامج متاح (524 مراجعة / المستوى 1747) بدل 523 غير المتاح.
"""
import time, json
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
import config.settings as cfg

INSTITUTION_ID = cfg.INSTITUTION_ID
NID = "1174838704"
EPISODE_ID = 4329
PROGRAM_ID = 523      # حفظ — تفعّل الآن
LEVEL_ID = 1744       # التزام حال الحضور (المستوى الأساسي، 1618 طالب)

single = [{
    "id": 0,
    "name": "فيصل مسعود حمد الشهراني",
    "user_is_changed": True,
    "username": NID,
    "episode_id": EPISODE_ID,
    "program_id": PROGRAM_ID,
    "level_id": LEVEL_ID,
    "original_username": NID,
}]

print(f"تجربة: {NID} → حلقة {EPISODE_ID} | program={PROGRAM_ID} (مراجعة) | level={LEVEL_ID}")
print("=" * 60)
with EnjaziClient() as client:
    get_valid_token(client)
    api = StudentsAPI(client)
    try:
        r = api.batch_register(single, INSTITUTION_ID)
        rd = r.get("data", {}) if isinstance(r, dict) else {}
        print("استجابة batch_register:")
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
        if r.get("success"):
            print(f"\n✅ نجح! direct={rd.get('direct_register_count')} "
                  f"approval={rd.get('approval_required_count')}")
            print("انتظار 25ث للتحقق...")
            time.sleep(25)
            from enjazi.api.recitation import RecitationAPI
            members = RecitationAPI(client).get_episode_students(EPISODE_ID, INSTITUTION_ID)
            found = [m for m in members if str(m.get("username")) == NID]
            print(f"  → {'✅ ظهر في الحلقة' if found else '⏳ لم يظهر بعد'} (طلاب الحلقة={len(members)})")
    except Exception as exc:
        print(f"❌ خطأ: {exc}")
