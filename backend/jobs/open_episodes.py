"""
مهمة: فتح الحلقات من جهة المعلم (العملية 2 — الساعة 4 صباحًا، السبت–الخميس عدا الجمعة).

الهدف: «فتح» كل حلقة نشطة لليوم بتحضير طالب واحد فيها من حساب المعلم الإشرافي
(تطبيق المعلم apps/v1)، حتى تصبح الحلقة قابلة لتسجيل التسميع/الحضور لبقية اليوم.

⚠️ الأثر الجانبي المؤكَّد: تحضير طالب واحد يُغيّب بقية الحلقة تلقائيًا. مقبول هنا لأن
   العملية 3 (كل ساعة) تحوّل من له سجل تسميع اليوم في Supabase إلى «حاضر» في إنجازي.

السلامة:
    - يفلتر بالمنشأة (institution_id) — الحساب الإشرافي قد يرى حلقات منشآت أخرى.
    - يتخطّى الحلقات المفتوحة مسبقًا (attended_today) — قابلة لإعادة التشغيل بأمان.
    - يتخطّى غير أيام العمل (is_work_today).
    - dry_run افتراضيًا True: يطبع ما سيُرسَل بلا إرسال فعلي.
    - episode_ids (اختياري): قائمة بيضاء لتقييد التشغيل الأول على حلقات محددة.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from enjazi.teacher_app.client import TeacherAppClient
from enjazi.teacher_app.api import TeacherAPI
from enjazi.utils.logger import logger
import config.settings as cfg


async def run(params: dict, log_id: int, db: Session) -> dict:
    """
    params:
        dry_run        — True (افتراضي): محاكاة بلا إرسال.
        institution_id — فلتر المنشأة (افتراضي INSTITUTION_ID من الإعدادات).
        episode_ids    — قائمة بيضاء اختيارية بأرقام حلقات إنجازي.
        attend_type    — نوع تحضير الطالب المفتوح به (افتراضي "attend").
    """
    dry_run = bool(params.get("dry_run", True))
    institution_id = int(params.get("institution_id", cfg.INSTITUTION_ID))
    whitelist = params.get("episode_ids")
    whitelist_set = {int(x) for x in whitelist} if whitelist else None
    attend_type = params.get("attend_type", "attend")

    result = {
        "dry_run": dry_run,
        "institution_id": institution_id,
        "episodes_seen": 0,
        "opened": 0,
        "skipped_already_open": 0,
        "skipped_not_workday": 0,
        "skipped_empty": 0,
        "skipped_other_institution": 0,
        "skipped_not_whitelisted": 0,
        "failed": 0,
        "details": [],
    }

    with TeacherAppClient() as client:
        client.get_valid_token()
        api = TeacherAPI(client)

        episodes = api.list_active_episodes()
        result["episodes_seen"] = len(episodes)
        logger.info(f"open_episodes: حلقات نشطة={len(episodes)} | المنشأة={institution_id} | dry_run={dry_run}")

        for ep in episodes:
            eid = ep.get("id")
            ep_inst = (ep.get("institution") or {}).get("id")
            detail = {"eid": eid, "name": ep.get("name")}

            # فلتر المنشأة
            if ep_inst != institution_id:
                detail["action"] = "skipped_other_institution"
                result["skipped_other_institution"] += 1
                result["details"].append(detail)
                continue

            # قائمة بيضاء اختيارية
            if whitelist_set is not None and int(eid) not in whitelist_set:
                detail["action"] = "skipped_not_whitelisted"
                result["skipped_not_whitelisted"] += 1
                result["details"].append(detail)
                continue

            try:
                data = api.get_episode_students(eid)

                if not data.get("is_work_today"):
                    detail["action"] = "skipped_not_workday"
                    result["skipped_not_workday"] += 1
                    result["details"].append(detail)
                    continue

                if data.get("attended_today"):
                    detail["action"] = "skipped_already_open"
                    result["skipped_already_open"] += 1
                    result["details"].append(detail)
                    continue

                items = data.get("items") or []
                if not items:
                    detail["action"] = "skipped_empty"
                    result["skipped_empty"] += 1
                    result["details"].append(detail)
                    continue

                sid = items[0].get("id")
                detail["opened_via_student"] = sid

                if dry_run:
                    detail["action"] = "dry_run"
                    detail["payload"] = {"students": [{"student_id": sid, "attend_type": attend_type}]}
                    logger.info(f"[DRY-RUN] فتح الحلقة {eid} عبر الطالب {sid}")
                else:
                    api.submit_attendance(eid, [{"student_id": sid, "attend_type": attend_type}])
                    detail["action"] = "opened"
                    result["opened"] += 1
                    logger.info(f"فُتحت الحلقة {eid} عبر الطالب {sid} ✅")

            except Exception as exc:
                detail["action"] = "failed"
                detail["error"] = f"{type(exc).__name__}: {exc}"
                result["failed"] += 1
                logger.error(f"تعذّر فتح الحلقة {eid}: {exc}")

            result["details"].append(detail)

    logger.info(
        f"open_episodes: فُتحت={result['opened']} مفتوحة مسبقًا={result['skipped_already_open']} "
        f"غير يوم عمل={result['skipped_not_workday']} فشل={result['failed']}"
    )
    return result
