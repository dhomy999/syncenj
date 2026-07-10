# إعداد Supabase — Supabase Integration Guide

دليل شامل لربط البرنامج بـ Supabase بدلاً من SQLite.

---

## 🚀 البدء السريع

### الخطوة 1: إنشاء مشروع Supabase

1. اذهب إلى [supabase.com](https://supabase.com)
2. سجل دخول أو أنشئ حساباً
3. أنشئ مشروع جديد:
   - **Project Name**: `enjazi-automation`
   - **Database Password**: اختر كلمة مرور قوية
   - **Region**: اختر الأقرب لك

4. انتظر حتى انتهاء البيانات (5-10 دقائق)

### الخطوة 2: الحصول على بيانات الاتصال

1. اذهب إلى **Settings → API**
2. انسخ:
   - **Project URL**: (يبدو مثل: `https://xyzabc.supabase.co`)
   - **anon public**: (المفتاح العام)

### الخطوة 3: تثبيت المكتبة

```bash
pip install supabase>=2.0.0 postgrest-py>=0.10.0
```

### الخطوة 4: إعداد الاتصال

#### الطريقة الأولى: تفاعلية (موصى به)

```bash
python setup_supabase.py
```

هذا سيطلب منك:
- SUPABASE_URL
- SUPABASE_KEY

ويحفظها في `.env` تلقائياً ✅

#### الطريقة الثانية: يدوية

أضف هذا إلى ملف `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
```

### الخطوة 5: اختبر الاتصال

```bash
python supabase_reader.py
```

يجب أن ترى:
```
✅ متصل بـ Supabase: https://...
✓ تم قراءة 0 سجل من جدول 'jobs'
...
```

---

## 📊 نقل الجداول من SQLite إلى Supabase

### الجداول المطلوبة

يجب إنشاء هذه الجداول في Supabase:

#### 1. جدول `jobs` (المهام)

```sql
CREATE TABLE jobs (
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
);
```

#### 2. جدول `job_logs` (سجلات المهام)

```sql
CREATE TABLE job_logs (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  status VARCHAR(50) NOT NULL,
  triggered_by VARCHAR(50),
  result JSONB,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  finished_at TIMESTAMP WITH TIME ZONE
);
```

#### 3. جدول `data_cache` (الكاش)

```sql
CREATE TABLE data_cache (
  key VARCHAR(255) PRIMARY KEY,
  data JSONB NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 4. جدول `student_imports` (الواردات)

```sql
CREATE TABLE student_imports (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  job_log_id BIGINT REFERENCES job_logs(id) ON DELETE CASCADE,
  student_data JSONB,
  import_status VARCHAR(50),
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### كيفية إنشاء الجداول

#### الطريقة 1: عبر Supabase Dashboard (الأسهل)

1. اذهب إلى مشروعك في Supabase
2. اختر **SQL Editor** من الجانب الأيسر
3. انسخ والصق أحد الأكواد أعلاه
4. اضغط **Run** (أو Ctrl+Enter)

#### الطريقة 2: عبر Python

```python
from supabase import create_client

client = create_client(
    url="https://your-project.supabase.co",
    key="your_anon_key"
)

# سيتم إضافة دالة لهذا قريباً
```

---

## 📖 استخدام `supabase_reader.py`

### قراءة جدول كامل

```python
from supabase_reader import read_jobs, read_job_logs, read_data_cache

# قراءة جميع المهام
jobs = read_jobs()
print(f"عدد المهام: {len(jobs)}")

# قراءة آخر 50 سجل من الـ logs
logs = read_job_logs(limit=50)
```

### قراءة مع تصفية

```python
from supabase_reader import SupabaseReader

reader = SupabaseReader()

# المهام النشطة فقط
active_jobs = reader.read_with_filter("jobs", "is_active", True)

# سجلات نوع معين
logs = reader.read_with_filter("job_logs", "status", "success")
```

### معلومات الجداول

```python
reader = SupabaseReader()

# عدد السجلات
count = reader.get_table_count("jobs")
print(f"عدد المهام: {count}")

# اختبار الاتصال
from supabase_reader import test_connection
test_connection()
```

---

## 🔄 هجرة البيانات من SQLite إلى Supabase

### السيناريو: لديك بيانات في SQLite وتريد نقلها

```python
import sqlite3
import json
from datetime import datetime
from supabase_reader import SupabaseReader

# 1. قراءة من SQLite
conn = sqlite3.connect("enjazi.db")
cursor = conn.cursor()

# قراءة الجداول
cursor.execute("SELECT * FROM jobs")
jobs = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

# 2. الكتابة إلى Supabase
reader = SupabaseReader()
for job in jobs:
    try:
        reader.client.table("jobs").insert(job).execute()
        print(f"✓ تم نقل المهمة: {job['name']}")
    except Exception as e:
        print(f"✗ خطأ في نقل {job['name']}: {e}")

conn.close()
print("✅ انتهت العملية")
```

---

## 🔐 الأمان

### أنواع المفاتيح في Supabase

| المفتاح | الاستخدام | الأمان |
|--------|----------|--------|
| **anon key** | تطبيقات العميل (Frontend) | عام، محدود الصلاحيات |
| **service role key** | تطبيقات الخادم (Backend) | سري، صلاحيات كاملة |

### نصائح الأمان

✅ **استخدم `anon key` للـ Frontend**
- محدود الوصول
- يمكن نشره علناً

✅ **استخدم `service role key` للـ Backend فقط**
- صلاحيات كاملة
- **لا تنشره أبداً**
- خزنه في متغيرات البيئة

❌ **لا تنشر أي مفاتيح في GitHub**

---

## 🔌 تحديث Backend للعمل مع Supabase

### تحديث `backend/database.py`

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# اختر بناءً على البيئة
USE_SUPABASE = os.getenv("SUPABASE_URL") is not None

if USE_SUPABASE:
    # Supabase (PostgreSQL)
    DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
else:
    # SQLite (محلي)
    DATABASE_URL = "sqlite:///./enjazi.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```

---

## 🐛 استكشاف الأخطاء

### الخطأ: "SUPABASE_URL مفقود"

**السبب**: متغيرات البيئة لم تُحفظ بشكل صحيح

**الحل**:
```bash
# تحقق من .env
cat .env | grep SUPABASE

# أو أعد التشغيل
python setup_supabase.py
```

### الخطأ: "Failed to connect"

**السبب**: بيانات الاتصال غير صحيحة

**الحل**:
1. تحقق من الـ URL والمفتاح في Supabase Dashboard
2. تأكد من أن المشروع مشغل
3. اختبر الاتصال:
   ```bash
   python supabase_reader.py
   ```

### الخطأ: "جدول غير موجود"

**السبب**: لم تنشئ الجداول في Supabase

**الحل**: أنشئ الجداول كما موضح أعلاه

---

## 📝 الملفات الجديدة

```
project/
├── supabase_reader.py      ← قارئ قاعدة البيانات
├── setup_supabase.py       ← أداة الإعداد التفاعلية
├── SUPABASE_SETUP.md       ← هذا الملف
└── .env                    ← (محدّث) يحتوي على SUPABASE_URL و SUPABASE_KEY
```

---

## 🎯 الخطوات التالية

### المرحلة 1: القراءة (اكتملت ✅)
- ✅ قراءة البيانات من Supabase
- ✅ اختبار الاتصال

### المرحلة 2: الكتابة
- ⏳ إضافة البيانات إلى Supabase
- ⏳ تحديث البيانات
- ⏳ حذف البيانات

### المرحلة 3: التكامل الكامل
- ⏳ تحديث Backend للعمل مع Supabase بدلاً من SQLite
- ⏳ نقل جميع البيانات القديمة
- ⏳ اختبار شامل

### المرحلة 4: الميزات الإضافية
- ⏳ Realtime Subscriptions
- ⏳ Supabase Auth للـ Frontend
- ⏳ Backups والنسخ الاحتياطية

---

## 📞 المساعدة

### مصادر مفيدة

- [Supabase Docs](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

### الأسئلة الشائعة

**س: هل يمكن استخدام Supabase بدون حذف SQLite؟**
ج: نعم! يمكنك استخدام كليهما معاً مؤقتاً

**س: كم تكلفة Supabase؟**
ج: مجاني للـ Development، ثم حسب الاستخدام

**س: هل بيانات Supabase آمنة؟**
ج: نعم، تشفير في المسير والتخزين

---

## ✅ تم الانتهاء من الإعداد الأولي!

الآن لديك:
- ✅ قارئ Supabase
- ✅ أداة إعداد
- ✅ توثيق شامل
- ✅ أمثلة للاستخدام

**الخطوة التالية**: اجلس بيانات Supabase الخاصة بك وشغّل `setup_supabase.py` 🚀
