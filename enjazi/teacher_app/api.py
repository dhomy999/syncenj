"""
TeacherAPI — نقاط تطبيق المعلم المستخدمة لفتح الحلقات (العملية 2).

المرجع: ATTENDANCE_FLOW.md و INJAAZY_AUTOMATION_GUIDE.md.
    GET  teacher/episodes-listing/active                 → data.items[] (الحلقات النشطة)
    GET  teacher/episode/students   (x-episode-id)        → data{attended_today,is_work_today,items[]}
    POST teacher/episode/attendece  (x-episode-id)        → اعتماد التحضير

⚠️ إرسال طالب واحد كـ attend يجعل الخادم يُغيّب بقية طلاب الحلقة تلقائيًا (اعتماد الجلسة كاملة).
   هذا مقبول في تصميمنا لأن الهدف فتح الحلقة فقط، والعملية 3 تحوّل من سمّع فعلًا إلى حاضر.
"""
from __future__ import annotations

from enjazi.teacher_app.client import TeacherAppClient
from enjazi.utils.logger import logger

# حجم الصفحة المطلوب من إنجازي. الـ API يرجّع افتراضيًا 15 حلقة فقط،
# فنمرّ على كل الصفحات لجلب جميع الحلقات النشطة (قد تتجاوز 39).
_PAGE_SIZE = 100
_MAX_PAGES = 50  # حماية ضد حلقة لا نهائية لو تجاهل الخادم معاملات الترقيم


class TeacherAPI:
    def __init__(self, client: TeacherAppClient):
        self.client = client

    def list_active_episodes(self) -> list[dict]:
        """الحلقات النشطة للحساب (قد تشمل عدة معلّمين لو الحساب إشرافي).

        يمرّ على كل الصفحات: الـ API يرجّع 15 حلقة فقط في الصفحة الواحدة افتراضيًا.
        متين تجاه اختلاف اسم معامل الترقيم (يمرّر page/per_page/limit معًا) وتجاهله
        (يتوقف عند صفحة فارغة أو صفحة بلا عناصر جديدة أو بلوغ الحد الأقصى للصفحات).
        """
        all_items: list[dict] = []
        seen_ids: set = set()

        for page in range(1, _MAX_PAGES + 1):
            resp = self.client.get(
                "teacher/episodes-listing/active",
                params={"page": page, "per_page": _PAGE_SIZE, "limit": _PAGE_SIZE},
            )
            data = resp.get("data", {}) if isinstance(resp, dict) else {}
            items = data.get("items", [])
            if not isinstance(items, list) or not items:
                break

            new_items = [it for it in items if it.get("id") not in seen_ids]
            if not new_items:
                # الخادم أعاد نفس الصفحة (تجاهل معامل الترقيم) → توقّف
                break

            for it in new_items:
                seen_ids.add(it.get("id"))
            all_items.extend(new_items)

            # الصفحة غير مكتملة → لا مزيد من الصفحات
            if len(items) < _PAGE_SIZE:
                break

        logger.info(f"list_active_episodes: إجمالي الحلقات النشطة المجلوبة={len(all_items)}")
        return all_items

    def get_episode_students(self, episode_id: int) -> dict:
        """طلاب الحلقة + حالة التحضير. يُرجع data (attended_today, is_work_today, items, ...)."""
        resp = self.client.get("teacher/episode/students", episode_id=episode_id)
        return resp.get("data", {}) if isinstance(resp, dict) else {}

    def submit_attendance(self, episode_id: int, students: list[dict]) -> dict:
        """POST teacher/episode/attendece — اعتماد تحضير الحلقة.

        students: [{"student_id": int, "attend_type": "attend"|"late"|"excused"|"absent"}]
        """
        return self.client.post(
            "teacher/episode/attendece",
            json={"students": students},
            episode_id=episode_id,
        )
