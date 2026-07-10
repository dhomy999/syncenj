# حالة مشروع ربط إنجازي بـ Supabase — ما تم والمتبقّي

> آخر تحديث: 2026-07-06
> الخطة الكاملة: `C:\Users\DELL\.claude\plans\expressive-dazzling-dijkstra.md`

---

## 1. نظرة عامة على الهدف

تحويل نظام `enjazinew` إلى **جسر مزامنة أحادي الاتجاه**:

```
Supabase (المصدر — حيث يُدخل المعلّمون البيانات)  ──►  إنجازي (الوجهة — المنصّة الرسمية)
```

النظام يقرأ من قاعدة **Supabase** (`dbe.abuhuraira.space`) ويعكس البيانات في منصّة **إنجازي**
(`api.injaazy.com`) — وليس العكس.

### الخدمات المطلوبة (فقط هذه)
1. **مزامنة الطلاب** — ربط طلاب Supabase بمعرّفات إنجازي.
2. **مزامنة التسميع اليومي** — قراءة `quran_recitation` وكتابتها في إنجازي (الخدمة الأساسية).
3. **إضافة الطلاب** — تسجيل طلاب Supabase في إنجازي (اعتُمد المسار **الفردي المتزامن**).
4. **واجهتان:** الحلقات + الطلاب (تقرآن من Supabase).

### قرارات معمارية محسومة
- **الاتصال:** عميل Supabase REST بمفتاح `service_role` (لا يوجد اتصال Postgres مباشر).
- **الربط بإنجازي:** عمود `enjazi_id` في جدولي `students` و`halaqat`.
- **المنشأة في إنجازي:** `539` (مضبوطة في `.env` كـ `ENJAZI_INSTITUTION_ID`).

---

## 2. قاعدة Supabase (نظام إنتاج موجود مسبقًا)

| الجدول | السجلات | ملاحظات |
|---|---|---|
| `students` | 1131 | + عمود `enjazi_id` (مُضاف) |
| `halaqat` | 85 | + عمود `enjazi_id` (مُضاف) |
| `quran_recitation` | 763 | + عمودا `synced_at`, `sync_error` (مُضافان) |
| `attendance` | 19095 | الحضور/الغياب |
| `enrollments` | 1271 | تسجيل الطلاب في الحلقات |
| `guardians` | 711 | أولياء الأمور |
| `employees` | 54 | الموظفون/المعلمون |
| `departments` | 4 | الأقسام |
| `roles` | 7 | الأدوار |
| `mutoon_books` | 17 | كتب المتون |

---

## 3. ✅ ما تم إنجازه فعليًا

### Phase 1 — طبقة الاتصال + السكيمة ✅
- **`backend/supabase_client.py`** (جديد) — عميل Supabase singleton بمفتاح service_role. **مُختبر** (قرأ 1131 طالبًا).
- **`config/settings.py`** — أُضيفت `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
- **DDL على Supabase** — نُفِّذ فعليًا عبر SQL Editor (الملف `supabase_migration.sql`). الأعمدة موجودة ومؤكَّدة:
  - `students.enjazi_id` (BIGINT) ✅
  - `halaqat.enjazi_id` (BIGINT) ✅
  - `quran_recitation.synced_at` (TIMESTAMPTZ) + `sync_error` (TEXT) ✅

### Phase 2 — مزامنة الطلاب ✅ (مبنية ومُشغَّلة)
- **`backend/jobs/sync_students.py`** (جديد) — يجلب طلاب إنجازي، يطابقهم بـ Supabase عبر رقم الهوية
  (`student_national_id == username`)، ويكتب `students.enjazi_id`.
- مُسجَّل في `backend/scheduler.py` و`backend/routers/jobs.py` (نوع `sync_students`).

### Phase 2b — تشغيل مزامنة الطلاب ✅ (شُغِّل 2026-07-06)
- شُغّلت المهمة فعليًا. النتيجة: طلاب إنجازي بالمنشأة 539 = **447**، تطابقوا وارتبطوا = **346**
  (كان 0)، غير متطابق = 816 (لأن أغلب طلاب Supabase غير مسجّلين في إنجازي أصلًا → Phase 4).
- مؤكَّد في Supabase: `students.enjazi_id=not.is.null` → **346**.

### Phase 0 — اكتشاف نقطة حفظ التسميع ✅
اكتُشفت من `CHANGE.MD` (HAR):
```
PUT /institution_panel/students/{student_id}/change-recite
```
شكل الـ body:
```json
{"episode_id":4339,"student_id":87829,"attend_type":"attend","date_of":"2026-07-02",
 "lessons":[{"action":1,"lesson_id":14679032,"pillar_id":2,
   "mistakes":{"error":0,"mention":0,"tajweed":0},
   "from_verse_id":5945,"to_verse_id":5913,"std_level_id":212457,
   "done":true,"lesson_type":"history","frond_id":"2-212457-14679032-<rand>"}]}
```
- **`enjazi/api/recitation.py`** (جديد) — `RecitationAPI` فيه: `change_recite`, `build_lesson`,
  `get_episode_students`, `get_plan`, `get_lesson_complete`, `get_history_lessons`.
- **`enjazi/api/base.py`** — أُضيف `_put`.
- **قاعدة تحويل الدرجة** (مسجّلة في `recitation.py`): `ممتاز`→0 أخطاء، `جيد جدا`→تردّدان (mention=2)،
  `جيد`→خطأ وتردّدان (error=1, mention=2)، `لم يسمع`→يُتخطّى الركن.
- **الأركان:** `pillar_id` 2 = الحفظ، 3 = المراجعة، **4 = التثبيت** (الجانبي) — ✅ مؤكَّد 2026-07-06
  من `plan` الطالب (`pillar_name="تثبيت"`)، وثُبِّت في `enjazi/api/recitation.py` (`PILLAR_SIDE=4`).

### Phase 5 — واجهات الحلقات والطلاب ✅
**Backend:**
- **`backend/routers/halaqat.py`** — `GET /api/halaqat` (حلقات + اسم المعلّم + حالة الربط)،
  `GET /api/halaqat/enjazi-episodes` (66 حلقة إنجازي مع كاش للاختيار)،
  `PATCH /api/halaqat/{id}/link` (كتابة `enjazi_id`).
- **`backend/routers/students.py`** — `GET /api/students` (بحث + فلترة + حالة الربط).
- مُسجَّلان في `backend/main.py`.

**Frontend:**
- **`frontend/app/halaqat/page.tsx`** (جديد) — جدول الحلقات + نافذة اختيار حلقة إنجازي قابلة للبحث + ربط/إلغاء.
- **`frontend/app/students/page.tsx`** — أُعيدت كتابتها لتقرأ من Supabase + تصدير CSV.
- **`frontend/lib/api.ts`** — `halaqatApi`, `studentsApi`, أنواعها.
- **`frontend/components/sidebar.tsx`** — «الحلقات» تشير لصفحة Supabase (أُزيلت روابط غير مطلوبة).
- ✅ يجتاز فحص TypeScript (`tsc --noEmit` → 0).

### إصلاحات تشغيلية ✅
- **CORS** (`backend/main.py`) — أُضيف أصل التطوير المحلي وعناوين الشبكة الخاصة عبر `allow_origin_regex`،
  وأُضيف `localhost:3000` إلى `ALLOWED_ORIGINS` في `.env`. السبب كان أن الخادم يرفض أصل الواجهة المحلية.
- **ملاحظة تشغيل:** `frontend/.env.local` يستخدم `NEXT_PUBLIC_API_URL=http://192.168.8.247:8000`،
  لذا يجب تشغيل الخادم بـ `--host 0.0.0.0` ليصل إليه عنوان الشبكة.

---

## 4. ⏳ المراحل المتبقّية

### Phase 3 — مزامنة التسميع اليومي (الخدمة الأساسية) — الأهم
**الحاجة قبل البناء:**
1. ~~رقم `pillar_id` للتثبيت~~ ✅ **حُلّ** (= 4، مثبَّت في `recitation.py`).
2. **عيّنة استجابة (response)** لـ `history-lessons` و`plan` — لمعرفة `lesson_id` و`std_level_id`
   لكل طالب. (ملاحظة: `plan` مُختبر ويرجع `std_level_id` — مثال 212459 للطالب 87836/حلقة 4339.)
3. **تأكيد ربط الآية ↔ verse_id:** Supabase يخزّن أرقام آيات عامة (1..6236)، وإنجازي يستخدم
   `from_verse_id`/`to_verse_id`. يجب التحقق أن الترقيم متطابق بطالب واحد.

**البناء المخطّط (`backend/jobs/sync_recitation.py`):**
- قراءة صفوف `quran_recitation` لتاريخ معيّن حيث `synced_at IS NULL`.
- لكل صف: جلب `student.enjazi_id` + `halqa.enjazi_id`، وجلب `std_level_id`/`lesson_id` من إنجازي،
  وتحويل نطاقات الآيات + الدرجات (عبر `grade_to_mistakes`) إلى payload، ثم `change_recite`.
- عند النجاح: ضبط `synced_at`؛ عند الفشل: كتابة `sync_error`.
- تسجيل النوع `sync_recitation` في الجدولة + الموجّه.

### Phase 4 — إضافة الطلاب فرديًا ✅ (المسار الفردي يعمل ومُختبَر 2026-07-06)

**القرار المعماري الجديد:** اعتمدنا **الإضافة الفردية المتزامنة** بدل التسجيل الجماعي غير المتزامن
(الأخير كان يرجع `job_id` ولا يكتمل لساعات). الإضافة الفردية تُنشئ الحساب **فورًا** وترجع `enjazi_id`.

**النقطة المؤكَّدة** (من HAR `add_student.md` — منشأة 539، طلب ناجح 200):
```
POST /institution_panel/students          (multipart/form-data)
```
الحقول بترتيب اللوحة: `username, name, nationality_id=1, phone_number, gender_id=1, guardian_phone,`
`phone_country_code=00966, guardian_phone_country_code=00966, date_of_birth, program=523, level_id=1744, episode_id`.
يسبقها فحص هوية: `POST /institution_panel/add-user-requests/check-username {"username":..,"add_as":"student"}`.

**التفرّع حسب `code` من فحص الهوية** (مطبَّق في `add_students_individual.py`):
| `code` | المعنى | الإجراء |
|---|---|---|
| `new` | غير موجود | `POST /students` (إنشاء) ✅ |
| `exists_user_deleted` | محذوف من الحلقات | `POST /students/{id}/add` (إعادة تسجيل) |
| `already_exists` | نشط في حلقة | تخطّي |
| `exists_user_requires_approval` | في منشأة أخرى | لم يُضف — يحتاج مسار موافقة (غير مؤكَّد بعد) |

**تعديلات SDK لإنجاح المسار الفردي (2026-07-06):**
- **`enjazi/api/students.py`** — `add()` تُرسل multipart عبر **`CurlMime`** (curl_cffi لا يدعم `files=`)،
  بحقول اللوحة نفسها (`phone_number`, `guardian_phone`, `phone_country_code="00966"`)، والقيم `bytes` UTF-8
  حتى لا تُشوَّه الأسماء العربية. حقلا `NewStudent.phone_country_code/guardian_phone_country_code` صارا `str="00966"`.
- **`enjazi/client.py`** + **`enjazi/api/base.py`** — أُضيف تمرير `multipart=` (CurlMime) عبر `request/post/_post`.
- **`add_students_individual.py`** (جديد) — سكربت تشغيل: يجمع المؤهّلين من Supabase، يفحص الهوية،
  يتفرّع حسب `code`، ويطبع علامات واضحة + بانر تنبيه 🚨 بالحالات التي تحتاج مراجعة، ويحفظ `add_students_result.json`.
  التشغيل: `python add_students_individual.py [N|all]`.

**نتيجة أول تشغيل (10 محاولات، 2026-07-06):** **8 نجحوا** (أُنشئت حسابات `enjazi_id` 264865–264877)،
**2 فشلوا** بـ 422 «اسم المستخدم موجود مسبقا» لأنهما حسابان قائمان:
- `1159652898` → `exists_user_deleted` (يحتاج إعادة تسجيل عبر `students/{id}/add`).
- `1745494` → `exists_user_requires_approval` (يحتاج موافقة).
كما تُخطّي 14 طالبًا `already_exists` قبل الوصول للعشرة. المؤهّلون الحاليون = **527**.

**المتبقّي:**
- تأكيد payload إعادة التسجيل (`students/{id}/add`) للحالة `exists_user_deleted` — النقطة القديمة كانت ترجع 422
  «المستوى غير متوفر» بحقل `program`؛ يُختبَر فعليًا عند أول حالة.
- اكتشاف نقطة مسار الموافقة لحالة `exists_user_requires_approval`.
- بعد التشغيل الكامل: إعادة `sync_students` لكتابة `enjazi_id` في Supabase (المطابقة برقم الهوية).

**ملاحظة:** المسار الجماعي القديم (`batch-operations/register-students` + `sync-programs-selections`)
لا يزال في `enjazi/api/students.py` و`backend/jobs/register_students.py` لكن **متروك** لصالح المسار الفردي.

### Phase 6 — نقل الجداول التشغيلية إلى Supabase
- نقل `jobs` و`job_logs` من SQLite إلى Supabase (عبر مستودع رقيق فوق عميل REST).
- إعادة ربط `scheduler.py`, `routers/jobs.py`, `routers/logs.py`.
- حذف `backend/database.py` (SQLite) و`backend/models/cache.py` (`data_cache`) و`enjazi.db`.
- SQL الجداول جاهز (معلّق) في `supabase_migration.sql`.
- **مفاضلة:** ممكن إبقاء الجداول التشغيلية في SQLite (سباكة داخلية) لتقليل المخاطرة.

### Phase 7 — تنظيف
- حذف: `backend/routers/student_page.py`، `backend/services/student_lookup.py`،
  نقاط `data.py` غير المطلوبة (branches/facilities/episodes/teachers)، بقايا Sheets.
- حذف صفحات الواجهة غير المطلوبة (`teachers`, `facilities`, `episodes`) وتحديث الصفحة الرئيسية
  لتقرأ إحصاءاتها من Supabase بدل كاش إنجازي.
- حذف ملفات المساعدة المؤقتة: `SUPABASE_*.md`, `read_supabase_data.py`, `create_supabase_tables.py`,
  `create_tables.sql`, و ملفات HAR (`TEST.MD`, `CHANGE.MD`) بعد استخلاص المطلوب.

---

## 5. جدول الحالة السريع

| Phase | الوصف | الحالة |
|---|---|---|
| 1 | الاتصال + الإعدادات + DDL | ✅ مكتمل |
| 2 | بناء مزامنة الطلاب | ✅ مبني |
| 2b | تشغيل مزامنة الطلاب | ✅ شُغِّل (346 مربوط) |
| 0 | اكتشاف نقطة حفظ التسميع + SDK | ✅ مكتمل |
| 5 | واجهات الحلقات والطلاب + الربط | ✅ مكتمل (الحلقات 40/85 مربوطة) |
| — | إصلاح CORS/التشغيل المحلي | ✅ مكتمل |
| 3 | مزامنة التسميع اليومي | ⏳ ينتظر (عيّنات response + ربط verse_id) — pillar التثبيت ✅ |
| 4 | إضافة الطلاب فرديًا (متزامن) | ✅ يعمل — 8/10 نجحوا؛ تفرّع حسب code مطبَّق |
| 6 | نقل الجداول التشغيلية | ⏳ لم يبدأ |
| 7 | التنظيف | ⏳ لم يبدأ |

---

## 6. المطلوب من المستخدم

**لإكمال Phase 4 (المسار الفردي يعمل):**
- عند ظهور حالة `exists_user_deleted` أو `exists_user_requires_approval` في بانر التنبيه، نسخها
  للتحليل وتأكيد payload إعادة التسجيل / اكتشاف نقطة الموافقة.
- تشغيل `python add_students_individual.py all` بعد الاطمئنان، ثم إعادة `sync_students`.

**لإكمال Phase 3:**
1. من F12 → Network في لوحة إنجازي، نسخ **استجابة** (Response) الطلبين لطالب فيه تسميع:
   - `.../history-lessons?...`
   - `.../profile/episodes/{eid}/plan`
2. (اختياري) تأكيد أن أرقام الآيات في Supabase تطابق `verse_id` في إنجازي.

---

## 7. كيفية التشغيل (تطوير محلي)

```powershell
# الخادم (مرتبط بكل الشبكة ليصل إليه عنوان الـ LAN في .env.local)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# الواجهة (نافذة أخرى)
cd frontend
npm run dev
```
ثم افتح: صفحة الحلقات `/halaqat` وصفحة الطلاب `/students`.

**متطلبات `.env`:** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ENJAZI_USERNAME`, `ENJAZI_PASSWORD`,
`ENJAZI_INSTITUTION_ID=539`, `ALLOWED_ORIGINS` (يشمل أصل الواجهة).

---

## 8. ملفات المشروع الرئيسية (لهذا العمل)

**جديدة:**
`backend/supabase_client.py` · `backend/jobs/sync_students.py` · `backend/jobs/register_students.py` ·
`backend/routers/halaqat.py` · `backend/routers/students.py` · `enjazi/api/recitation.py` ·
`frontend/app/halaqat/page.tsx` · `supabase_migration.sql` · `add.md` (HAR تسجيل جماعي — مرجع) ·
`add_student.md` (HAR إضافة فردية ناجحة — مرجع Phase 4) · `add_students_individual.py` (سكربت التشغيل الفردي)

**معدّلة:**
`config/settings.py` · `backend/main.py` · `backend/scheduler.py` · `backend/routers/jobs.py` ·
`enjazi/api/base.py` (تمرير `multipart`) · `enjazi/api/students.py` (`add()` عبر CurlMime + `batch_*`) ·
`enjazi/client.py` (دعم `multipart=`) · `enjazi/api/recitation.py` (`PILLAR_SIDE=4`) · `enjazi/api/__init__.py` ·
`frontend/lib/api.ts` · `frontend/app/students/page.tsx` · `frontend/components/sidebar.tsx` · `.env`
