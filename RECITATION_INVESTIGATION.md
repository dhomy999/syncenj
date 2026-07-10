# تقرير: آلية تسجيل التسميع في إنجازي وخريطة الآيات (verse_id)

> تاريخ التحقيق: 2026-07-08
> المصدر: تحليل HAR محاكى (`TSM3E.txt`) + فحص مباشر لـ API إنجازي + بيانات Supabase الحقيقية.
> الهدف: تمهيد مزامنة أحادية الاتجاه لسجلات التسميع **Supabase → إنجازي**.

---

## 1) نقطة الحفظ المركزية (The Endpoint)

```
PUT /institution_panel/students/{student_id}/change-recite
```

- **الطريقة `PUT`** (وليست POST) — تُستخدم لإنشاء **و**تعديل تسميع يوم معيّن.
- `{student_id}` = معرّف الطالب في إنجازي (مثال `30364`) — يُمرَّر في المسار.
- المتصفح يسبقها بطلب `OPTIONS` (CORS preflight) ثم يرسل `PUT` — هذا سلوك المتصفح فقط ولا يلزم في الـ backend.

---

## 2) بنية الطلب الكاملة (The Payload)

```json
{
  "episode_id": 4339,
  "student_id": 30364,
  "attend_type": "attend",
  "date_of": "2026-07-02",
  "lessons": [
    {
      "action": 1,
      "lesson_id": 14679001,
      "pillar_id": 2,
      "mistakes": { "error": 0, "mention": 1, "tajweed": 0 },
      "from_verse_id": 6126,
      "to_verse_id": 6130,
      "std_level_id": 212256,
      "done": true,
      "lesson_type": "history",
      "frond_id": "2-212256-14679001-31e21t6de9a"
    }
  ]
}
```

### شرح الحقول

| الحقل | المعنى | مثال | المصدر عند المزامنة |
|------|--------|------|---------------------|
| `episode_id` | الحلقة في إنجازي | `4339` | `halaqat.enjazi_id` |
| `student_id` | الطالب في إنجازي | `30364` | `students.enjazi_id` |
| `attend_type` | نوع الحضور | `"attend"` | ثابت (حاضر) |
| `date_of` | يوم التسميع | `"2026-07-02"` | `quran_recitation.recite_date` |
| `lessons[]` | مصفوفة الأركان المُسمَّعة | — | يُبنى لكل ركن |
| `action` | إجراء الدرس | `1` | `1` = حفظ/تأكيد |
| `lesson_id` | معرّف الدرس الداخلي | `14679001` | ⚠️ مصدره قيد التحقيق (القسم 7) |
| `pillar_id` | نوع الركن | `2` | 2=حفظ، 3=مراجعة، 4=تثبيت |
| `mistakes` | الأخطاء `{error,mention,tajweed}` | `{0,1,0}` | تُحوَّل من الدرجة النصية |
| `from_verse_id` | آية البداية (كونية) | `6126` | `*_start_aya` (مباشر) |
| `to_verse_id` | آية النهاية (كونية) | `6130` | `*_end_aya` (مباشر) |
| `std_level_id` | مستوى الطالب في الحلقة | `212256` | من `plan.data.program.level.std_level_id` |
| `done` | مكتمل | `true` | ثابت |
| `lesson_type` | نوع الدرس | `"history"` | ثابت |
| `frond_id` | مُعرّف واجهة فريد | `"2-212256-..."` | يُولَّد عشوائياً |

---

## 3) الترويسات (Headers)

اللوحة أرسلت فقط:
```
content-type: application/json
x-current-role: 7
x-institution-id: 539
x-requested-with: XMLHttpRequest
authorization: Bearer <token>
```

> ملاحظة: لم تُرسِل `x-behalf-id`/`x-behalf-on`، لكن `institution_headers()` في المشروع تضيفهما — والخادم يقبلهما (لا تعارض).

---

## 4) الطلبات المساندة (بيانات لازمة قبل بناء الـ payload)

تسلسل المحاكاة في HAR:
1. `GET models-filter/episode-students?episodes_ids={eid}` — طلاب الحلقة.
2. `GET students/{sid}/profile/episodes/{eid}/plan` — خطة الطالب ← **`std_level_id`** + المواضع.
3. `GET students/{sid}/calendar?episode_id={eid}` — أيام التسميع.
4. `GET students/{sid}/history-lessons?date_of={date}` — أركان مسجّلة مسبقاً (تعديل vs جديد).
5. `GET students/{sid}/get-lesson-complete?episode_id=&std_level_id=&pillar_id=&from_verse_id=&student_id=` ← منها **`to_verse_id`**.
6. `PUT students/{sid}/change-recite` ← الحفظ.

---

## 5) الاكتشاف المحوري: `verse_id` = الرقم الكوني للآية ✅

### السؤال الأصلي
> Supabase يخزّن أرقام آيات، وإنجازي يستخدم `verse_id`. هل الترقيم متطابق؟ هل نحتاج جدول وسيط؟

### الإجابة
**لا يوجد endpoint منفصل لجدول الآيات في إنجازي**، وجُرِّبت كل المسارات:
`/surahs`, `/verses`, `/quran/surahs`, `/institution_panel/surahs`,
`/institution_panel/verses`, `/models-filter/verses`...
كلها رجعت الاستجابة الافتراضية لـ Laravel (`"message":"app is running"`) = مسارات غير موجودة.

**لكن السبب أنك لست بحاجة إليه:** رقم `verse_id` = **الرقم الكوني للآية في المصحف (1..6236)**،
وهو **مطابق تماماً** لأرقام الآيات المخزّنة في Supabase.

### الدليل القاطع (من بيانات Supabase الحقيقية — ~2600 صف)

| الفحص | النتيجة |
|------|---------|
| مدى القيم | من `1` إلى `6236` (بالضبط مدى آيات المصحف) |
| قيم تتجاوز 286 (أطول سورة: البقرة) | **13,913 قيمة** ← تأكيد أنها أرقام **كونية** وليست ضمن-سورة |
| قيم تتجاوز 6236 | **0** (نطاق سليم 100%) |

### دليل إضافي من بنية `plan` في إنجازي
```
plan.data.verses[]:
  start_surah_id: 1,  start_verse_id: 1    (الفاتحة، الآية 1)
  end_surah_id: 114,  end_verse_id: 6236   (الناس، آخر آية)

plan.data.pillars[].current_lesson.from:
  surah_id: 97, surah_name: "القدر", verse_order: 1, verse_id: 6126
  ✓ سورة القدر تبدأ فعلاً عند الآية الكونية 6126
```

### الترجمة: الترابط مباشر بلا جدول وسيط

| Supabase (`quran_recitation`) | → إنجازي |
|-------------------------------|----------|
| `lesson_start_aya` | `from_verse_id` (pillar 2) |
| `lesson_end_aya` | `to_verse_id` (pillar 2) |
| `review_start_aya` | `from_verse_id` (pillar 3) |
| `review_end_aya` | `to_verse_id` (pillar 3) |
| `side_start_aya` | `from_verse_id` (pillar 4) |
| `side_end_aya` | `to_verse_id` (pillar 4) |
| `recite_date` | `date_of` |
| `student_id` (UUID) → `enjazi_id` | `student_id` |
| `halqa_id` → `enjazi_id` | `episode_id` |
| `*_grade` (نصي) | `mistakes` (عبر `grade_to_mistakes`) |
| `synced_at IS NULL` | = طابور المزامنة |
| `sync_error` | تسجيل الخطأ عند الفشل |

### 🔍 ملاحظة هامة: اتجاه المراجعة معكوس
في بيانات Supabase توجد صفوف `start > end`:
- الحفظ: 143 صفًا
- **المراجعة: 483 صفًا** ← الأكثر
- التثبيت: 60 صفًا

هذا **طبيعي ومقصود**: إنجازي يُسمِع المراجعة **بالاتجاه المعاكس** (مؤكَّد في HAR:
مراجعة `from=6126 → to=6104`). لذلك تُنقل القيم **كما هي** دون تطبيع `start<=end`.

---

## 6) الحالة الراهنة للكود

وحدة `enjazi/api/recitation.py` مبنية أصلاً ومطابقة للـ HAR 100% (ترتيب الحقول + طريقة الـ body):
- `change_recite` (الـ PUT) ✅
- `get_plan`, `get_lesson_complete`, `get_history_lessons`, `get_episode_students` ✅
- `build_lesson`, `grade_to_mistakes`, `make_frond_id` ✅
- الثوابت `PILLAR_LESSON=2`, `PILLAR_REVIEW=3`, `PILLAR_SIDE=4` ✅
- خريطة الدرجات `GRADE_TO_MISTAKES` (ممتاز/جيد جدا/جيد/لم يسمع) ✅

### ملاحظات تصحيحية دقيقة
- **`frond_id` ليس hex**: الجزء العشوائي في HAR (`31e21t6de9a`, `rnrnu3n8ht`) يحوي حروفاً خارج hex
  (`t,r,n,u,h`). الكود الحالي يستخدم `secrets.token_hex(6)`. الخادم غالباً لا يتحقق من تنسيقه،
  لكن للدقّة يُفضَّل توليده **أبجدي-رقمي** (مثل `secrets.token_urlsafe` مقتطع، أو اختيار عشوائي من `[a-z0-9]`).

---

## 7) مصدر `lesson_id` — ✅ حُلّ (فحص حيّ 2026-07-09)

فُحصت جميع endpoints القراءة حيّاً بردودها الكاملة (المصدر: مِسبار مباشر على API إنجازي):

| المصدر | يحوي `lesson_id`؟ |
|--------|-------------------|
| `plan` | ❌ لا (فقط `current_lesson.from/to`) |
| `get-lesson-complete` | ❌ لا (فقط `{from_verse_id, to_verse_id, level_finished}`) |
| `history-lessons` — يوم **بلا** تسميع | ❌ `lessons: []` فارغة، `attend_type:"not-attend"` |
| `history-lessons` — يوم **مُسمَّع** | ✅ **نعم** — كل عنصر `lessons[]` يحمل `lesson_id` |

**الخلاصة:** `lesson_id` **مفتاح أساسي يولّده الخادم عند أول حفظ**. لا يوجد endpoint يولّده مسبقاً.

### تمييز «جديد» عن «تعديل» (حاسم للمزامنة)
- الاختبار في `TSM3E.txt` كان **تعديلاً** لا تسميعاً جديداً: في `calendar` يوم `2026-07-02` = `attend, code:2`
  (مُسمَّع مسبقاً). فاللوحة جلبت `lesson_id` القائم من `history-lessons` وأعادت إرساله مع `action:1`.
- خريطة إجراءات `calendar.actions`: **`1=MODIFY_RECITE`، `2=CANCEL_RECITE`، `3=ADD_NON_RECITE`، `4=ADD_RECITED`**.
- **حالتنا كلها «جديد»** (لم يُدفع أي تسميع بعد) ⇒ المتوقع `action:4` (ADD_RECITED) بلا `lesson_id` قائم.

> **النقطة الوحيدة غير المؤكَّدة تجريبياً:** شكل payload التسميع **الجديد** بالضبط (هل `lesson_id:0`/محذوف؟
> هل `action:4`؟). لم يظهر في الـ HAR لأن الاختبار كان تعديلاً. تُحسم باختبار كتابة **واحد مضبوط** (طالب/يوم
> تجريبي ثم CANCEL_RECITE للتنظيف) — يتطلب إذن المستخدم لأنه تعديل على نظام إنجازي الإنتاجي.

### اكتشافات مصاحبة
- **`std_level_id` تاريخي:** داخل `history-lessons.lessons[]` كان `std_level_id=212256` بينما مستوى الخطة
  الحالي `93965` — أي أنه مستوى الطالب **وقت** ذلك التسميع. للمزامنة اليومية (days_back=1) نستخدم
  `std_level_id` الحالي من `plan` (التاريخ ≈ اليوم فيتطابق).
- **درجة `إعادة` غير مُغطّاة:** قيم الدرجات الفعلية في Supabase (3481 صف):
  `ممتاز 5316` / `جيد جدا 2000` / `لم يسمع 1226` / `جيد 700` / `إعادة 476` / `null 725`.
  ⚠️ **`إعادة` (476) غير موجودة في `GRADE_TO_MISTAKES`** ⇒ تُعامَل الآن خطأً كـ«لا تُسمَّع» وتُتخطّى بصمت.
  يجب إضافتها (إعادة = تسميع ضعيف يتطلب إعادة، تُقابل أسوأ درجة ناجحة أو معالجة خاصة).
- **حجم الطابور:** `2443` صفاً مربوطاً (طالب+حلقة لهما `enjazi_id`) وغير مُزامَن — الـ backlog التاريخي.

---

## 8) مخطط بناء المزامنة (بعد حل `lesson_id`)

الـ job المخطّط `backend/jobs/sync_recitation.py` (بنمط `sync_register_students.py`):
1. يقرأ صفوف `quran_recitation` حيث `synced_at IS NULL`، والطالب والحلقة مربوطان (`enjazi_id` موجود).
2. لكل صف، يجلب `std_level_id` من `plan` مرة واحدة للطالب.
3. لكل ركن مُسمَّع (lesson/review/side) حيث الدرجة ≠ «لم يسمع»:
   - يحوّل `*_start_aya`/`*_end_aya` مباشرة إلى `from_verse_id`/`to_verse_id`.
   - يحوّل الدرجة إلى `mistakes` عبر `grade_to_mistakes`.
   - يبني عنصر `lessons[]` عبر `build_lesson`.
4. `PUT change-recite`.
5. عند النجاح: `synced_at = now()`؛ عند الفشل: كتابة `sync_error` لإعادة المحاولة لاحقاً.
6. تسجيل النوع `sync_recitation` في المجدول + راوتر المهام.

---

## ملخّص التنفيذي
| البند | الحالة |
|------|--------|
| endpoint الحفظ (`change-recite`) | ✅ مؤكَّد ومطابق للكود |
| خريطة الدرجات → أخطاء | ✅ جاهزة |
| أرقام الأركان (2/3/4) | ✅ مؤكَّدة |
| **خريطة الآية ↔ verse_id** | ✅ **حُلّت — الترقيم متطابق (كوني 1..6236)، لا جدول وسيط** |
| `std_level_id` | ✅ من `plan` (الحالي) |
| `lesson_id` | ✅ **حُلّ** — يولّده الخادم عند الحفظ؛ حالتنا كلها «جديد» فلا نجلبه |
| شكل payload التسميع **الجديد** (`action`/`lesson_id:0`) | 🟡 يُحسم باختبار كتابة واحد مضبوط (يتطلب إذن) |
| درجة `إعادة` | 🔴 غير مُغطّاة في الخريطة — يجب إضافتها |
