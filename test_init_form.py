"""
حسم: ما المستويات/البرامج الصحيحة المتاحة للمنشأة؟
نجرب init-form و program-builder لإيجاد level_id الصالح للتسجيل.
قراءة فقط.
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

    print("=" * 70)
    print("[1] students/init-form")
    print("=" * 70)
    try:
        r = api._get("/institution_panel/students/init-form",
                     headers=cfg.institution_headers(INSTITUTION_ID))
        # اطبع مختصراً: ابحث عن أي قوائم تحتوي level/program
        txt = json.dumps(r, ensure_ascii=False)
        print(txt[:3000])
    except Exception as exc:
        print(f"(تعذّر): {exc}")

    import time; time.sleep(2)

    print("\n" + "=" * 70)
    print("[2] settings/program-builder/programs (قائمة البرامج)")
    print("=" * 70)
    for path in [
        "/institution_panel/settings/program-builder/programs",
        "/institution_panel/settings/program-builder",
        "/institution_panel/settings/program-builder/levels",
    ]:
        try:
            r = api._get(path, headers=cfg.institution_headers(INSTITUTION_ID))
            txt = json.dumps(r, ensure_ascii=False)
            print(f"\n--- {path} ---")
            print(txt[:1500])
        except Exception as exc:
            print(f"\n--- {path} ---\n(تعذّر): {exc}")
