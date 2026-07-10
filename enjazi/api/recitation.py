"""
Recitation API — institution scope.

نقطة الحفظ المكتشفة (من HAR لوحة إنجازي):
    PUT /institution_panel/students/{student_id}/change-recite

نقاط القراءة المساعدة:
    GET /institution_panel/models-filter/episode-students?episodes_ids={eid}&limit=
    GET /institution_panel/students/{sid}/profile/episodes/{eid}/plan
    GET /institution_panel/students/{sid}/get-lesson-complete?episode_id=&std_level_id=&pillar_id=&from_verse_id=&student_id=
    GET /institution_panel/students/{sid}/history-lessons?student_id=&episode_id=&date_of=

نموذج التسميع في إنجازي:
    pillar_id: 2 = الحفظ (الدرس) | 3 = المراجعة | (الجانبي = قيمة أخرى تُؤكَّد لاحقًا)
    الأخطاء: mistakes = {error, mention, tajweed} (أعداد، وليست درجة حرفية)
    المواضع: from_verse_id / to_verse_id = معرّفات الآيات في إنجازي
    std_level_id + lesson_id: معرّفات داخلية للطالب (تُجلب من plan/get-lesson-complete/history-lessons)
"""
from __future__ import annotations

import secrets

import config.settings as cfg
from enjazi.api.base import BaseAPI
from enjazi.utils.logger import logger

# أركان التسميع في إنجازي
PILLAR_LESSON = 2   # الحفظ / الدرس
PILLAR_REVIEW = 3   # المراجعة
PILLAR_SIDE = 4     # التثبيت (الجانبي) — مؤكَّد من plan الطالب (pillar_name="تثبيت", pillar_id=4)

# تحويل الدرجة النصية (Supabase) → أعداد الأخطاء في إنجازي {error, mention, tajweed}
# (تردد = mention/تلقين). "لم يسمع" = لم يُسمَّع الركن → يُتخطّى.
GRADE_TO_MISTAKES: dict[str, dict | None] = {
    "ممتاز":    {"error": 0, "mention": 0, "tajweed": 0},
    "جيد جدا":  {"error": 0, "mention": 2, "tajweed": 0},
    "جيد جدًا":  {"error": 0, "mention": 2, "tajweed": 0},
    "جيد":      {"error": 1, "mention": 2, "tajweed": 0},
    # "إعادة" = تسميع ضعيف يتطلب إعادة (أسوأ من "جيد"). القيم تقديرية — Supabase يخزّن درجة نصية
    # لا أعداد أخطاء دقيقة. تُراجَع بعد رؤية أعداد الأخطاء الفعلية لدرجة "إعادة" في لوحة إنجازي.
    "إعادة":    {"error": 3, "mention": 3, "tajweed": 0},
    "لم يسمع":   None,  # يُتخطّى هذا الركن (لم يُسمَّع)
}


def grade_to_mistakes(grade: str) -> dict | None:
    """يُرجع أعداد الأخطاء لدرجة نصية، أو None إذا كان الركن لا يُسمَّع (لم يسمع/غير معروف)."""
    return GRADE_TO_MISTAKES.get((grade or "").strip())


def make_frond_id(pillar_id: int, std_level_id: int, lesson_id: int) -> str:
    """معرّف frond_id مركّب كما تولّده اللوحة: {pillar}-{level}-{lesson}-{random}."""
    return f"{pillar_id}-{std_level_id}-{lesson_id}-{secrets.token_hex(6)}"


def build_lesson(
    *,
    lesson_id: int,
    pillar_id: int,
    std_level_id: int,
    from_verse_id: int,
    to_verse_id: int,
    error: int = 0,
    mention: int = 0,
    tajweed: int = 0,
    done: bool = True,
    action: int = 1,
    lesson_type: str = "history",
) -> dict:
    """يبني عنصر درس واحد ضمن مصفوفة lessons في طلب change-recite."""
    return {
        "action": action,
        "lesson_id": lesson_id,
        "pillar_id": pillar_id,
        "mistakes": {"error": error, "mention": mention, "tajweed": tajweed},
        "from_verse_id": from_verse_id,
        "to_verse_id": to_verse_id,
        "std_level_id": std_level_id,
        "done": done,
        "lesson_type": lesson_type,
        "frond_id": make_frond_id(pillar_id, std_level_id, lesson_id),
    }


class RecitationAPI(BaseAPI):

    def get_episode_students(
        self, episode_id: int | str, institution_id: str | None = None, limit: int = 10000
    ) -> list[dict]:
        """GET models-filter/episode-students — طلاب حلقة (episode) في إنجازي."""
        resp = self._get(
            "/institution_panel/models-filter/episode-students",
            params={"episodes_ids": episode_id, "limit": limit},
            headers=cfg.institution_headers(institution_id),
        )
        return self._extract_list(resp.get("data", {}) if isinstance(resp, dict) else {}, key="items") \
            or self._extract_list(resp, key="data")

    def get_plan(
        self, student_id: int, episode_id: int, institution_id: str | None = None
    ) -> dict:
        """GET students/{sid}/profile/episodes/{eid}/plan — خطة الطالب (تشمل std_level_id والمواضع)."""
        resp = self._get(
            f"/institution_panel/students/{student_id}/profile/episodes/{episode_id}/plan",
            headers=cfg.institution_headers(institution_id),
        )
        return resp.get("data", {}) if isinstance(resp, dict) else {}

    def get_lesson_complete(
        self,
        student_id: int,
        episode_id: int,
        std_level_id: int,
        pillar_id: int,
        from_verse_id: int,
        institution_id: str | None = None,
    ) -> dict:
        """GET get-lesson-complete — يحسب الدرس الكامل (lesson_id, to_verse_id) من آية البداية."""
        resp = self._get(
            f"/institution_panel/students/{student_id}/get-lesson-complete",
            params={
                "episode_id": episode_id,
                "std_level_id": std_level_id,
                "pillar_id": pillar_id,
                "from_verse_id": from_verse_id,
                "student_id": student_id,
            },
            headers=cfg.institution_headers(institution_id),
        )
        return resp.get("data", {}) if isinstance(resp, dict) else {}

    def get_history_lessons(
        self, student_id: int, episode_id: int, date_of: str, institution_id: str | None = None
    ) -> dict:
        """GET history-lessons — دروس الطالب المسجّلة ليوم (تشمل lesson_id لكل ركن)."""
        resp = self._get(
            f"/institution_panel/students/{student_id}/history-lessons",
            params={"student_id": student_id, "episode_id": episode_id, "date_of": date_of},
            headers=cfg.institution_headers(institution_id),
        )
        return resp.get("data", {}) if isinstance(resp, dict) else {}

    def change_recite(
        self,
        student_id: int,
        episode_id: int,
        date_of: str,
        lessons: list[dict],
        attend_type: str = "attend",
        institution_id: str | None = None,
    ) -> dict:
        """
        PUT change-recite — حفظ/تعديل تسميع الطالب ليوم معيّن.

        Args:
            student_id:  رقم الطالب في إنجازي
            episode_id:  رقم الحلقة في إنجازي
            date_of:     "YYYY-MM-DD"
            lessons:     قائمة دروس (استخدم build_lesson لبنائها)
            attend_type: "attend" (حاضر) وغيرها حسب اللوحة
        """
        body = {
            "episode_id": episode_id,
            "student_id": student_id,
            "attend_type": attend_type,
            "date_of": date_of,
            "lessons": lessons,
        }
        logger.info(f"change-recite: student={student_id} episode={episode_id} date={date_of} lessons={len(lessons)}")
        return self._put(
            f"/institution_panel/students/{student_id}/change-recite",
            json=body,
            headers=cfg.institution_headers(institution_id),
        )
