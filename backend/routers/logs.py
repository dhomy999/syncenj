from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from backend.database import get_db
from backend.models.job_log import JobLog
from backend.models.student_import import StudentImport

router = APIRouter()


class LogOut(BaseModel):
    id: int
    job_id: int
    status: str
    triggered_by: str
    started_at: datetime
    finished_at: datetime | None
    result: dict | None
    error_message: str | None

    class Config:
        from_attributes = True


class StudentImportOut(BaseModel):
    id: int
    student_username: str
    student_name: str
    episode_id: str
    status: str
    error: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[LogOut])
def list_logs(
    job_id: int | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """سجل تنفيذ المهام مع إمكانية التصفية."""
    q = db.query(JobLog)
    if job_id:
        q = q.filter(JobLog.job_id == job_id)
    if status:
        q = q.filter(JobLog.status == status)
    return q.order_by(JobLog.started_at.desc()).limit(limit).all()


@router.get("/{log_id}", response_model=LogOut)
def get_log(log_id: int, db: Session = Depends(get_db)):
    """تفاصيل سجل تنفيذ واحد."""
    log = db.get(JobLog, log_id)
    if not log:
        from fastapi import HTTPException
        raise HTTPException(404, "السجل غير موجود")
    return log


@router.get("/{log_id}/students", response_model=list[StudentImportOut])
def get_log_students(log_id: int, db: Session = Depends(get_db)):
    """تفاصيل الطلاب المستوردين في سجل معين."""
    return (
        db.query(StudentImport)
        .filter(StudentImport.job_log_id == log_id)
        .order_by(StudentImport.id)
        .all()
    )
