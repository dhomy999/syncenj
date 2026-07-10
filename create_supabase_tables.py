#!/usr/bin/env python3
"""
أداة إنشاء جداول Supabase — Create Supabase Tables
تنشئ الجداول المطلوبة في قاعدة البيانات
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv(Path(__file__).parent / ".env", override=False)

# قائمة الجداول التي سيتم إنشاؤها
TABLES_SQL = {
    "jobs": """
        CREATE TABLE IF NOT EXISTS jobs (
            id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            name VARCHAR(200) NOT NULL,
            type VARCHAR(50) NOT NULL,
            cron_expression VARCHAR(100),
            params JSONB,
            is_active BOOLEAN DEFAULT true,
            description TEXT,
            last_run_at TIMESTAMP WITH TIME ZONE,
            next_run_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """,
    "job_logs": """
        CREATE TABLE IF NOT EXISTS job_logs (
            id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            status VARCHAR(50) NOT NULL,
            triggered_by VARCHAR(50),
            result JSONB,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            finished_at TIMESTAMP WITH TIME ZONE
        )
    """,
    "data_cache": """
        CREATE TABLE IF NOT EXISTS data_cache (
            key VARCHAR(255) PRIMARY KEY,
            data JSONB NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """,
    "student_imports": """
        CREATE TABLE IF NOT EXISTS student_imports (
            id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            job_log_id BIGINT REFERENCES job_logs(id) ON DELETE CASCADE,
            student_data JSONB,
            import_status VARCHAR(50),
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """,
}


def create_tables():
    """إنشاء الجداول في Supabase"""
    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL", "")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

        if not url or not service_key:
            print("❌ بيانات Supabase مفقودة في .env")
            print("تأكد من وجود:")
            print("  SUPABASE_URL=...")
            print("  SUPABASE_SERVICE_ROLE_KEY=...")
            return False

        print("\n🔗 جاري الاتصال بـ Supabase...")
        client = create_client(url, service_key)
        print(f"✅ متصل بـ {url}")

        print("\n📋 جاري إنشاء الجداول...\n")

        for table_name, sql in TABLES_SQL.items():
            try:
                # محاولة تنفيذ SQL
                response = client.rpc(
                    "run_sql", {"query": sql.strip()}, invoke_options={"count": "exact"}
                ).execute()
                print(f"  ✅ جدول '{table_name}' تم إنشاؤه بنجاح")
            except Exception as e:
                # قد يكون الجدول موجوداً بالفعل، وهذا حسن
                if "already exists" in str(e):
                    print(f"  ℹ️  جدول '{table_name}' موجود بالفعل")
                else:
                    # محاولة بديلة: استخدام API مباشرة
                    try:
                        # التحقق من وجود الجدول
                        client.table(table_name).select("id").limit(1).execute()
                        print(f"  ℹ️  جدول '{table_name}' موجود بالفعل")
                    except Exception as e2:
                        print(f"  ❌ خطأ في جدول '{table_name}': {e2}")
                        print(f"     الحل: أنشئ الجدول يدوياً من Supabase Dashboard")

        print("\n" + "=" * 60)
        print("✅ انتهت عملية إنشاء الجداول!")
        print("=" * 60)
        print("\nالخطوة التالية:")
        print("  python read_supabase_data.py")
        print("\nأو استخدم البيانات برمجياً:")
        print("  from supabase_reader import read_jobs, read_job_logs")
        print()

        return True

    except ImportError:
        print("❌ مكتبة supabase غير مثبتة")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        return False


def create_tables_manual():
    """دليل إنشاء الجداول يدوياً"""
    print("\n" + "=" * 70)
    print("🔧 دليل إنشاء الجداول يدوياً")
    print("=" * 70)
    print("\nإذا لم ينجح الإنشاء التلقائي:")
    print("\n1. اذهب إلى Supabase Dashboard")
    print("2. اختر SQL Editor من الجانب الأيسر")
    print("3. انسخ والصق أحد الأكواد التالية:")

    for table_name, sql in TABLES_SQL.items():
        print(f"\n--- جدول: {table_name} ---")
        print(sql.strip())

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🏗️  أداة إنشاء جداول Supabase")
    print("=" * 70)

    success = create_tables()

    if not success:
        create_tables_manual()
