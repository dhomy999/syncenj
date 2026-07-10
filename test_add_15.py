"""
تجربة مسار الطالب الفردي على 15 طالباً مؤهّلاً.

لكل طالب على حدة:
  1. check_username  → معرفة الحالة (موجود/جديد/يحتاج موافقة) + المعرّف الفعلي إن وُجد
  2. batch_register  → بقائمة من عنصر واحد (id = المعرّف الفعلي إن وُجد، وإلا 0)
  3. تسجيل أي مشكلة

في النهاية: كتابة enjazi_id للطلاب الموجودين + تحقق من الظهور في الحلقات.
"""
import time, json
from collections import defaultdict

from backend.supabase_client import get_supabase
from backend.jobs.register_students import _collect_eligible, PROGRAM_ID, LEVEL_ID
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
from enjazi.api.recitation import RecitationAPI
import config.settings as cfg

N = 15
INSTITUTION_ID = cfg.INSTITUTION_ID

# ── 1) جمع 15 طالباً مؤهّلاً ─────────────────────────────────────────────────
sb = get_supabase()
eligible = _collect_eligible(sb)[:N]
print(f"عدد المؤهّلين المختارين للتجربة: {len(eligible)}\n")
for i, e in enumerate(eligible, 1):
    print(f"  {i:2}. {e['username']} | {e['name']} | حلقة {e['halqa_code']} (ep {e['episode_id']})")

# ─ـ 2) المعالجة الفردية ──────────────────────────────────────────────────────
results = []
with EnjaziClient() as client:
    get_valid_token(client)
    api = StudentsAPI(client)

    # تفعيل البرنامج مرّة واحدة (كما تفعل اللوحة)
    try:
        api.sync_program_selection(PROGRAM_ID, INSTITUTION_ID)
        print("\n✓ sync_program_selection تم")
    except Exception as exc:
        print(f"\n⚠ sync_program_selection فشل (نتابع): {exc}")

    print(f"\nبدء معالجة {len(eligible)} طالباً (مسار فردي)...\n")

    for i, e in enumerate(eligible, 1):
        nid, name, ep = e["username"], e["name"], e["episode_id"]
        rec = {"idx": i, "username": nid, "name": name,
               "halqa": e["halqa_code"], "episode_id": ep,
               "check_code": None, "enjazi_id": None, "reg_ok": None,
               "direct": 0, "approval": 0, "error": None}

        # (أ) check_username
        try:
            ck = api.check_username(nid, INSTITUTION_ID)
            d = ck.get("data", {}) if isinstance(ck, dict) else {}
            rec["check_code"] = d.get("code")
            user = d.get("user") or {}
            rec["enjazi_id"] = user.get("id")
            rec["check_msg"] = d.get("message")
        except Exception as exc:
            rec["error"] = f"check_username: {exc}"
            results.append(rec)
            print(f"  [{i:2}/{len(eligible)}] {nid} ❌ check فشل: {exc}")
            continue

        # (ب) batch_register بعنصر واحد
        payload_id = rec["enjazi_id"] if rec["enjazi_id"] else 0
        single = [{
            "id": payload_id,
            "name": name,
            "user_is_changed": True,
            "username": nid,
            "episode_id": ep,
            "program_id": PROGRAM_ID,
            "level_id": LEVEL_ID,
            "original_username": nid,
        }]
        try:
            r = api.batch_register(single, INSTITUTION_ID)
            rd = r.get("data", {}) if isinstance(r, dict) else {}
            rec["reg_ok"] = bool(r.get("success", False))
            rec["direct"] = rd.get("direct_register_count", 0)
            rec["approval"] = rd.get("approval_required_count", 0)
            rec["reg_msg"] = rd.get("message")
            flag = "✓" if rec["reg_ok"] else "⚠"
            print(f"  [{i:2}/{len(eligible)}] {nid} {flag} code={rec['check_code']} "
                  f"id={rec['enjazi_id']} direct={rec['direct']} appr={rec['approval']}")
        except Exception as exc:
            rec["error"] = f"batch_register: {exc}"
            print(f"  [{i:2}/{len(eligible)}] {nid} ❌ register فشل: {exc}")

        results.append(rec)

# ── 3) كتابة enjazi_id للطلاب الموجودين في إنجازي ─────────────────────────────
writebacks = [r for r in results if r["enjazi_id"] and r["reg_ok"]]
print(f"\nكتابة enjazi_id لـ {len(writebacks)} طالب (الموجودين في إنجازي)...")
ok_wb = 0
for r in writebacks:
    try:
        sb.table("students").update({"enjazi_id": r["enjazi_id"]}).eq(
            "student_national_id", r["username"]).execute()
        ok_wb += 1
    except Exception as exc:
        print(f"  ⚠ فشل كتابة enjazi_id لـ {r['username']}: {exc}")
print(f"✓ كُتب {ok_wb} من {len(writebacks)}")

# ── 4) التحقق من الظهور في الحلقات (تجميعاً) ──────────────────────────────────
print(f"\nانتظار 25 ثانية ليكتمل الربط غير المتزامن...")
time.sleep(25)

by_ep = defaultdict(list)
for r in results:
    if r["reg_ok"]:
        by_ep[r["episode_id"]].append(r)

print("\nالتحقق من الظهور في الحلقات:")
with EnjaziClient() as client:
    get_valid_token(client)
    rec_api = RecitationAPI(client)
    for ep, recs in by_ep.items():
        try:
            members = rec_api.get_episode_students(ep, INSTITUTION_ID)
            member_nids = {str(m.get("username")) for m in members}
            for r in recs:
                present = r["username"] in member_nids
                r["verified_in_episode"] = present
                mark = "✅" if present else "⏳"
                print(f"  {mark} {r['username']} → حلقة {ep} ({len(members)} طالب)")
        except Exception as exc:
            print(f"  ⚠ تعذّر جلب طلاب الحلقة {ep}: {exc}")

# ── 5) ملخّص نهائي ───────────────────────────────────────────────────────────
print("\n" + "=" * 72)
print("الملخّص النهائي")
print("=" * 72)
exists = [r for r in results if r["check_code"] == "already_exists"]
news   = [r for r in results if r["check_code"] and r["check_code"] != "already_exists"]
reg_ok = [r for r in results if r["reg_ok"]]
errs   = [r for r in results if r["error"]]
ver_ok = [r for r in results if r.get("verified_in_episode")]
print(f"  موجودون في إنجازي (already_exists): {len(exists)}")
print(f"  جدد/حالات أخرى:                     {len(news)}")
print(f"  نجح التسجيل (batch_register):        {len(reg_ok)}")
print(f"  فشل:                                 {len(errs)}")
print(f"  تأكّد ظهورهم في الحلقة:              {len(ver_ok)}")
print(f"  كُتب enjazi_id في Supabase:         {ok_wb}")

if news:
    print("\n  — حالات غير (already_exists) (للمراجعة):")
    for r in news:
        print(f"     {r['username']}: code={r['check_code']} | {r.get('check_msg')}")
if errs:
    print("\n  — أخطاء:")
    for r in errs:
        print(f"     {r['username']}: {r['error']}")

print("\nتفاصيل كاملة (JSON):")
print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
