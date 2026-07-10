"""
Supabase Database Reader — قارئ قاعدة بيانات Supabase
يتصل بـ Supabase ويقرأ البيانات من الجداول الموجودة
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv(Path(__file__).parent / ".env", override=False)

# ─── استيراد Supabase ───────────────────────────────────────────────────
try:
    from supabase import create_client, Client
except ImportError:
    print("❌ مكتبة supabase غير مثبتة")
    print("📦 قم بتثبيتها: pip install supabase>=2.0.0")
    exit(1)


class SupabaseReader:
    """قارئ قاعدة بيانات Supabase — للقراءة فقط"""

    def __init__(self, url: str = None, key: str = None):
        """
        تهيئة الاتصال بـ Supabase

        Args:
            url: SUPABASE_URL (من متغيرات البيئة افتراضياً)
            key: SUPABASE_ANON_KEY (من متغيرات البيئة افتراضياً)
        """
        self.url = url or os.getenv("SUPABASE_URL", "")
        self.key = key or os.getenv("SUPABASE_ANON_KEY", "")

        if not self.url or not self.key:
            raise EnvironmentError(
                "❌ بيانات Supabase مفقودة\n"
                "أضف هذه المتغيرات إلى .env:\n"
                "  SUPABASE_URL=https://your-host\n"
                "  SUPABASE_ANON_KEY=your_key"
            )

        self.client: Client = create_client(self.url, self.key)
        print(f"✅ متصل بـ Supabase: {self.url}")

    # ─── قراءة الجداول ──────────────────────────────────────────────────

    def read_table(self, table_name: str, limit: int = 1000) -> list[dict]:
        """
        قراءة جدول كامل من Supabase

        Args:
            table_name: اسم الجدول (jobs, job_logs, data_cache, إلخ)
            limit: الحد الأقصى للسجلات المسترجعة

        Returns:
            قائمة من السجلات
        """
        try:
            response = (
                self.client.table(table_name)
                .select("*")
                .limit(limit)
                .execute()
            )
            print(f"✓ تم قراءة {len(response.data)} سجل من جدول '{table_name}'")
            return response.data
        except Exception as e:
            print(f"❌ خطأ عند قراءة الجدول '{table_name}': {e}")
            return []

    def read_with_filter(
        self, table_name: str, filter_col: str, filter_val, limit: int = 1000
    ) -> list[dict]:
        """
        قراءة جدول مع شرط تصفية

        Args:
            table_name: اسم الجدول
            filter_col: اسم العمود للتصفية
            filter_val: القيمة المراد تصفيتها
            limit: الحد الأقصى للسجلات

        Returns:
            قائمة من السجلات المطابقة
        """
        try:
            response = (
                self.client.table(table_name)
                .select("*")
                .eq(filter_col, filter_val)
                .limit(limit)
                .execute()
            )
            print(
                f"✓ تم قراءة {len(response.data)} سجل من '{table_name}' "
                f"حيث {filter_col}={filter_val}"
            )
            return response.data
        except Exception as e:
            print(f"❌ خطأ في التصفية: {e}")
            return []

    # ─── معلومات الجداول ────────────────────────────────────────────────

    def get_table_count(self, table_name: str) -> int:
        """الحصول على عدد السجلات في جدول"""
        try:
            response = (
                self.client.table(table_name)
                .select("id", count="exact")
                .execute()
            )
            return response.count
        except Exception as e:
            print(f"❌ خطأ في عد السجلات: {e}")
            return 0

    def get_table_schema(self, table_name: str) -> dict:
        """الحصول على معلومات الأعمدة في الجدول"""
        try:
            # استخدام REST API مباشرة للحصول على schema
            response = self.client.postgrest.get(f"/information_schema.columns")
            return response
        except Exception as e:
            print(f"❌ خطأ في الحصول على schema: {e}")
            return {}


# ─── الدوال الرئيسية للاستخدام المباشر ──────────────────────────────────

def read_jobs() -> list[dict]:
    """قراءة جميع المهام المجدولة"""
    reader = SupabaseReader()
    return reader.read_table("jobs")


def read_job_logs(limit: int = 100) -> list[dict]:
    """قراءة سجلات تنفيذ المهام"""
    reader = SupabaseReader()
    return reader.read_table("job_logs", limit=limit)


def read_data_cache() -> list[dict]:
    """قراءة الكاش المحلي"""
    reader = SupabaseReader()
    return reader.read_table("data_cache")


def read_active_jobs() -> list[dict]:
    """قراءة المهام النشطة فقط"""
    reader = SupabaseReader()
    return reader.read_with_filter("jobs", "is_active", True)


# ─── اختبار الاتصال ─────────────────────────────────────────────────────

def test_connection():
    """اختبار الاتصال بـ Supabase وعرض إحصاءات الجداول"""
    try:
        reader = SupabaseReader()

        tables = ["jobs", "job_logs", "data_cache", "student_imports"]
        print("\n📊 إحصاءات الجداول:\n" + "=" * 50)

        for table in tables:
            count = reader.get_table_count(table)
            print(f"  • {table:20} : {count} سجل")

        print("=" * 50)
        print("✅ الاتصال ناجح!")
        return True

    except EnvironmentError as e:
        print(f"\n❌ {e}")
        return False
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        return False


if __name__ == "__main__":
    print("\n🔗 اختبار الاتصال بـ Supabase...\n")
    test_connection()
