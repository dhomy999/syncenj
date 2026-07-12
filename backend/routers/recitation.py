"""
Recitation Sync API — إحصائيات دقيقة لما زُومن وما بقي، وتحكّم يدوي بالعامل.

GET  /api/recitation/stats        — عدّادات الحالات + حالة العامل + آخر دورة
GET  /api/recitation/rows         — صفوف بحالة معيّنة (pending/failed/skipped/synced)
POST /api/recitation/retry        — إعادة الصفوف الفاشلة إلى pending (تصفير المحاولات)
POST /api/recitation/run          — تشغيل دفعة الآن بلا انتظار العامل
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend import worker
from backend.services import recite_sync
from backend.supabase_client import get_supabase
import config.settings as cfg

router = APIRouter()

_STATUSES = ("pending", "synced", "skipped", "failed")


class RetryBody(BaseModel):
    row_ids: list[str] | None = None      # None = كل الفاشلة


@router.get("/stats")
def stats():
    counts = recite_sync.stats()
    return {
        "counts": counts,
        "worker": {
            "enabled": cfg.RECITE_WORKER_ENABLED,
            "running": worker.state["running"],
            "cycles": worker.state["cycles"],
            "last_result": worker.state["last_result"],
            "last_error": worker.state["last_error"],
            "batch": cfg.RECITE_WORKER_BATCH,
            "interval": cfg.RECITE_WORKER_INTERVAL,
        },
        "max_attempts": recite_sync.MAX_ATTEMPTS,
    }


@router.get("/rows")
def rows(
    status: str = Query("failed", description="pending | synced | skipped | failed"),
    limit: int = Query(100, le=1000),
):
    if status not in _STATUSES:
        status = "failed"
    sb = get_supabase()
    data = (
        sb.table("quran_recitation")
        .select(
            "id,recite_date,sync_status,sync_attempts,sync_error,synced_at,"
            "students(student_name,enjazi_id),halaqat(halqa_code)"
        )
        .eq("sync_status", status)
        .order("recite_date", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    out = []
    for r in data:
        stu = r.get("students") or {}
        hal = r.get("halaqat") or {}
        out.append({
            "id": r["id"],
            "recite_date": r.get("recite_date"),
            "student_name": stu.get("student_name"),
            "enjazi_id": stu.get("enjazi_id"),
            "halqa_code": hal.get("halqa_code"),
            "sync_status": r.get("sync_status"),
            "sync_attempts": r.get("sync_attempts"),
            "sync_error": r.get("sync_error"),
            "synced_at": r.get("synced_at"),
        })
    return {"data": out, "total": len(out)}


@router.post("/retry")
def retry(body: RetryBody):
    """يعيد الصفوف الفاشلة إلى قائمة الانتظار (العامل سيلتقطها في دورته التالية)."""
    sb = get_supabase()
    payload = {"sync_status": "pending", "sync_attempts": 0, "sync_error": None}
    q = sb.table("quran_recitation").update(payload)
    q = q.in_("id", body.row_ids) if body.row_ids else q.eq("sync_status", "failed")
    res = q.execute()
    return {"ok": True, "requeued": len(res.data or [])}


@router.post("/run")
async def run_now(limit: int = Query(25, le=200), dry_run: bool = Query(False)):
    """دفعة فورية (نفس منطق العامل) — مفيدة للاختبار أو لدفع المتراكم."""
    return await asyncio.to_thread(recite_sync.process_pending, limit, dry_run)
