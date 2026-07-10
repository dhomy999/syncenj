"""
تشخيص: مقارنة السجل الكامل للحلقة 4242 (نجحت بـlevel 1744) مع 4339 (فشلت).
الهدف: إيجاد الحقل الذي يحدّد level_id الصحيح لكل حلقة.
"""
import json
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.episodes import EpisodesAPI
import config.settings as cfg

INSTITUTION_ID = cfg.INSTITUTION_ID
WANT = {4242, 4339, 4329, 4398, 4312, 8741, 4302, 11637, 4335}

with EnjaziClient() as client:
    get_valid_token(client)
    eps = EpisodesAPI(client).list_by_institution(INSTITUTION_ID)

print(f"إجمالي حلقات المنشأة: {len(eps)}\n")
for e in eps:
    if e.get("id") in WANT:
        print(f"=== الحلقة {e.get('id')} ({e.get('name')}) ===")
        # اطبع كل الحقول عدا القوائم الطويلة
        clean = {k: v for k, v in e.items()
                 if k not in ("institution_id", "institution_name")}
        print(json.dumps(clean, ensure_ascii=False, indent=2, default=str))
        print()

# اطبع كل المفاتيح المتاحة في أول حلقة لمعرفة البنية
if eps:
    print("=== كل المفاتيح المتاحة في سجل الحلقة ===")
    print(sorted(eps[0].keys()))
