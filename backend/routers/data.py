from datetime import datetime
from fastapi import APIRouter, Query, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.cache import DataCache
from backend.services.student_lookup import list_all_students
from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api import InstitutionsAPI, EpisodesAPI, StudentsAPI, TeachersAPI

router = APIRouter()


# ─── students roster (for admin cards) ─────────────────────────────────────────

@router.get("/students-roster")
def get_students_roster():
    """قائمة الطلاب الذين لديهم sub_url مع الاسم ورقم الطالب — تُستخدم لبطاقات الإدارة."""
    items = list_all_students()
    return {"data": items, "total": len(items)}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _client_with_token() -> EnjaziClient:
    client = EnjaziClient()
    get_valid_token(client)
    return client


def _read_cache(db: Session, key: str) -> dict:
    """أرجع بيانات الكاش أو dict فارغ."""
    row: DataCache | None = db.get(DataCache, key)
    if row:
        return {
            "data": row.data,
            "total": len(row.data) if isinstance(row.data, list) else 0,
            "updated_at": row.updated_at.isoformat(),
        }
    return {"data": [], "total": 0, "updated_at": None}


def _write_cache(db: Session, key: str, data: list | dict) -> DataCache:
    """احفظ أو حدّث صف في الكاش."""
    row: DataCache | None = db.get(DataCache, key)
    if row:
        row.data = data
        row.updated_at = datetime.utcnow()
    else:
        row = DataCache(key=key, data=data, updated_at=datetime.utcnow())
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ─── branches ─────────────────────────────────────────────────────────────────

@router.get("/branches")
def get_branches(db: Session = Depends(get_db)):
    return _read_cache(db, "branches")


@router.post("/branches/refresh")
def refresh_branches(db: Session = Depends(get_db)):
    """نطاق المنشأة: لا توجد فروع — إرجاع قائمة فارغة."""
    row = _write_cache(db, "branches", [])
    return {"data": [], "total": 0, "updated_at": row.updated_at.isoformat()}


@router.get("/branches/list")
def get_branches_list():
    """نطاق المنشأة: لا توجد فروع."""
    return {"data": []}


# ─── facilities ───────────────────────────────────────────────────────────────

@router.get("/facilities")
def get_facilities(db: Session = Depends(get_db)):
    return _read_cache(db, "facilities")


@router.post("/facilities/refresh")
def refresh_facilities(db: Session = Depends(get_db)):
    """نطاق المنشأة: المنشأة الواحدة المُهيّأة (مع أسماء الجمعية/الفرع)."""
    with _client_with_token() as client:
        items = InstitutionsAPI(client).list_all()
    row = _write_cache(db, "facilities", items)
    return {"data": row.data, "total": len(row.data), "updated_at": row.updated_at.isoformat()}


# ─── episodes ─────────────────────────────────────────────────────────────────

@router.get("/episodes")
def get_episodes(db: Session = Depends(get_db)):
    return _read_cache(db, "episodes")


@router.post("/episodes/refresh")
def refresh_episodes(db: Session = Depends(get_db)):
    with _client_with_token() as client:
        institutions = InstitutionsAPI(client).list_all()
        items = EpisodesAPI(client).list_all(institutions=institutions)
    row = _write_cache(db, "episodes", items)
    return {"data": row.data, "total": len(row.data), "updated_at": row.updated_at.isoformat()}


# ─── students ─────────────────────────────────────────────────────────────────

@router.get("/students")
def get_students(db: Session = Depends(get_db)):
    return _read_cache(db, "students")


@router.post("/students/refresh")
def refresh_students(db: Session = Depends(get_db)):
    with _client_with_token() as client:
        institutions = InstitutionsAPI(client).list_all()
        items = StudentsAPI(client).list_all(institutions=institutions)
    row = _write_cache(db, "students", items)
    return {"data": row.data, "total": len(row.data), "updated_at": row.updated_at.isoformat()}


# ─── teachers ─────────────────────────────────────────────────────────────────

@router.get("/teachers")
def get_teachers(db: Session = Depends(get_db)):
    return _read_cache(db, "teachers")


@router.post("/teachers/refresh")
def refresh_teachers(db: Session = Depends(get_db)):
    """نطاق المنشأة: معلمو المنشأة المُهيّأة."""
    with _client_with_token() as client:
        teachers = TeachersAPI(client).list_by_institution()
    # توحيد status (bool → string) ليتوافق مع الواجهة
    items = []
    for t in teachers:
        st = t.get("status")
        t["status"] = "active" if (st is True or st == "active") else "inactive"
        items.append(t)
    row = _write_cache(db, "teachers", items)
    return {"data": row.data, "total": len(row.data), "updated_at": row.updated_at.isoformat()}
