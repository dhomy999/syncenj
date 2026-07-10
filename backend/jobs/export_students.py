"""
مهمة: تصدير بيانات جميع الطلاب
تجلب كل الطلاب وتُرجع ملخصاً في السجل.
يمكن توسيعها لاحقاً لحفظ CSV أو رفع Google Sheets.
"""
from sqlalchemy.orm import Session

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api.students import StudentsAPI
from enjazi.utils.logger import logger


async def run(params: dict, log_id: int, db: Session) -> dict:
    """
    params:
        limit (optional): الحد الأقصى للطلاب (افتراضي 5000)
    """
    limit = int(params.get("limit", 5000))

    with EnjaziClient() as client:
        get_valid_token(client)
        api = StudentsAPI(client)
        students = api.list_all(limit=limit)

    logger.info(f"export_students: جُلب {len(students)} طالب")

    # إحصاءات مفيدة
    male   = sum(1 for s in students if s.get("gender_id") == 1)
    female = sum(1 for s in students if s.get("gender_id") == 2)
    active = sum(1 for s in students if s.get("active"))

    return {
        "total": len(students),
        "male": male,
        "female": female,
        "active": active,
    }
