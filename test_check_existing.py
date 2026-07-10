"""
تحقق: هل الطلاب الفاشلون (422) مسجّلون أصلاً في منشأتنا 539؟
نبحث عنهم في طلاب المنشأة وفي طلاب حلقاتهم المستهدفة.
قراءة فقط.
"""
import json
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
from enjazi.api.recitation import RecitationAPI
import config.settings as cfg

INSTITUTION_ID = cfg.INSTITUTION_ID
# (student_id, national_id, target_episode)
TARGETS = [
    (87414, "1174838704", 4329),
    (87912, "1185267430", 4339),
    (87876, "1156260539", 4339),
    (87856, "1181321363", 4398),
    (263189, "1159952959", 4242),   # الناجح سابقاً (للمقارنة)
]

with EnjaziClient() as client:
    get_valid_token(client)
    stu = StudentsAPI(client)
    rec = RecitationAPI(client)

    # 1) هل هم في قائمة طلاب المنشأة 539؟
    print("[1] البحث في قائمة طلاب المنشأة 539...")
    all_students = stu.list_by_institution(INSTITUTION_ID, limit=2000)
    print(f"    إجمالي طلاب المنشأة: {len(all_students)}")
    inst_map = {s["id"]: s for s in all_students}
    for sid, nid, ep in TARGETS:
        s = inst_map.get(sid)
        if s:
            eps = s.get("episodes_list") or s.get("episodes") or []
            print(f"    • {nid} (id={sid}): موجود في المنشأة ← "
                  f"episodes={eps if eps else '(لا قائمة)'}")
        else:
            print(f"    • {nid} (id={sid}): غير موجود في قائمة المنشأة")

    # 2) هل هم أصلاً في حلقاتهم المستهدفة؟
    print("\n[2] هل هم في حلقاتهم المستهدفة؟")
    eps_to_check = {}
    for sid, nid, ep in TARGETS:
        eps_to_check.setdefault(ep, []).append((sid, nid))
    for ep, members_info in eps_to_check.items():
        try:
            members = rec.get_episode_students(ep, INSTITUTION_ID)
            ids = {m.get("student_id") for m in members}
            for sid, nid in members_info:
                mark = "✅ موجود بالفعل" if sid in ids else "➖ غير موجود"
                print(f"    • {nid} (id={sid}) في الحلقة {ep}: {mark} (طلاب الحلقة={len(members)})")
        except Exception as exc:
            print(f"    ⚠ تعذّر جلب طلاب الحلقة {ep}: {exc}")
