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


class TeacherAPI:
    def __init__(self, client: TeacherAppClient):
        self.client = client

    def list_active_episodes(self) -> list[dict]:
        """الحلقات النشطة للحساب (قد تشمل عدة معلّمين لو الحساب إشرافي)."""
        resp = self.client.get("teacher/episodes-listing/active")
        data = resp.get("data", {}) if isinstance(resp, dict) else {}
        items = data.get("items", [])
        return items if isinstance(items, list) else []

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
