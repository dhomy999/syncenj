"""
Institutions API — institution scope (single configured institution).

الحساب يعمل على مستوى المنشأة (role=7) ويدير منشأة واحدة مُهيّأة عبر
ENJAZI_INSTITUTION_ID. لا يوجد وصول لقوائم الجمعية/الفرع.

Endpoints:
  GET /institution_panel/settings/general_settings — إعدادات المنشأة (وأسماء الجمعية/الفرع)
"""
from __future__ import annotations

import config.settings as cfg
from enjazi.api.base import BaseAPI
from enjazi.utils.logger import logger


class InstitutionsAPI(BaseAPI):

    def settings(self, institution_id: str | None = None) -> dict:
        """
        GET /institution_panel/settings/general_settings
        إعدادات المنشأة العامة (تشمل institution_name و center_name و corporation_name).
        """
        resp = self._get(
            "/institution_panel/settings/general_settings",
            headers=cfg.institution_headers(institution_id),
        )
        return resp.get("data", {}) if isinstance(resp, dict) else {}

    def get_current(self) -> dict:
        """
        تُرجع المنشأة المُهيّأة الواحدة كـ:
            {id, name, center_name, corporation_name}
        تُجلب الأسماء من endpoint الإعدادات.
        """
        iid = cfg.INSTITUTION_ID
        try:
            iid_int = int(iid)
        except (TypeError, ValueError):
            iid_int = iid

        name = f"منشأة {iid}"
        center_name = ""
        corporation_name = ""
        try:
            data = self.settings(iid)
            inst = data.get("institution", {}) if isinstance(data, dict) else {}
            if isinstance(inst, dict):
                name = inst.get("institution_name") or name
                center_name = inst.get("center_name", "") or ""
                corporation_name = inst.get("corporation_name", "") or ""
        except Exception as exc:
            logger.warning(f"تعذّر جلب إعدادات المنشأة {iid}: {exc}")

        return {
            "id": iid_int,
            "name": name,
            "center_name": center_name,
            "corporation_name": corporation_name,
        }

    def list_all(self, limit: int = 1000) -> list[dict]:
        """
        نطاق المنشأة: تُرجع قائمة بعنصر واحد هو المنشأة المُهيّأة.
        يحافظ هذا على توافق مواقع الاستدعاء التي تمرّ على المنشآت (fan-out)
        فتعمل على منشأة واحدة بدل كل منشآت الجمعية.
        """
        logger.info(f"نطاق المنشأة: إرجاع المنشأة الحالية ({cfg.INSTITUTION_ID})")
        return [self.get_current()]

    def get_list(self) -> list[dict]:
        """قائمة مختصرة للقوائم المنسدلة — نفس المنشأة الواحدة."""
        cur = self.get_current()
        return [{"id": cur["id"], "name": cur["name"]}]
