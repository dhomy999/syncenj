# خطوات إعداد Supabase — Supabase Setup Steps

دليل سريع لإنشاء الجداول والتحقق من الاتصال.

---

## ✅ ما تم حتى الآن

1. ✅ تثبيت مكتبة Supabase
2. ✅ إضافة بيانات الاتصال إلى `.env`
3. ✅ اختبار الاتصال بنجاح ✨

```
✅ متصل بـ https://dbe.abuhuraira.space
```

---

## 📋 الخطوة التالية: إنشاء الجداول

### الطريقة الأولى: من Supabase Dashboard (الأسهل) ✨

#### الخطوات:
1. اذهب إلى [Supabase Dashboard](https://supabase.com/dashboard)
2. اختر مشروعك
3. من الجانب الأيسر، اختر **SQL Editor**
4. اضغط **New Query**
5. انسخ محتوى الملف: **`create_tables.sql`**
6. ألصقه في محرر SQL
7. اضغط **Run** (أو Ctrl+Enter)

#### ستشاهد:
```
Query executed successfully
4 rows affected
```

---

### الطريقة الثانية: من الترمينال (لاحقاً)

يمكن استخدام أدوات مثل `psql` مباشرة:

```bash
psql -h dbe.abuhuraira.space -U postgres -d postgres -c "$(cat create_tables.sql)"
```

---

## 🔍 التحقق من نجاح الإنشاء

بعد إنشاء الجداول، شغّل هذا:

```bash
python -X utf8 read_supabase_data.py
```

يجب أن ترى:

```
✅ متصل بـ https://dbe.abuhuraira.space

📊 جدول: jobs
   عدد السجلات: 0

📊 جدول: job_logs
   عدد السجلات: 0

... إلخ
```

---

## 📖 الملفات المتاحة

| الملف | الوصف |
|------|-------|
| **`supabase_reader.py`** | قارئ البيانات من Supabase |
| **`read_supabase_data.py`** | عرض البيانات بصيغة جميلة |
| **`create_supabase_tables.py`** | أداة لإنشاء الجداول (قد لا تعمل) |
| **`create_tables.sql`** | أكواد SQL لإنشاء الجداول |
| **`SUPABASE_SETUP.md`** | دليل شامل |
| **`.env`** | بيانات الاتصال |

---

## 🚀 استخدام البيانات برمجياً

### بعد إنشاء الجداول، يمكنك استخدام البيانات هكذا:

```python
from supabase_reader import SupabaseReader

# إنشاء القارئ
reader = SupabaseReader()

# قراءة جدول
jobs = reader.read_table("jobs", limit=100)
print(f"عدد المهام: {len(jobs)}")

# قراءة مع تصفية
active_jobs = reader.read_with_filter("jobs", "is_active", True)

# عد السجلات
count = reader.get_table_count("jobs")
print(f"إجمالي: {count}")
```

---

## 🐛 استكشاف الأخطاء

### الخطأ: "relation does not exist"

**المعنى**: الجدول غير موجود

**الحل**: أنشئ الجدول من Supabase Dashboard

### الخطأ: "connection refused"

**المعنى**: لا يمكن الاتصال بـ Supabase

**الحل**:
1. تحقق من بيانات الاتصال في `.env`
2. تحقق من أن المشروع مشغل

### الخطأ: "permission denied"

**المعنى**: المفتاح (Key) ليس لديه صلاحيات كافية

**الحل**: استخدم `SUPABASE_SERVICE_ROLE_KEY` للكتابة

---

## 📝 ملاحظات مهمة

### الأمان
- ❌ لا تشارك `SUPABASE_SERVICE_ROLE_KEY` مع أحد
- ✅ استخدم `SUPABASE_ANON_KEY` للقراءة فقط
- ✅ حفظ المفاتيح في متغيرات البيئة فقط

### الأداء
- الجداول يمكن أن تنمو كبيرة مع الوقت
- استخدم الفهارس (Indexes) للسرعة
- الفهارس موجودة بالفعل في `create_tables.sql`

### النسخ الاحتياطية
- Supabase يعمل نسخ احتياطية تلقائية يومية
- يمكنك استعادة النسخ من Settings

---

## 🎯 الخطوات التالية

### بعد إنشاء الجداول:

1. **اختبر القراءة**
   ```bash
   python -X utf8 read_supabase_data.py
   ```

2. **أضف بيانات تجريبية** (اختياري)
   ```python
   from supabase_reader import SupabaseReader
   reader = SupabaseReader()
   
   # إضافة مهمة جديدة
   new_job = {
       "name": "مهمة تجريبية",
       "type": "sync_episodes",
       "cron_expression": "0 6 * * *"
   }
   reader.client.table("jobs").insert(new_job).execute()
   ```

3. **تحديث Backend** (لاحقاً)
   - تغيير من SQLite إلى Supabase
   - نقل البيانات القديمة
   - اختبار شامل

---

## 📞 تحتاج إلى مساعدة؟

### من داخل البرنامج:
```bash
# قراءة البيانات
python -X utf8 read_supabase_data.py

# اختبار الاتصال
python supabase_reader.py
```

### من Supabase Dashboard:
1. اذهب إلى **Database** → **Tables**
2. تحقق من وجود الجداول
3. اختر جدول واعرض البيانات

### المساعدة الإضافية:
- Supabase Docs: https://supabase.com/docs
- SQL Reference: https://www.postgresql.org/docs/

---

## ✨ بعد الانتهاء

بعد إنشاء الجداول بنجاح:

1. ✅ الاتصال يعمل
2. ✅ الجداول جاهزة
3. ✅ يمكنك قراءة البيانات
4. ⏳ بعد ذلك: الكتابة والتحديث والحذف

**الشيء التالي**: تحديث Backend للعمل مع Supabase! 🚀
