"""
مهمة: تسجيل الطلاب الجدد فرديًا في إنجازي (العملية 1 — تعمل الساعة 1 صباحًا).

المصدر: جدول students في Supabase — كل طالب بلا enjazi_id، في حلقة مربوطة بإنجازي.
المسار الفردي المتزامن (يُنشئ الحساب فورًا ويُرجع enjazi_id):
    POST /institution_panel/add-user-requests/check-username   → يرجع code يحدّد الحالة
    ثم حسب code:
        new                            → POST /institution_panel/students            (إنشاء حساب جديد)
        exists_user_deleted            → POST /institution_panel/students/{id}/add    (إعادة تسجيل حساب قائم)
        already_exists                 → لا إنشاء (نشط في حلقة أصلًا) — لكن نربط enjazi_id إن توفّر
        exists_user_requires_approval  → لم يُضف (يحتاج مسار موافقة) — نربط enjazi_id إن توفّر
        (أي كود آخر)                    → لم يُضف (كود غير معروف — يظهر في attention)

بعد كل نجاح/ربط: يُكتب enjazi_id عائدًا في Supabase (students.enjazi_id) لضمان عدم
إعادة معالجة الطالب في تشغيل الليلة التالية (idempotency).

هذا الملف هو مصدر المنطق؛ سكربت add_students_individual.py في الجذر غلاف CLI رقيق فوقه.
"""
from __future__ import annotations

import json
from datetime import date

from sqlalchemy.orm import Session

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI, NewStudent
from enjazi.utils.logger import logger
from backend.supabase_client import get_supabase
import config.settings as cfg

PROGRAM_ID = 523
LEVEL_ID = 1744
_ACTIVE = "نشط"


def collect_eligible(sb) -> list[dict]:
    """طلاب غير مربوطين، في حلقة مربوطة بإنجازي، بلا تكرار برقم الهوية."""
    # يُحسب داخل الدالة (لا وقت الاستيراد) لأن الخادم عملية طويلة العمر قد تمتد لأيام.
    placeholder_dob = date.today().isoformat()

    rows = (
        sb.table("enrollments")
        .select(
            "status,"
            "students(student_national_id,student_name,enjazi_id,mobile_phone_1,birth_date,nationality),"
            "halaqat(halqa_code,enjazi_id)"
        )
        .eq("status", _ACTIVE)
        .execute()
        .data
    )

    by_nid: dict[str, dict] = {}
    for r in rows:
        stu = r.get("students") or {}
        hal = r.get("halaqat") or {}
        nid = str(stu.get("student_national_id") or "").strip()
        episode_id = hal.get("enjazi_id")

        if not nid or stu.get("enjazi_id") is not None or episode_id is None or nid in by_nid:
            continue

        dob = stu.get("birth_date") or placeholder_dob
        by_nid[nid] = {
            "username": nid,
            "name": str(stu.get("student_name") or "").strip(),
            "episode_id": int(episode_id),
            "halqa_code": hal.get("halqa_code"),
            "phone": str(stu.get("mobile_phone_1") or "").strip(),
            "date_of_birth": str(dob)[:10],
        }
    return list(by_nid.values())


def _build_student(e: dict, program_id: int = PROGRAM_ID, level_id: int = LEVEL_ID) -> NewStudent:
    return NewStudent(
        username=e["username"],
        name=e["name"],
        date_of_birth=e["date_of_birth"],
        episode_id=e["episode_id"],
        program=program_id,
        level_id=level_id,
        phone=e["phone"],
        guardian_phone=e["phone"],
    )


def _parse_check(check) -> tuple[str | None, int | None]:
    """يستخرج (code, existing_enjazi_id) من استجابة فحص الهوية."""
    if not isinstance(check, dict):
        return None, None
    data = check.get("data") or {}
    code = data.get("code")
    existing_id = (data.get("user") or {}).get("id")
    return code, existing_id


def _writeback(sb, national_id: str, enjazi_id: int) -> bool:
    """يكتب enjazi_id عائدًا في Supabase (students.student_national_id == username)."""
    if not enjazi_id:
        return False
    try:
        sb.table("students").update({"enjazi_id": int(enjazi_id)}) \
            .eq("student_national_id", national_id).execute()
        return True
    except Exception as exc:
        logger.warning(f"تعذّرت كتابة enjazi_id={enjazi_id} للهوية {national_id}: {exc}")
        return False


def process_one(
    api: StudentsAPI,
    e: dict,
    institution_id: str,
    program_id: int = PROGRAM_ID,
    level_id: int = LEVEL_ID,
) -> dict:
    """يعالج طالبًا واحدًا (فحص الهوية + التفرّع). يُرجع سجلًا موحّدًا بلا كتابة Supabase."""
    rec = {
        "username": e["username"], "name": e["name"],
        "halqa_code": e["halqa_code"], "episode_id": e["episode_id"],
        "phone": e["phone"], "date_of_birth": e["date_of_birth"],
        "code": None, "status": None, "enjazi_id": None, "error": None,
    }

    # 1) فحص الهوية
    try:
        check = api.check_username(e["username"], institution_id)
    except Exception as exc:
        rec["status"] = "check_error"
        rec["error"] = f"{type(exc).__name__}: {exc}"
        return rec

    code, existing_id = _parse_check(check)
    rec["code"] = code
    student = _build_student(e, program_id, level_id)

    if code == "new":
        try:
            resp = api.add(student, institution_id)
            new_id = resp.get("id") if isinstance(resp, dict) else None
            rec["status"] = "created"
            rec["enjazi_id"] = new_id
        except Exception as exc:
            rec["status"] = "failed"
            rec["error"] = f"{type(exc).__name__}: {exc}"

    elif code == "exists_user_deleted":
        if not existing_id:
            rec["status"] = "failed"
            rec["error"] = "لا يوجد id قائم في استجابة الفحص"
            return rec
        try:
            resp = api.add_existing(existing_id, student, institution_id)
            ok = isinstance(resp, dict) and resp.get("success", True)
            if ok:
                rec["status"] = "re_registered"
                rec["enjazi_id"] = existing_id
            else:
                rec["status"] = "failed"
                rec["error"] = json.dumps(resp, ensure_ascii=False)[:1000]
        except Exception as exc:
            rec["status"] = "failed"
            rec["error"] = f"{type(exc).__name__}: {exc}"

    elif code == "already_exists":
        rec["status"] = "already_active"
        rec["enjazi_id"] = existing_id

    elif code == "exists_user_requires_approval":
        rec["status"] = "requires_approval"
        rec["enjazi_id"] = existing_id

    else:
        rec["status"] = "unknown_code"
        rec["error"] = f"check={json.dumps(check, ensure_ascii=False)[:400]}"

    return rec


# الحالات التي تحتاج انتباه المستخدم (تظهر في نتيجة السجل)
_ATTENTION_STATUSES = {"failed", "check_error", "requires_approval", "unknown_code"}


async def run(params: dict, log_id: int, db: Session) -> dict:
    """
    params:
        limit       — عدد أقصى للطلاب في التشغيل الواحد (افتراضي 50؛ None أو "all" = الكل).
        program_id  — معرّف البرنامج (افتراضي 523).
        level_id    — معرّف المستوى (افتراضي 1744).
        dry_run     — True: يجمع المؤهّلين ويُبلغ بلا استدعاء API (افتراضي False).
    """
    program_id = int(params.get("program_id", PROGRAM_ID))
    level_id = int(params.get("level_id", LEVEL_ID))
    dry_run = bool(params.get("dry_run", False))
    institution_id = cfg.INSTITUTION_ID

    raw_limit = params.get("limit", 50)
    if raw_limit in (None, "all", "ALL"):
        limit = None
    else:
        limit = int(raw_limit)

    sb = get_supabase()
    eligible = collect_eligible(sb)
    target = eligible if limit is None else eligible[:limit]

    logger.info(
        f"add_students: مؤهّلون={len(eligible)} | سنعالج={len(target)} | "
        f"المنشأة={institution_id} | dry_run={dry_run}"
    )

    result = {
        "eligible": len(eligible),
        "attempted": len(target),
        "dry_run": dry_run,
        "created": 0, "re_registered": 0, "already_active": 0,
        "requires_approval": 0, "unknown_code": 0,
        "failed": 0, "check_error": 0,
        "enjazi_ids_written": 0,
        "attention": [],
        "details": [],
    }

    if not target:
        return result

    if dry_run:
        for e in target:
            result["details"].append({
                "username": e["username"], "name": e["name"],
                "halqa_code": e["halqa_code"], "episode_id": e["episode_id"],
                "status": "dry_run",
            })
        return result

    with EnjaziClient() as client:
        get_valid_token(client)
        api = StudentsAPI(client)

        for e in target:
            rec = process_one(api, e, institution_id, program_id, level_id)

            # كتابة enjazi_id عائدًا لكل حالة توفّر معرّفًا (نجاح أو حساب قائم مرتبط)
            if rec.get("enjazi_id"):
                if _writeback(sb, rec["username"], rec["enjazi_id"]):
                    result["enjazi_ids_written"] += 1

            status = rec["status"]
            result[status] = result.get(status, 0) + 1
            result["details"].append(rec)
            if status in _ATTENTION_STATUSES:
                result["attention"].append(rec)

            logger.info(f"[{e['name']} / {e['username']}] → {status}"
                        + (f" (enjazi_id={rec['enjazi_id']})" if rec.get("enjazi_id") else "")
                        + (f" — {rec['error']}" if rec.get("error") else ""))

    logger.info(
        f"add_students: تم={result['created']} أُعيد={result['re_registered']} "
        f"نشط={result['already_active']} موافقة={result['requires_approval']} "
        f"فشل={result['failed']} كتابة enjazi_id={result['enjazi_ids_written']}"
    )
    return result
