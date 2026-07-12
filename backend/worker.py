"""
العامل الدائم: يسحب صفوف التسميع المعلّقة من Supabase ويزامنها مع إنجازي — بلا cron.

يبدأ مع الـ backend (lifespan) ويظلّ يدور: دفعة → نوم قصير → دفعة. أي صف جديد يُضاف في
Supabase يُلتقط خلال ثوانٍ. إن لم يوجد معلّق، ينام فترة أطول (idle) بلا أي طلب لإنجازي.

الإيقاف: RECITE_WORKER_ENABLED=false في .env.
"""
from __future__ import annotations

import asyncio

from backend.services.recite_sync import process_pending
from enjazi.utils.logger import logger
import config.settings as cfg

_task: asyncio.Task | None = None

# حالة مباشرة تعرضها صفحة الإحصائيات (آخر دورة).
state: dict = {
    "running": False,
    "cycles": 0,
    "last_cycle_at": None,
    "last_result": None,
    "last_error": None,
}


async def _loop() -> None:
    logger.info(
        f"recite_worker: بدأ (كل {cfg.RECITE_WORKER_INTERVAL}s عند وجود معلّق، "
        f"و{cfg.RECITE_WORKER_IDLE_INTERVAL}s عند الفراغ، دفعة={cfg.RECITE_WORKER_BATCH})"
    )
    while True:
        try:
            # process_pending تعمل بـ requests (حاجزة) — تُنفَّذ في خيط حتى لا توقف الخادم.
            result = await asyncio.to_thread(process_pending, cfg.RECITE_WORKER_BATCH, False)
            state["cycles"] += 1
            state["last_cycle_at"] = asyncio.get_running_loop().time()
            state["last_result"] = result
            state["last_error"] = None
            idle = result["picked"] == 0
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            state["last_error"] = f"{type(exc).__name__}: {exc}"
            logger.error(f"recite_worker: دورة فاشلة — {exc}")
            idle = True

        await asyncio.sleep(
            cfg.RECITE_WORKER_IDLE_INTERVAL if idle else cfg.RECITE_WORKER_INTERVAL
        )


def start() -> None:
    global _task
    if not cfg.RECITE_WORKER_ENABLED:
        logger.info("recite_worker: معطَّل (RECITE_WORKER_ENABLED=false)")
        return
    if _task and not _task.done():
        return
    _task = asyncio.create_task(_loop())
    state["running"] = True


async def stop() -> None:
    global _task
    state["running"] = False
    if _task and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    _task = None
