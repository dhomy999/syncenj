from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any
from datetime import datetime

from backend.database import get_db
from backend.models.job import Job
from backend.scheduler import add_or_update_job, remove_job, execute_job

router = APIRouter()


# --- Schemas ---

class JobCreate(BaseModel):
    name: str
    type: str
    cron_expression: str | None = None
    params: dict[str, Any] | None = None
    description: str | None = None
    is_active: bool = True


class JobUpdate(BaseModel):
    name: str | None = None
    cron_expression: str | None = None
    params: dict[str, Any] | None = None
    description: str | None = None
    is_active: bool | None = None


class JobOut(BaseModel):
    id: int
    name: str
    type: str
    cron_expression: str | None
    params: dict | None
    description: str | None
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Endpoints ---

@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    """جميع المهام المجدولة."""
    return db.query(Job).order_by(Job.created_at.desc()).all()


@router.post("", response_model=JobOut, status_code=201)
def create_job(body: JobCreate, db: Session = Depends(get_db)):
    """إنشاء مهمة جديدة."""
    VALID_TYPES = {
        "sync_episodes",
        "export_students",
        "sync_students",
        "register_students",
        "sync_register_students",
        "sync_recitation",
        "add_students",
        "open_episodes",
        "sync_attend100",
    }
    if body.type not in VALID_TYPES:
        raise HTTPException(400, f"نوع غير صالح. الأنواع المتاحة: {VALID_TYPES}")

    job = Job(**body.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    add_or_update_job(job)
    return job


@router.patch("/{job_id}", response_model=JobOut)
def update_job(job_id: int, body: JobUpdate, db: Session = Depends(get_db)):
    """تعديل مهمة (تفعيل/إيقاف/تغيير جدول)."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "المهمة غير موجودة")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    add_or_update_job(job)
    return job


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """حذف مهمة."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "المهمة غير موجودة")
    remove_job(job_id)
    db.delete(job)
    db.commit()


@router.post("/{job_id}/run", status_code=202)
async def run_job_now(job_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """تشغيل مهمة يدوياً فوراً."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "المهمة غير موجودة")

    background_tasks.add_task(execute_job, job_id, "manual")
    return {"message": f"تم إطلاق المهمة [{job.name}]", "job_id": job_id}
