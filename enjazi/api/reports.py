"""
Reports API
GET /institution_panel/reports/students/{student_id} — student performance report
"""
from __future__ import annotations

import config.settings as cfg
from enjazi.api.base import BaseAPI
from enjazi.utils.logger import logger


class ReportsAPI(BaseAPI):

    def get_student_report(
        self,
        student_id: int,
        episode_id: int,
        institution_id: str,
        period_range: str = "W",
        date_of: str = "",
    ) -> dict:
        """
        GET /institution_panel/reports/students/{student_id}

        Args:
            student_id:     رقم الطالب في إنجازي
            episode_id:     رقم الحلقة
            institution_id: رقم المنشأة (x-behalf-id)
            period_range:   "W" أسبوعي | "D" يومي
            date_of:        "YYYY/MM/DD-YYYY/MM/DD"
        """
        logger.info(f"Fetching report for student {student_id} (episode={episode_id}, range={period_range})")
        resp = self._get(
            f"/institution_panel/reports/students/{student_id}",
            params={
                "episode_id": episode_id,
                "period_range": period_range,
                "date_of": date_of,
                "student_id": student_id,
            },
            headers=cfg.institution_headers(institution_id),
        )
        return resp.get("data", {}) if isinstance(resp, dict) else {}
