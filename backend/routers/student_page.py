"""
Student Dashboard Page API
GET /api/student-page/{sub_url} — returns all data needed for the student dashboard
"""
from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, timedelta
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.reports import ReportsAPI
from enjazi.api.students import StudentsAPI
from enjazi.utils.logger import logger
from backend.services.student_lookup import resolve_sub_url

router = APIRouter()



def _default_date_range() -> str:
    """Returns current week range: Sunday-Saturday in YYYY/MM/DD-YYYY/MM/DD format."""
    today = date.today()
    # Find last Sunday (start of week)
    days_since_sunday = (today.weekday() + 1) % 7
    sunday = today - timedelta(days=days_since_sunday)
    saturday = sunday + timedelta(days=6)
    return f"{sunday.strftime('%Y/%m/%d')}-{saturday.strftime('%Y/%m/%d')}"


def _default_month_range() -> str:
    """Returns current month range: 1st-last day in YYYY/MM/DD-YYYY/MM/DD format."""
    today = date.today()
    first = today.replace(day=1)
    last = today.replace(day=monthrange(today.year, today.month)[1])
    return f"{first.strftime('%Y/%m/%d')}-{last.strftime('%Y/%m/%d')}"


# ── Main endpoint ────────────────────────────────────────────────────────────

@router.get("/{sub_url}")
async def get_student_page(
    sub_url: str,
    period_range: str = Query("W", pattern="^[WD]$"),
    date_of: str = Query(""),
):
    """
    Resolves sub_url → Google Sheet data + Enjazi report.
    Returns combined JSON for the student dashboard.
    """
    # 1. Resolve sub_url from Google Sheets
    lookup = resolve_sub_url(sub_url)
    if lookup is None:
        raise HTTPException(status_code=404, detail=f"sub_url '{sub_url}' not found")

    # 2. Default date range if not provided
    if not date_of:
        date_of = _default_date_range()

    # 3. Get Enjazi report + today's lessons
    report = {}
    monthly_attendance = {}
    quran_progress = {}
    today_lessons = {}
    try:
        with EnjaziClient() as client:
            get_valid_token(client)
            institution_id = str(lookup.institution_id)

            reports_api = ReportsAPI(client)
            report = reports_api.get_student_report(
                student_id=lookup.enjazi_student_id,
                episode_id=lookup.episode_id,
                institution_id=institution_id,
                period_range=period_range,
                date_of=date_of,
            )

            # Fetch monthly report for attendance only
            monthly_report = reports_api.get_student_report(
                student_id=lookup.enjazi_student_id,
                episode_id=lookup.episode_id,
                institution_id=institution_id,
                period_range="W",
                date_of=_default_month_range(),
            )
            monthly_attendance = monthly_report.get("attendece", {})

            # Calculate Quran progress from monthly pages_numbers
            pages_numbers_raw = monthly_report.get("saved_pages", {}).get("pages_numbers", "")
            nums = [int(x) for x in re.findall(r"\d+", pages_numbers_raw)]
            if nums:
                min_page = min(nums)
                quran_progress = {
                    "total": 604,
                    "completed": 604 - min_page,
                    "remaining": min_page,
                    "current_page": min_page,
                    "pages_numbers_raw": pages_numbers_raw,
                }
            else:
                quran_progress = {}

            # Calculate actual pace: monthly recite / monthly attend days
            monthly_recite = monthly_report.get("saved_pages", {}).get("recite", 0) or 0
            monthly_attend = monthly_attendance.get("attend", 0) or 0
            pages_per_day = round(monthly_recite / monthly_attend, 2) if monthly_attend > 0 else 0
            quran_progress["pages_per_day"] = pages_per_day

            logger.info(f"Quran progress for {sub_url}: {quran_progress}")

            # Fetch today's specific lessons
            students_api = StudentsAPI(client)
            today_lessons = students_api.get_history_lessons(
                student_id=lookup.enjazi_student_id,
                episode_id=lookup.episode_id,
                institution_id=institution_id,
                date_of=date.today().strftime("%Y-%m-%d"),
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to fetch Enjazi report: {exc}")
        report = {}
        monthly_attendance = {}
        quran_progress = {}
        today_lessons = {}

    # 4. Build response
    return {
        "personal": {
            "name": lookup.name,
            "id_number": lookup.id_number,
            "nationality": lookup.nationality,
            "gender": lookup.gender,
            "phone": lookup.phone,
            "institution_name": lookup.institution_name,
            "teacher_name": lookup.teacher_name,
        },
        "report": report,
        "monthly_attendance": monthly_attendance,
        "quran_progress": quran_progress,
        "today_lessons": today_lessons,
        "meta": {
            "sub_url": sub_url,
            "enjazi_student_id": lookup.enjazi_student_id,
            "episode_id": lookup.episode_id,
            "period_range": period_range,
            "date_of": date_of,
        },
    }
