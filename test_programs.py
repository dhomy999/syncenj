"""
استخراج كل البرامج ومستوياتها من init-form للمنشأة 539.
نريد تحديد level_id الصالح لبرنامج 523 (حفظ حسب خطة التسميع).
"""
import json
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.base import BaseAPI
import config.settings as cfg

INSTITUTION_ID = cfg.INSTITUTION_ID

with EnjaziClient() as client:
    get_valid_token(client)
    api = BaseAPI(client)
    r = api._get("/institution_panel/students/init-form",
                 headers=cfg.institution_headers(INSTITUTION_ID))

programs = r.get("data", {}).get("programs", [])
print(f"عدد البرامج: {len(programs)}\n")
print(f"{'prog_id':>8} | {'prog_name':30} | {'level_id':>8} | {'level_name':35} | طلاب")
print("-" * 110)
for p in programs:
    pid = p.get("id")
    pname = p.get("name")
    levels = p.get("levels", [])
    if not levels:
        print(f"{pid:>8} | {pname:30} | (لا مستويات)")
    for lv in levels:
        print(f"{pid:>8} | {pname:30} | {lv.get('id'):>8} | {lv.get('name',''):35} | {lv.get('students_count','')}")

# تركيز على برنامج 523
print("\n" + "=" * 70)
print("تفصيل برنامج 523 (إن وُجد):")
print("=" * 70)
p523 = [p for p in programs if p.get("id") == 523]
if p523:
    print(json.dumps(p523[0], ensure_ascii=False, indent=2, default=str)[:2500])
else:
    print("⚠ برنامج 523 غير موجود في init-form! قد لا يكون مفعّلاً للمنشأة.")
    print("  البرامج المتاحة:", [p.get("id") for p in programs])
