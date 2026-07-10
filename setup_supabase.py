#!/usr/bin/env python3
"""
أداة إعداد Supabase — Setup Supabase Connection
تساعدك في إدخال بيانات Supabase وحفظها في .env
"""
import os
import sys
from pathlib import Path


def get_supabase_credentials():
    """الحصول على بيانات Supabase من المستخدم"""
    print("\n" + "=" * 60)
    print("🔧 أداة إعداد Supabase")
    print("=" * 60)
    print(
        "\nالخطوات:\n"
        "1. اذهب إلى https://supabase.com\n"
        "2. سجل دخول أو أنشئ حساباً\n"
        "3. اختر مشروعك أو أنشئ واحداً جديداً\n"
        "4. من Settings → API → انسخ:\n"
        "   - Project URL\n"
        "   - anon public key\n"
        "5. ألصقها هنا"
    )

    print("\n" + "-" * 60)

    # طلب البيانات
    supabase_url = input("\n📌 أدخل SUPABASE_URL (Project URL):\n> ").strip()
    if not supabase_url:
        print("❌ URL مفقود!")
        return None, None

    supabase_key = input("\n🔑 أدخل SUPABASE_KEY (anon public key):\n> ").strip()
    if not supabase_key:
        print("❌ مفتاح مفقود!")
        return None, None

    return supabase_url, supabase_key


def save_to_env(url: str, key: str):
    """حفظ البيانات في ملف .env"""
    env_path = Path(__file__).parent / ".env"

    # قراءة المحتوى الحالي
    content = ""
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()

    # إزالة البيانات القديمة إن وجدت
    lines = content.split("\n")
    lines = [l for l in lines if not l.startswith("SUPABASE_")]

    # إضافة البيانات الجديدة
    new_content = "\n".join(lines).rstrip() + "\n\n# ─── Supabase ──────────────────────────────────────────────\n"
    new_content += f"SUPABASE_URL={url}\n"
    new_content += f"SUPABASE_KEY={key}\n"

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"\n✅ تم حفظ البيانات في {env_path}")
    return True


def test_connection():
    """اختبار الاتصال"""
    print("\n" + "-" * 60)
    print("🔗 اختبار الاتصال...\n")

    try:
        from supabase_reader import SupabaseReader
        reader = SupabaseReader()

        # اختبار الاتصال
        tables = ["jobs", "job_logs", "data_cache"]
        print("\n📊 جداول موجودة:\n")

        for table in tables:
            try:
                count = reader.get_table_count(table)
                print(f"  ✓ {table:20} : {count} سجل")
            except Exception as e:
                print(f"  ✗ {table:20} : غير موجود أو خطأ في الاتصال")

        print("\n✅ الاتصال ناجح!\n")
        return True

    except ImportError:
        print("⚠️  مكتبة supabase غير مثبتة")
        print("قم بتثبيتها: pip install -q supabase>=2.0.0")
        return False
    except EnvironmentError as e:
        print(f"❌ {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False


def main():
    """البرنامج الرئيسي"""
    # الحصول على البيانات
    url, key = get_supabase_credentials()
    if not url or not key:
        print("\n❌ تم الإلغاء")
        return False

    # حفظ البيانات
    save_to_env(url, key)

    # اختبار الاتصال
    success = test_connection()

    if success:
        print("\n" + "=" * 60)
        print("✅ تم الإعداد بنجاح!")
        print("=" * 60)
        print("\nالخطوة التالية:")
        print("  python supabase_reader.py")
        print("\nأو في الكود:")
        print("  from supabase_reader import read_jobs, read_job_logs")
        print("  jobs = read_jobs()")
        print("=" * 60 + "\n")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
