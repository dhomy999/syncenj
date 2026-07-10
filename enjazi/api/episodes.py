"""
Episodes (Halaqat) API — institution scope.
GET /institution_panel/episodes — حلقات المنشأة
"""
from __future__ import annotations

import config.settings as cfg
from enjazi.api.base import BaseAPI
from enjazi.utils.logger import logger


class EpisodesAPI(BaseAPI):

    def list_by_institution(self, institution_id: str, institution_name: str = "", limit: int = 1000) -> list[dict]:
        """
        GET /institution_panel/episodes
        سجلات الحلقات الكاملة لمنشأة واحدة (تشمل teacher_name و category و days).
        يُحقن institution_id و institution_name في كل سجل.
        """
        logger.info(f"جلب حلقات المنشأة {institution_id}")
        resp = self._get(
            "/institution_panel/episodes",
            params={"limit": limit, "page": 1},
            headers=cfg.institution_headers(institution_id),
        )
        episodes = self._extract_list(resp.get("data", {}), key="items")
        for ep in episodes:
            ep["institution_id"]   = institution_id
            ep["institution_name"] = institution_name
        return episodes

    def list_all(self, institutions: list[dict] | None = None) -> list[dict]:
        """
        نطاق المنشأة: يجلب حلقات المنشأة المُهيّأة (عنصر واحد في القائمة).
        يحافظ على توقيع list_all ليتوافق مع بقية الوحدات والمهام.
        """
        from enjazi.api.institutions import InstitutionsAPI

        if institutions is None:
            institutions = InstitutionsAPI(self.client).list_all()

        logger.info(f"جلب حلقات {len(institutions)} منشأة")
        seen: dict[int, dict] = {}
        for inst in institutions:
            inst_id   = str(inst.get("id", ""))
            inst_name = inst.get("name", "")
            if not inst_id:
                continue
            try:
                episodes = self.list_by_institution(inst_id, inst_name)
                for ep in episodes:
                    seen[ep["id"]] = ep
            except Exception as exc:
                logger.warning(f"Failed to fetch episodes for institution {inst_id}: {exc}")

        result = list(seen.values())
        logger.info(f"Total unique episodes: {len(result)}")
        return result
