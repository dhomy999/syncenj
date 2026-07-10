# Supabase Integration — التكامل مع Supabase

## 🚀 البدء السريع (5 دقائق)

### 1. الاتصال ✅
```bash
✅ متصل بـ https://dbe.abuhuraira.space
```

### 2. إنشاء الجداول (الآن)
```
👉 اذهب إلى: https://dbe.abuhuraira.space/project/_/sql
👉 انسخ: محتوى ملف create_tables.sql
👉 اضغط: Run
```

### 3. اختبر الاتصال
```bash
python -X utf8 read_supabase_data.py
```

---

## 📁 الملفات المهمة

| الملف | الغرض |
|------|--------|
| `.env` | بيانات الاتصال (محفوظة ✓) |
| `supabase_reader.py` | قارئ البيانات |
| `read_supabase_data.py` | عرض البيانات |
| `create_tables.sql` | أكواد SQL للجداول |
| `SUPABASE_STATUS.md` | الحالة الحالية |
| `SUPABASE_SETUP.md` | دليل شامل |

---

## 📊 الجداول الجاهزة للإنشاء

- `jobs` — المهام المجدولة
- `job_logs` — سجلات التنفيذ
- `data_cache` — كاش البيانات
- `student_imports` — واردات الطلاب

---

## 💻 الاستخدام البرمجي

```python
from supabase_reader import SupabaseReader

reader = SupabaseReader()

# قراءة جدول
jobs = reader.read_table("jobs")

# قراءة مع تصفية
active_jobs = reader.read_with_filter("jobs", "is_active", True)

# عد السجلات
count = reader.get_table_count("jobs")
```

---

## ✨ الحالة

- ✅ Supabase: متصل
- ✅ المكتبات: مثبتة
- ✅ الأكواد: جاهزة
- ⏳ الجداول: جاهزة للإنشاء
- ⏳ البيانات: بعد إنشاء الجداول

---

## 🎯 الخطوات التالية

1. **الآن**: إنشاء الجداول (من Supabase Dashboard)
2. **بعدها**: اختبار القراءة
3. **لاحقاً**: دمج مع Backend

---

## 📞 تحتاج مساعدة؟

- **الاتصال**: `SUPABASE_STATUS.md`
- **الشرح الكامل**: `SUPABASE_SETUP.md`
- **الأكواد**: `create_tables.sql`

---

**لا تنس**: نسخ `create_tables.sql` إلى Supabase Dashboard وتشغيله! 🚀
