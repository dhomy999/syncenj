"""
اختبار شامل لجميع الـ API wrappers.
يطبع عدد العناصر المُستردة من كل endpoint.

Run:
    python scripts/test_api.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from enjazi.client import EnjaziClient
from enjazi.auth import get_valid_token
from enjazi.api import CentersAPI, InstitutionsAPI, EpisodesAPI, StudentsAPI, TeachersAPI
from enjazi.utils.logger import logger


def section(title: str):
    logger.info(f"{'='*10} {title} {'='*10}")


def main():
    with EnjaziClient() as client:
        get_valid_token(client)

        centers_api      = CentersAPI(client)
        institutions_api = InstitutionsAPI(client)
        episodes_api     = EpisodesAPI(client)
        students_api     = StudentsAPI(client)
        teachers_api     = TeachersAPI(client)

        # --- Centers (الفروع) ---
        section("الفروع")
        centers = centers_api.list()
        logger.info(f"  centers.list()       -> {len(centers)} فروع")

        centers_short = centers_api.get_list()
        logger.info(f"  centers.get_list()   -> {len(centers_short)} فروع (قائمة مختصرة)")

        # --- Institutions (المنشآت) ---
        section("المنشآت")
        inst_list = institutions_api.get_list()
        logger.info(f"  institutions.get_list()  -> {len(inst_list)} منشأة تحت الفرع")

        inst_all = institutions_api.list_all()
        logger.info(f"  institutions.list_all()  -> {len(inst_all)} منشأة (كل الجمعية)")

        # --- Episodes ---
        section("الحلقات")
        ep_center = episodes_api.list_by_center()
        logger.info(f"  episodes.list_by_center()  -> {len(ep_center)} حلقة")

        ep_all = episodes_api.list_all()
        logger.info(f"  episodes.list_all()        -> {len(ep_all)} حلقة (كل الجمعية)")

        # --- Students ---
        section("الطلاب")
        students = students_api.list_all()
        logger.info(f"  students.list_all()  -> {len(students)} طالب")

        # --- Teachers ---
        section("المعلمون")
        teachers = teachers_api.list_all()
        logger.info(f"  teachers.list_all()         -> {len(teachers)} معلم")

        teachers_c = teachers_api.list_by_center()
        logger.info(f"  teachers.list_by_center()   -> {len(teachers_c)} معلم تحت المركز")

        supervisors = teachers_api.supervisors_by_center()
        logger.info(f"  teachers.supervisors_by_center() -> {len(supervisors)} مشرف")

        # --- Summary ---
        section("الملخص")
        logger.success("جميع الـ API wrappers تعمل بنجاح")
        print()
        print(f"  الفروع:        {len(centers)}")
        print(f"  المنشآت:       {len(inst_all)}")
        print(f"  الحلقات:       {len(ep_all)}")
        print(f"  الطلاب:        {len(students)}")
        print(f"  المعلمون:      {len(teachers)}")


if __name__ == "__main__":
    main()
