"""
تشخيص: استجابة batch_check_usernames — هل تكشف level_id الصحيح لكل طالب؟
قراءة فقط (لا تلامس register-students).
"""
import time, json
from backend.jobs.register_students import _collect_eligible, PROGRAM_ID
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
import config.settings as cfg

INSTITUTION_ID = cfg.INSTITUTION_ID

# عيّنة من الطلاب الفاشلين (حلقات 4339/4329) + الناجح سابقاً (4242)
sample_nids = ["1174838704", "1185267430", "1156260539"]  # كلهم فشلوا بـ422

print("=" * 72)
print("batch_check_usernames لعيّنة من الطلاب الفاشلين")
print("=" * 72)

with EnjaziClient() as client:
    get_valid_token(client)
    api = StudentsAPI(client)
    try:
        resp = api.batch_check_usernames(sample_nids, INSTITUTION_ID)
        print(json.dumps(resp, ensure_ascii=False, indent=2, default=str))
    except Exception as exc:
        print(f"❌ خطأ: {exc}")

# جرّب أيضاً جلب مستويات البرنامج إن أمكن
print("\n" + "=" * 72)
print("محاولة جلب مستويات البرنامج (program-builder)...")
print("=" * 72)
try:
    # نقطة رأيناها في HAR: /settings/program-builder/levels/{level_id}/curricula
    r = api._get(
        "/institution_panel/settings/program-builder/levels/1744/curricula",
        headers=cfg.institution_headers(INSTITUTION_ID),
    )
    print(json.dumps(r, ensure_ascii=False, indent=2, default=str)[:2000])
except Exception as exc:
    print(f"(تعذّر): {exc}")
