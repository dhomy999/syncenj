"""
POST /api/import/csv          — استيراد من ملف CSV
POST /api/import/batch        — استيراد من JSON (بدون streaming)
POST /api/import/batch/stream — استيراد مع SSE (نتائج حية)
"""
import asyncio
import csv
import io
import json
from threading import Thread
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI, NewStudent
from enjazi.utils.logger import logger

router = APIRouter()


# ─── Shared helpers ───────────────────────────────────────────────────────────

def _is_existing_student_error(err: str) -> bool:
    return "مسجل" in err or "exists" in err.lower() or "422" in err

def _add_existing_student(api: StudentsAPI, student: NewStudent, institution_id: str) -> tuple[str, str]:
    """
    Two-step flow للطالب المسجل مسبقاً:
      1. check-username → get user.id
      2. /students/{id}/add
    Returns (status, error_message).
    """
    try:
        check   = api.check_username(student.username, institution_id)
        user_id = check.get("data", {}).get("user", {}).get("id")
        if not user_id:
            return "skipped", "طالب مسجل — لم يُعثر على ID في النظام"
        api.add_existing(user_id, student, institution_id)
        return "requested", "طلب إضافة مُرسَل، بانتظار موافقة الطالب"
    except Exception as exc2:
        return "failed", str(exc2)


# ─── Shared import logic ──────────────────────────────────────────────────────

def _run_import(
    students: list[NewStudent],
    institution_id: str,
) -> dict:
    results: list[dict] = []
    with EnjaziClient() as client:
        get_valid_token(client)
        api = StudentsAPI(client)
        total = len(students)
        for idx, student in enumerate(students, 1):
            logger.info(f"[{idx}/{total}] إضافة: {student.name} ({student.username})")
            try:
                api.add(student, institution_id=institution_id)
                results.append({"username": student.username, "name": student.name,
                                 "status": "success", "error": None})
            except Exception as exc:
                err = str(exc)
                if _is_existing_student_error(err):
                    status, error = _add_existing_student(api, student, institution_id)
                else:
                    status, error = "failed", err
                    logger.error(f"فشل إضافة {student.username}: {err}")
                results.append({"username": student.username, "name": student.name,
                                 "status": status, "error": error})
    return {
        "total":     len(results),
        "success":   sum(1 for r in results if r["status"] == "success"),
        "requested": sum(1 for r in results if r["status"] == "requested"),
        "skipped":   sum(1 for r in results if r["status"] == "skipped"),
        "failed":    sum(1 for r in results if r["status"] == "failed"),
        "results":   results,
    }


# ─── Batch JSON endpoint (editable table) ────────────────────────────────────

class StudentRow(BaseModel):
    username:        str
    name:            str
    date_of_birth:   str
    gender_id:       int = 1
    phone:           Optional[str] = ""
    guardian_phone:  Optional[str] = ""
    email:           Optional[str] = ""

class BatchImportRequest(BaseModel):
    institution_id: str
    episode_id:     int
    program:        int = 523
    level_id:       int = 1745
    students:       list[StudentRow]

@router.post("/batch")
async def import_batch(payload: BatchImportRequest):
    """استيراد طلاب من الجدول التفاعلي (JSON)."""
    if not payload.students:
        raise HTTPException(status_code=400, detail="لا توجد بيانات للاستيراد")

    parse_errors: list[dict] = []
    students: list[NewStudent] = []

    for i, row in enumerate(payload.students, start=1):
        try:
            if not row.username.strip() or not row.name.strip() or not row.date_of_birth.strip():
                raise ValueError("username أو name أو date_of_birth فارغ")
            students.append(NewStudent(
                username=       row.username.strip(),
                name=           row.name.strip(),
                date_of_birth=  row.date_of_birth.strip(),
                gender_id=      row.gender_id,
                episode_id=     payload.episode_id,
                program=        payload.program,
                level_id=       payload.level_id,
                phone=          (row.phone or "").strip(),
                guardian_phone= (row.guardian_phone or "").strip(),
                email=          (row.email or "").strip(),
            ))
        except Exception as exc:
            parse_errors.append({"row": i, "error": str(exc)})

    result = _run_import(students, payload.institution_id)
    result["parse_errors"] = parse_errors
    return result


# ─── Streaming endpoint (SSE — نتائج حية) ────────────────────────────────────

@router.post("/batch/stream")
async def import_batch_stream(payload: BatchImportRequest):
    """يرسل نتيجة كل طالب فوراً عبر SSE."""
    if not payload.students:
        raise HTTPException(status_code=400, detail="لا توجد بيانات للاستيراد")

    parse_errors: list[dict] = []
    students: list[NewStudent] = []

    for i, row in enumerate(payload.students, start=1):
        try:
            if not row.username.strip() or not row.name.strip() or not row.date_of_birth.strip():
                raise ValueError("username أو name أو date_of_birth فارغ")
            students.append(NewStudent(
                username=       row.username.strip(),
                name=           row.name.strip(),
                date_of_birth=  row.date_of_birth.strip(),
                gender_id=      row.gender_id,
                episode_id=     payload.episode_id,
                program=        payload.program,
                level_id=       payload.level_id,
                phone=          (row.phone or "").strip(),
                guardian_phone= (row.guardian_phone or "").strip(),
                email=          (row.email or "").strip(),
            ))
        except Exception as exc:
            parse_errors.append({"row": i, "error": str(exc)})

    total = len(students)
    loop  = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def _worker():
        try:
            with EnjaziClient() as client:
                get_valid_token(client)
                api = StudentsAPI(client)
                for idx, student in enumerate(students, 1):
                    logger.info(f"[{idx}/{total}] {student.name} ({student.username})")
                    try:
                        api.add(student, institution_id=payload.institution_id)
                        event = {"type": "result", "idx": idx, "total": total,
                                 "username": student.username, "name": student.name,
                                 "status": "success", "error": None}
                    except Exception as exc:
                        err = str(exc)
                        if _is_existing_student_error(err):
                            status, error = _add_existing_student(api, student, payload.institution_id)
                        else:
                            status, error = "failed", err
                            logger.error(f"فشل {student.username}: {err}")
                        event = {"type": "result", "idx": idx, "total": total,
                                 "username": student.username, "name": student.name,
                                 "status": status, "error": error}
                    asyncio.run_coroutine_threadsafe(queue.put(event), loop)
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(None), loop)  # sentinel

    Thread(target=_worker, daemon=True).start()

    async def generate():
        yield f"data: {json.dumps({'type': 'start', 'total': total, 'parse_errors': parse_errors}, ensure_ascii=False)}\n\n"
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── CSV file endpoint (kept for compatibility) ───────────────────────────────

@router.post("/csv")
async def import_from_csv(
    institution_id: str = Form(...),
    episode_id: int = Form(...),
    program: int = Form(523),
    level_id: int = Form(1745),
    file: UploadFile = File(...),
):
    """
    يقبل ملف CSV بأعمدة: username, name, date_of_birth, gender_id
    ويضيف كل طالب إلى المنشأة والحلقة المحددة.
    """
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")  # يدعم BOM
    except UnicodeDecodeError:
        text = raw.decode("cp1256")     # fallback للـ Windows Arabic

    reader = csv.DictReader(io.StringIO(text))

    students: list[NewStudent] = []
    parse_errors: list[dict] = []

    for i, row in enumerate(reader, start=2):  # i = رقم السطر في الملف
        try:
            username = (row.get("username") or "").strip()
            name     = (row.get("name") or "").strip()
            dob      = (row.get("date_of_birth") or "").strip()
            if not username or not name or not dob:
                raise ValueError("username أو name أو date_of_birth فارغ")

            gender_raw = (row.get("gender_id") or "1").strip()
            gender_id  = 1 if gender_raw in ("1", "ذكر", "M", "m", "male") else 2

            students.append(NewStudent(
                username=username,
                name=name,
                date_of_birth=dob,
                gender_id=gender_id,
                episode_id=episode_id,
                program=program,
                level_id=level_id,
                phone=          (row.get("phone")           or "").strip(),
                guardian_phone= (row.get("guardian_phone")  or "").strip(),
                email=          (row.get("email")           or "").strip(),
            ))
        except Exception as exc:
            parse_errors.append({"row": i, "error": str(exc), "data": dict(row)})

    if not students and not parse_errors:
        raise HTTPException(status_code=400, detail="الملف فارغ أو لا يحتوي على صفوف بيانات")

    result = _run_import(students, institution_id)
    result["parse_errors"] = parse_errors
    return result
