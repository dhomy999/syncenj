"""
Students API — institution scope.
GET  /institution_panel/students              — طلاب المنشأة
POST /institution_panel/students              — إضافة طالب
POST /institution_panel/students/{id}/add     — إضافة طالب مسجل مسبقاً
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

import config.settings as cfg
from enjazi.api.base import BaseAPI
from enjazi.utils.logger import logger


@dataclass
class NewStudent:
    """
    Data required to register a new student.
    All IDs must be confirmed from the episodes/institutions API first.
    """
    username: str           # رقم الهوية الوطنية
    name: str               # الاسم الكامل
    date_of_birth: str      # YYYY-MM-DD (ميلادي)
    episode_id: int         # رقم الحلقة
    program: int            # رقم البرنامج (523 = حفظ حسب خطة التسميع)
    level_id: int           # رقم المستوى (1745)
    nationality_id: int = 1             # 1=سعودي
    gender_id: int = 1                  # 1=ذكر, 2=أنثى
    phone_country_code: str = "00966"   # كما ترسله اللوحة تمامًا
    guardian_phone_country_code: str = "00966"
    phone: str = ""                     # رقم جوال الطالب (بدون رمز الدولة) → يُرسَل كـ phone_number
    guardian_phone: str = ""            # رقم جوال ولي الأمر
    email: str = ""                     # البريد الإلكتروني


class StudentsAPI(BaseAPI):

    def get_history_lessons(
        self,
        student_id: int,
        episode_id: int,
        institution_id: str,
        date_of: str,
    ) -> dict:
        """
        GET /institution_panel/students/{student_id}/history-lessons
        Returns saved & revision lessons for a specific date.

        Args:
            student_id:     رقم الطالب في إنجازي
            episode_id:     رقم الحلقة
            institution_id: رقم المنشأة (x-behalf-id)
            date_of:        "YYYY-MM-DD"
        """
        logger.info(f"Fetching history-lessons for student {student_id} on {date_of}")
        resp = self._get(
            f"/institution_panel/students/{student_id}/history-lessons",
            params={"student_id": student_id, "episode_id": episode_id, "date_of": date_of},
            headers=cfg.institution_headers(institution_id),
        )
        return resp.get("data", {}) if isinstance(resp, dict) else {}

    def list_by_institution(self, institution_id: str, limit: int = 1000) -> list[dict]:
        """
        GET /institution_panel/students
        Full student records for one institution (includes username, gender_id, episodes_list).
        """
        logger.info(f"Fetching students for institution {institution_id}")
        resp = self._get(
            "/institution_panel/students",
            params={"limit": limit, "page": 1},
            headers=cfg.institution_headers(institution_id),
        )
        return self._extract_list(resp.get("data", {}), key="items")

    def list_all(self, institutions: list[dict] | None = None, limit: int = 1000) -> list[dict]:
        """
        نطاق المنشأة: يجلب طلاب المنشأة المُهيّأة (عنصر واحد في القائمة).
        يحافظ على توقيع list_all ليتوافق مع بقية الوحدات والمهام.
        """
        from enjazi.api.institutions import InstitutionsAPI

        if institutions is None:
            institutions = InstitutionsAPI(self.client).list_all()

        logger.info(f"جلب طلاب {len(institutions)} منشأة")
        seen: dict[int, dict] = {}
        for inst in institutions:
            inst_id = str(inst.get("id", ""))
            if not inst_id:
                continue
            try:
                students = self.list_by_institution(inst_id, limit=limit)
                for s in students:
                    seen[s["id"]] = s
            except Exception as exc:
                logger.warning(f"Failed to fetch students for institution {inst_id}: {exc}")

        result = list(seen.values())
        logger.info(f"Total unique students: {len(result)}")
        return result

    def add(self, student: NewStudent, institution_id: str | None = None) -> dict:
        """
        POST /institution_panel/students
        Add a single student to an institution.
        Uses multipart/form-data as required by the API.

        Returns the created student data dict on success.
        Raises ValidationError if username already exists or data is invalid.
        """
        iid = institution_id or cfg.INSTITUTION_ID
        logger.info(f"Adding student '{student.name}' (ID: {student.username}) to institution {iid}")

        # multipart/form-data بترتيب اللوحة نفسه (مطابق لطلب add_student.md الناجح).
        # تُرسَل عبر files= كأجزاء (None, value) لإجبار curl_cffi على multipart بدل urlencoded.
        fields: dict[str, str] = {
            "username": student.username,
            "name": student.name,
            "nationality_id": str(student.nationality_id),
            "phone_number": student.phone,
            "gender_id": str(student.gender_id),
            "guardian_phone": student.guardian_phone or student.phone,
            "phone_country_code": str(student.phone_country_code),
            "guardian_phone_country_code": str(student.guardian_phone_country_code),
            "date_of_birth": student.date_of_birth,
            "program": str(student.program),
            "level_id": str(student.level_id),
            "episode_id": str(student.episode_id),
        }
        if student.email:
            fields["email"] = student.email

        # curl_cffi يتطلب CurlMime لـ multipart/form-data. القيم bytes UTF-8 حتى لا
        # تُشوَّه الأسماء العربية، وبدون filename لتكون حقول نص عادية (كما ترسله اللوحة).
        from curl_cffi import CurlMime

        mp = CurlMime()
        for key, val in fields.items():
            mp.addpart(name=key, data=str(val).encode("utf-8"))

        resp = self._post(
            "/institution_panel/students",
            multipart=mp,
            headers=cfg.institution_headers(iid),
        )

        if isinstance(resp, dict) and resp.get("success"):
            logger.success(f"Student added: {resp.get('message', 'OK')}")
            return resp.get("data", {})

        logger.warning(f"Unexpected response: {resp}")
        return resp

    # ─── التسجيل الجماعي (batch-operations) — النقطة التي تستخدمها لوحة إنجازي ───
    # مكتشفة من HAR (add.md): تسلسل sync-programs-selections → check-usernames → register-students.

    def sync_program_selection(self, item_ids: str, institution_id: str | None = None) -> dict:
        """
        POST /institution_panel/central-programs/sync-programs-selections
        تفعيل برنامج/برامج للمنشأة قبل التسجيل الجماعي (item_ids نصّ مثل "523").
        """
        return self._post(
            "/institution_panel/central-programs/sync-programs-selections",
            json={"item_ids": str(item_ids)},
            headers=cfg.institution_headers(institution_id),
        )

    def batch_check_usernames(
        self, usernames: list[str], institution_id: str | None = None, country_id: int = 1
    ) -> dict:
        """
        POST /institution_panel/settings/batch-operations/register-students/check-usernames
        يتحقق من أرقام الهوية قبل التسجيل الجماعي.
        """
        return self._post(
            "/institution_panel/settings/batch-operations/register-students/check-usernames",
            json={"usernames": usernames, "target_country_id": country_id},
            headers=cfg.institution_headers(institution_id),
        )

    def batch_register(self, students: list[dict], institution_id: str | None = None) -> dict:
        """
        POST /institution_panel/settings/batch-operations/register-students
        التسجيل الجماعي الفعلي. كل عنصر في students يجب أن يحوي:
            id (0 لجديد), name, user_is_changed, username, episode_id,
            program_id, level_id, original_username
        تُضاف ترويسة x-idempotency-key فريدة لكل طلب كما تفعل اللوحة.
        """
        headers = cfg.institution_headers(institution_id)
        headers["x-idempotency-key"] = str(uuid.uuid4())
        return self._post(
            "/institution_panel/settings/batch-operations/register-students",
            json={"students": students},
            headers=headers,
        )

    def check_username(self, username: str, institution_id: str) -> dict:
        """POST /institution_panel/add-user-requests/check-username"""
        return self._post(
            "/institution_panel/add-user-requests/check-username",
            json={"username": username, "add_as": "student"},
            headers=cfg.institution_headers(institution_id),
        )

    def add_existing(self, student_id: int, student: "NewStudent", institution_id: str) -> dict:
        """POST /institution_panel/students/{id}/add — للطالب المسجل مسبقاً."""
        logger.info(f"Adding existing student {student_id} ({student.username}) to episode {student.episode_id}")
        return self._post(
            f"/institution_panel/students/{student_id}/add",
            json={
                "id":            student_id,
                "program":       student.program,
                "level_id":      student.level_id,
                "episode_id":    student.episode_id,
                "date_of_birth": student.date_of_birth,
            },
            headers=cfg.institution_headers(institution_id),
        )

    def add_batch(
        self,
        students: list[NewStudent],
        institution_id: str | None = None,
        stop_on_error: bool = False,
    ) -> list[dict]:
        """
        Add multiple students one by one.
        Rate limiter in the client handles delays automatically.

        Returns list of results: each item is either the created student dict
        or an error dict with 'error' and 'student' keys.
        """
        results = []
        total = len(students)

        for i, student in enumerate(students, 1):
            logger.info(f"[{i}/{total}] Processing: {student.name}")
            try:
                result = self.add(student, institution_id)
                results.append({"status": "success", "data": result, "student": student.username})
            except Exception as exc:
                logger.error(f"Failed to add {student.username}: {exc}")
                results.append({"status": "error", "error": str(exc), "student": student.username})
                if stop_on_error:
                    break

        success = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - success
        logger.info(f"Batch done: {success} added, {failed} failed out of {total}")
        return results
