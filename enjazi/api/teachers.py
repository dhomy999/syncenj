"""
Teachers API — institution scope.
GET /institution_panel/teachers
GET /institution_panel/supervisors/list
"""
from __future__ import annotations

import config.settings as cfg
from enjazi.api.base import BaseAPI
from enjazi.utils.logger import logger


class TeachersAPI(BaseAPI):

    def list_by_institution(self, institution_id: str | None = None, limit: int = 1000) -> list[dict]:
        """
        GET /institution_panel/teachers
        جميع معلمي المنشأة.
        الرد: { data: { items, all_teachers, active_teachers, inactive_teachers, paginate } }
        """
        iid = institution_id or cfg.INSTITUTION_ID
        logger.info(f"جلب معلمي المنشأة {iid} (limit={limit})")
        resp = self._get(
            "/institution_panel/teachers",
            params={"limit": limit, "page": 1},
            headers=cfg.institution_headers(iid),
        )
        return self._extract_list(resp.get("data", {}), key="items")

    def list_all(self, limit: int = 1000) -> list[dict]:
        """
        نطاق المنشأة: معلمو المنشأة المُهيّأة الواحدة.
        (يحافظ على نفس توقيع list_all ليتوافق مع باقي الوحدات.)
        """
        return self.list_by_institution(limit=limit)

    def supervisors_by_institution(self, institution_id: str | None = None, limit: int = 1000) -> list[dict]:
        """
        GET /institution_panel/supervisors/list
        مشرفو المنشأة.
        """
        iid = institution_id or cfg.INSTITUTION_ID
        logger.info(f"جلب مشرفي المنشأة {iid}")
        resp = self._get(
            "/institution_panel/supervisors/list",
            params={"limit": limit, "refresh": "true"},
            headers=cfg.institution_headers(iid),
        )
        return self._extract_list(resp.get("data", {}), key="list")
