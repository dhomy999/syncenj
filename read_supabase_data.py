#!/usr/bin/env python3
"""
قارئ بيانات Supabase — Supabase Data Reader
يقرأ جميع البيانات من Supabase ويعرضها بصيغة جميلة
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# تحميل متغيرات البيئة
load_dotenv(Path(__file__).parent / ".env", override=False)


def print_section(title: str, width: int = 70):
    """طباعة عنوان قسم"""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_table(data: list[dict], max_rows: int = 10):
    """طباعة جدول من البيانات"""
    if not data:
        print("  (لا توجد بيانات)")
        return

    # الأعمدة
    if isinstance(data[0], dict):
        cols = list(data[0].keys())
    else:
        cols = ["value"]

    # حساب عرض الأعمدة
    col_widths = {col: max(len(col), 15) for col in cols}
    for row in data[:max_rows]:
        for col in cols:
            val = str(row.get(col, "")).replace("\n", " ")[:30]
            col_widths[col] = max(col_widths[col], len(val))

    # رأس الجدول
    header = " | ".join(col.ljust(col_widths[col]) for col in cols)
    print("  " + header)
    print("  " + "-" * (len(header) + 4))

    # البيانات
    for i, row in enumerate(data):
        if i >= max_rows:
            print(f"  ... و {len(data) - max_rows} سجل آخر")
            break
        values = [str(row.get(col, "")).replace("\n", " ")[:30] for col in cols]
        line = " | ".join(val.ljust(col_widths[col]) for val in values)
        print("  " + line)


def read_from_supabase():
    """قراءة البيانات من Supabase"""
    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_ANON_KEY", "")

        if not url or not key:
            print("\n❌ بيانات Supabase مفقودة في .env")
            return None

        print("\n🔗 جاري الاتصال بـ Supabase...")
        client = create_client(url, key)
        print(f"✅ متصل بـ {url}")

        return client

    except ImportError:
        print("\n❌ مكتبة supabase غير مثبتة بعد")
        print("⏳ جاري التثبيت... (قد تأخذ دقيقة أو دقيقتين)")
        return None
    except Exception as e:
        print(f"\n❌ خطأ في الاتصال: {e}")
        return None


def display_table_info(client, table_name: str, limit: int = 5):
    """عرض معلومات جدول"""
    try:
        # عد السجلات
        response = client.table(table_name).select("id", count="exact").execute()
        count = response.count or 0

        print(f"\n📊 جدول: {table_name}")
        print(f"   عدد السجلات: {count}")

        if count == 0:
            print(f"   (جدول فارغ)")
            return

        # قراءة عينة
        response = client.table(table_name).select("*").limit(limit).execute()
        data = response.data

        if data:
            print(f"\n   عينة من أول {len(data)} سجل:")
            print_table(data, max_rows=limit)

    except Exception as e:
        print(f"\n❌ خطأ في قراءة جدول '{table_name}': {e}")


def main():
    """البرنامج الرئيسي"""
    print_section("📖 قارئ بيانات Supabase", 70)

    # الاتصال
    client = read_from_supabase()
    if not client:
        print("\n⏳ يرجى انتظار انتهاء التثبيت ثم إعادة التشغيل:")
        print("   python read_supabase_data.py")
        return

    # قائمة الجداول
    tables = [
        "jobs",
        "job_logs",
        "data_cache",
        "student_imports",
    ]

    print_section("📋 البيانات المتاحة في Supabase", 70)

    for table in tables:
        display_table_info(client, table, limit=5)

    # ملخص
    print_section("✅ انتهت القراءة", 70)
    print("\n📝 ملاحظات:")
    print("  • يمكنك استخدام supabase_reader.py للقراءة برمجياً")
    print("  • استخدم SUPABASE_ANON_KEY للقراءة فقط")
    print("  • استخدم SUPABASE_SERVICE_ROLE_KEY للكتابة والحذف")
    print()


if __name__ == "__main__":
    main()
