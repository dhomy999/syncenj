# تقرير تدفّق التحضير (Attendance Flow) — تطبيق إنجازي للمعلم

> **الهدف:** توثيق مسار تحضير طلاب الحلقة واعتماده لغرض الأتمتة والتكامل مع نظام خارجي.
> **المصدر:** تحليل `libapp.so` (إصدار 2.0.34) + اختبار حيّ على الحساب `2366680136`.
> **Base URL:** `https://api.injaazy.com/apps/v1/`
> **تاريخ التوثيق:** 2026-07-09

---

## 1. ملخص تنفيذي

- تحضير طلاب الحلقة واعتماده يتم عبر **`POST teacher/episode/attendece`** (وليس `attendecep` — الأخير خطأ مطبعي في السلاسل المستخرجة).
- الحلقة تُمرَّر عبر **ترويسة** `x-episode-id` وليس في المسار أو الـ query string.
- الاستدعاء **يعتمد/يُنهي جلسة التحضير** ويطبّق **غياباً تلقائياً** على بعض الطلاب — ليس تحديثاً إضافياً لطالب واحد. راجع [قسم الأثر الجانبي](#7-أثر-جانبي-مهم).

---

## 2. المصادقة (مطلوبة قبل أي استدعاء)

**`POST auth/login`**

```json
{
  "username": "2366680136",
  "password": "********",
  "country_id": 1
}
```

- `country_id` **إلزامي** — بدونه يرجع `422: حقل country id مطلوب`.
- الاستجابة تُعيد `data.access_token` يُستخدم كـ `Authorization: Bearer <token>`.

### الترويسات العامة

```http
Authorization: Bearer {access_token}
Content-Type: application/json
Accept: application/json
```

---

## 3. نقاط النهاية المستخدمة في تدفّق التحضير

| # | Method | Endpoint | الترويسات الخاصة | الوظيفة |
|---|--------|----------|------------------|---------|
| 1 | `POST` | `auth/login` | — | تسجيل الدخول والحصول على التوكن |
| 2 | `GET` | `teacher/episodes-listing/active` | — | قائمة الحلقات النشطة (لاختيار الحلقة) |
| 3 | `GET` | `teacher/episode/students` | `x-episode-id` | كشف طلاب الحلقة + حالة التحضير الحالية |
| 4 | `POST` | `teacher/episode/attendece` | `x-episode-id` | **إرسال/اعتماد التحضير** |

> **ملاحظة:** `teacher/episode/attendecep` (بحرف p) لا يقبل `POST` (يرجع `405`)، و`GET` عليه يرجع فحص صحّة الخادم فقط. المسار الصحيح للإرسال هو `attendece`.

---

## 4. جلب الحلقات النشطة

**`GET teacher/episodes-listing/active`**

مقتطف من الاستجابة:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 3508,
        "name": "...",
        "status": true,
        "teacher": { "id": 70953, "name": "..." },
        "institution": { "id": 539, "name": "..." },
        "period": { "id": 20, "name": "..." },
        "students_count": 45,
        "progress_indicator": 0
      }
    ]
  }
}
```

- `data.items[].id` = رقم الحلقة المستخدم لاحقاً في ترويسة `x-episode-id`.

---

## 5. جلب طلاب الحلقة وحالة التحضير

**`GET teacher/episode/students`**
الترويسة الإلزامية: `x-episode-id: {episode_id}` — بدونها يرجع `422: x-episode-id header is required`.

مقتطف من الاستجابة:

```json
{
  "success": true,
  "data": {
    "attendece_counts": [
      { "attend_type": "attend",  "total": 0 },
      { "attend_type": "late",    "total": 0 },
      { "attend_type": "excused", "total": 0 },
      { "attend_type": "absent",  "total": 0 }
    ],
    "attended_today": false,
    "is_work_today": true,
    "items": [
      {
        "id": 191954,
        "name": "...",
        "username": "2307176293",
        "pillars_count": 2,
        "pillars": [
          { "pillar_id": 2, "done": false, "state": "PENDING" },
          { "pillar_id": 3, "done": false, "state": "PENDING" }
        ],
        "attendece": "not-attend",
        "program_type": 4,
        "is_edu": false
      }
    ]
  }
}
```

### الحقول المهمة
| الحقل | الوصف |
|-------|-------|
| `items[].id` | **student_id** المستخدم في حمولة الإرسال |
| `items[].attendece` | حالة التحضير الحالية: `not-attend` (لم يُحضَّر) / `attend` / `late` / `excused` / `absent` |
| `attended_today` | هل اعتُمد تحضير اليوم؟ |
| `is_work_today` | هل اليوم يوم عمل للحلقة؟ |
| `attendece_counts` | إجمالي كل نوع تحضير |

---

## 6. إرسال / اعتماد التحضير

**`POST teacher/episode/attendece`**
الترويسة الإلزامية: `x-episode-id: {episode_id}`

### الحمولة

```json
{
  "students": [
    { "student_id": 191954, "attend_type": "attend" }
  ]
}
```

### قواعد التحقق (مُكتشفة من أخطاء 422)
| الحقل | القاعدة |
|-------|---------|
| `students` | مصفوفة **إلزامية** |
| `students[].student_id` | **إلزامي** (= `items[].id` من كشف الطلاب) |
| `students[].attend_type` | **إلزامي** — القيم: `attend` / `late` / `excused` / `absent` |

### الاستجابة عند النجاح

```json
{
  "success": true,
  "data": null,
  "status": 200,
  "message": "تم تسجيل حالة التحضير بنجاح"
}
```

بعد الإرسال يصبح `attended_today = true` في كشف الطلاب.

---

## 7. أثر جانبي مهم

الاستدعاء **ليس تحديثاً إضافياً (incremental)** لطالب واحد، بل يبدو أنه **يعتمد جلسة التحضير كاملة**:

- **قبل الإرسال:** جميع العدّادات = 0، وكل الطلاب `not-attend`.
- **بعد إرسال طالب واحد فقط كـ `attend`:** أصبح العدّاد `attend: 1` **و** `absent: 4` — أي أن الخادم سجّل **طلاباً آخرين كـ"غائب" تلقائياً**.

### التوصية للأتمتة
أرسل **جميع** طلاب الحلقة بحالاتهم الصحيحة في نفس الطلب (`students[]` كاملة)، لا طالباً واحداً، لتجنّب غياب تلقائي غير مقصود على البقية.

```json
{
  "students": [
    { "student_id": 191954, "attend_type": "attend" },
    { "student_id": 85881,  "attend_type": "attend" },
    { "student_id": 85871,  "attend_type": "excused" }
    // ... بقية طلاب الحلقة
  ]
}
```

---

## 8. جدول رموز الاستجابة المُلاحَظة أثناء الاكتشاف

| الحالة | المعنى في هذا السياق |
|--------|----------------------|
| `200` | نجاح التسجيل |
| `422` | حقل مطلوب مفقود (`country_id` / `students` / `x-episode-id` ...) |
| `405` | Method غير مسموح (مثلاً `POST` على `attendecep`) |
| `502` / `400` | مسار غير مطابق (fallback خادم) |

---

## 9. مثال متكامل (cURL)

```bash
# 1) تسجيل الدخول
TOKEN=$(curl -s -X POST "https://api.injaazy.com/apps/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"2366680136","password":"********","country_id":1}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['data']['access_token'])")

# 2) الحلقات النشطة
curl -s "https://api.injaazy.com/apps/v1/teacher/episodes-listing/active" \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/json"

# 3) طلاب الحلقة (EP = رقم الحلقة)
EP=3508
curl -s "https://api.injaazy.com/apps/v1/teacher/episode/students" \
  -H "Authorization: Bearer $TOKEN" -H "x-episode-id: $EP"

# 4) اعتماد التحضير
curl -s -X POST "https://api.injaazy.com/apps/v1/teacher/episode/attendece" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "x-episode-id: $EP" \
  -d '{"students":[{"student_id":191954,"attend_type":"attend"}]}'
```

---

## 10. سجل الاختبار الحيّ (2026-07-09)

- **الحساب:** `2366680136` (id 85319، بصلاحية إشرافية ترى حلقات عدّة معلّمين في مؤسسة 539).
- **الحلقة:** id `3508` (45 طالباً).
- **الطالب:** id `191954` (username `2307176293`) → سُجِّل `attend`.
- **النتيجة:** `200 — تم تسجيل حالة التحضير بنجاح`، `attended_today = true`.
- **أثر جانبي:** ظهر `absent: 4` تلقائياً على طلاب آخرين (راجع القسم 7). يلزم التراجع اليدوي لإعادة الحالة.

### الطلاب المطلوب التراجع عنهم في الحلقة 3508
| student_id | username | الحالة بعد الاختبار |
|------------|----------|---------------------|
| 191954 | 2307176293 | attend |
| 85881 | 1132010370 | absent |
| 85871 | 2513726410 | absent |
| 85330 | 1132425420 | absent |
| (الرابع) | — | absent (في صفحة أخرى من الكشف) |

> لم تُكتشف بعد نقطة "مسح/إلغاء التحضير" (الأنواع المتاحة كلها تسجيل حالة، لا حذف). يُنصح بالتراجع من واجهة التطبيق، أو استكمال البحث في `libapp.so` عن نقطة إعادة الضبط/الحذف.

---

*تم إعداد هذا التقرير بتحليل `libapp.so` واختبار حيّ على الـ API — إصدار التطبيق 2.0.34.*
