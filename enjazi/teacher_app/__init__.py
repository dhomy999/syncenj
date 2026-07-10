"""
عميل تطبيق المعلم (apps/v1) — نظام مستقل عن لوحة المنشأة (front_app_api).

يُستخدم لفتح الحلقات من جهة المعلم عبر تحضير طالب واحد لكل حلقة (العملية 2).
رابط أساسي مختلف، تسجيل دخول مختلف (data.access_token)، وترويسة x-episode-id.
"""
from enjazi.teacher_app.client import TeacherAppClient
from enjazi.teacher_app.api import TeacherAPI

__all__ = ["TeacherAppClient", "TeacherAPI"]
