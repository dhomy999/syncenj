"""
مهمة: مزامنة بيانات الحلقات من إنجازي
نطاق المنشأة: تجلب حلقات المنشأة المُهيّأة الواحدة وتحفظ النتيجة في سجل المهمة.
"""
import config.settings as cfg
from sqlalchemy.orm import Session

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.episodes import EpisodesAPI
from enjazi.utils.logger import logger


async def run(params: dict, log_id: int, db: Session) -> dict:
    with EnjaziClient() as client:
        get_valid_token(client)
        api = EpisodesAPI(client)
        episodes = api.list_all()  # نطاق المنشأة: حلقات المنشأة الواحدة

    scope = f"institution:{cfg.INSTITUTION_ID}"
    logger.info(f"sync_episodes: جُلب {len(episodes)} حلقة (scope={scope})")

    return {
        "total": len(episodes),
        "scope": scope,
        "sample": [{"id": e.get("id"), "name": e.get("name")} for e in episodes[:5]],
    }
