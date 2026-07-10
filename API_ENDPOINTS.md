# API Documentation - تطبيق إنجازي للمعلم

> **المصدر:** تحليل ملف `libapp.so` المستخرج من `split_config.arm64_v8a.apk`  
> **إصدار التطبيق:** 2.0.34  
> **Package:** `com.injaazy.teacherapp.injaazy`

---

## معلومات الاتصال

| | |
|---|---|
| **Base URL** | `https://api.injaazy.com/apps/v1/` |
| **WebSocket** | `wss://ws.injaazy.com` |
| **Dashboard** | `https://dashboard.injaazy.com` |
| **Quran Files** | `https://quranfiles.injaazy.com` |
| **Country Flags** | `https://api.injaazy.com/assets/flags/{country_code}.png` |

---

## Headers المتوقعة

```http
Authorization: Bearer {token}
Content-Type: application/json
Accept: application/json
```

---

## 1. AUTH - المصادقة

**Base:** `https://api.injaazy.com/apps/v1/auth/`

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `auth/login` | تسجيل الدخول |
| `POST` | `auth/logout` | تسجيل الخروج |
| `POST` | `auth/refresh` | تجديد التوكن (Refresh Token) |
| `POST` | `auth/check_username` | التحقق من وجود اسم المستخدم |
| `POST` | `auth/otp/verify` | التحقق من رمز OTP |
| `POST` | `auth/password/send-otp` | إرسال OTP لاستعادة كلمة المرور |
| `POST` | `auth/password/rest` | إعادة تعيين كلمة المرور |
| `POST` | `auth/password/updatei` | تحديث كلمة المرور |

### مثال: تسجيل الدخول
```http
POST https://api.injaazy.com/apps/v1/auth/login
Content-Type: application/json

{
  "username": "...",
  "password": "..."
}
```

---

## 2. GENERAL - عام

**Base:** `https://api.injaazy.com/apps/v1/general/`

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `general/fetch-countries` | جلب قائمة الدول |
| `GET` | `general/fetch-nationalites` | جلب قائمة الجنسيات |
| `GET` | `general/fetch-sour` | جلب قائمة السور |
| `GET` | `general/about-us` | معلومات عن التطبيق |
| `GET` | `general/policy` | سياسة الخصوصية والشروط |

---

## 3. TEACHER - المعلم

**Base:** `https://api.injaazy.com/apps/v1/teacher/`

### 3.1 الملف الشخصي والإعدادات

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `teacher/profile` | جلب بيانات الملف الشخصي |
| `PUT` / `PATCH` | `teacher/profile` | تحديث الملف الشخصي |
| `GET` | `teacher/settings` | جلب الإعدادات |
| `PUT` | `teacher/settings` | تحديث الإعدادات |
| `GET` | `teacher/statics` | إحصائيات المعلم العامة |
| `DELETE` | `teacher/delete-my-account` | حذف الحساب نهائياً |
| `POST` | `teacher/contact-us` | إرسال رسالة تواصل |

### 3.2 الإشعارات

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `teacher/notifications` | جلب كل الإشعارات |
| `GET` | `teacher/notifications/unread-counts` | عدد الإشعارات غير المقروءة |
| `POST` | `teacher/notifications/mark-all-as-read` | تعليم كل الإشعارات كمقروءة |

### 3.3 الحلقات (Episodes)

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `teacher/episodes-listing/all` | جلب كل الحلقات |
| `GET` | `teacher/episodes-listing/active` | الحلقات النشطة فقط |
| `GET` | `teacher/episodes-listing/suspended` | الحلقات الموقوفة |
| `GET` | `teacher/episodes-listing/not-worked` | الحلقات غير المعمول بها |
| `GET` | `teacher/episodes/statistics` | إحصائيات الحلقات |
| `GET` | `teacher/episode/` | تفاصيل حلقة معينة |
| `POST` | `teacher/episode/activate` | تفعيل حلقة |
| `PUT` | `teacher/episode/update-setting` | تحديث إعدادات الحلقة |
| `GET` | `teacher/episode/form-data/` | بيانات نموذج الحلقة |
| `GET` | `teacher/episode/students` | طلاب الحلقة |
| `GET` | `teacher/episode/recite-cards` | بطاقات تسميع الحلقة |
| `GET` | `teacher/episode/my-points` | نقاط المعلم في الحلقة |
| `GET` | `teacher/episode/from-verse-permissions` | صلاحيات الآية الابتدائية |
| `GET` | `teacher/episode/attendecep` | حضور الحلقة |

### 3.4 الاختبارات (Exams)

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `teacher/episode/exams` | اختبارات الحلقة |
| `GET` | `teacher/episode/exams/scheduling/exams-groups` | مجموعات جدولة الاختبارات |
| `POST` | `teacher/exams/schedule/bulk` | جدولة اختبارات متعددة دفعة واحدة |
| `GET` | `teacher/exams/scheduled/all-episodes` | الاختبارات المجدولة لكل الحلقات |

### 3.5 الطلاب (Students)

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `teacher/students` | قائمة الطلاب |
| `GET` | `teacher/students/init-form` | بيانات نموذج إضافة طالب |
| `POST` | `teacher/students/add-user` | إضافة طالب جديد |
| `POST` | `teacher/students/check-username` | التحقق من اسم مستخدم الطالب |
| `GET` | `teacher/students/lesson-actions` | إجراءات الدرس للطلاب |
| `GET` | `teacher/students/plan-management/constants` | ثوابت إدارة خطة الطالب |

### 3.6 الحضور والانصراف (Attendance)

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `teacher/attendance/check-in` | تسجيل الحضور |
| `POST` | `teacher/attendance/check-out` | تسجيل الانصراف |
| `GET` | `teacher/attendance/active-session` | الجلسة النشطة الحالية |
| `GET` | `teacher/attendance/records` | سجل الحضور |
| `GET` | `teacher/attendance/units` | وحدات الحضور |
| `POST` | `teacher/attendance/absence-request` | طلب غياب |
| `GET` | `teacher/attendance/my-requests` | طلباتي (غياب/تأخر) |
| `POST` | `teacher/attendance/validate-device` | التحقق من الجهاز |
| `POST` | `teacher/attendance/validate-location` | التحقق من الموقع الجغرافي |
| `POST` | `teacher/attendance/validate-subscription` | التحقق من الاشتراك |
| `POST` | `teacher/attendance/device-binding-request` | طلب ربط الجهاز |

### 3.7 المحادثات (Chats)

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `teacher/chats` | قائمة المحادثات |
| `WS` | `wss://ws.injaazy.com/ws?token={token}` | اتصال WebSocket للمحادثات المباشرة |

---

## 4. STUDENT - الطالب

**Base:** `https://api.injaazy.com/apps/v1/`

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `POST` | `approve-add-user` | قبول طلب إضافة مستخدم |
| `POST` | `reject-add-user` | رفض طلب إضافة مستخدم |
| `POST` | `join-episode` | الانضمام لحلقة |
| `POST` | `suspend` | إيقاف |

---

## 5. LESSON - الدرس

**Base:** `https://api.injaazy.com/apps/v1/`

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `lessons` | قائمة الدروس |
| `GET` | `history-lessons` | سجل الدروس السابقة |
| `POST` | `update-next-lesson` | تحديث الدرس القادم |
| `POST` | `change-starting` | تغيير نقطة البداية |
| `POST` | `change-plan` | تغيير الخطة |
| `POST` | `remind-me-later` | تذكيري لاحقاً |
| `POST` | `update` | تحديث |

---

## 6. RECITATION - التسميع

**Base:** `https://api.injaazy.com/apps/v1/`

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `recite-cards` | بطاقات التسميع |
| `POST` | `sync-recite-cards` | مزامنة بطاقات التسميع |
| `POST` | `cancel-recite` | إلغاء التسميع |
| `POST` | `extra-recite` | تسميع إضافي |
| `PUT` | `extra-recite/modify` | تعديل تسميع إضافي |
| `DELETE` | `extra-recite/cancel` | إلغاء تسميع إضافي |
| `GET` | `read` | قراءة |

---

## 7. PLAN - الخطة

**Base:** `https://api.injaazy.com/apps/v1/`

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `plan` | جلب الخطة |
| `GET` | `plan-management` | إدارة الخطة |
| `POST` | `plan-management/init` | تهيئة الخطة |

---

## 8. POINTS - النقاط

**Base:** `https://api.injaazy.com/apps/v1/`

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `points` | جلب النقاط |
| `POST` | `points/add_points` | إضافة نقاط |

---

## 9. REPORTS - التقارير

**Base:** `https://api.injaazy.com/apps/v1/`

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `reports/filter-labels` | تصنيفات التقارير |
| `GET` | `reports/pages-details` | تفاصيل صفحات التقرير |

---

## 10. ATTENDANCE (شاملة)

**Base:** `https://api.injaazy.com/apps/v1/`

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `attendece` | الحضور |

---

## 11. STATICS - الإحصائيات

| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| `GET` | `statics` | إحصائيات عامة |

---

## 12. WebSocket - الاتصال المباشر

```
wss://ws.injaazy.com/ws?token={JWT_TOKEN}
```

يُستخدم لـ:
- المحادثات الفورية بين المعلم والطالب
- الإشعارات الفورية

---

## 13. Static Assets - الملفات الثابتة

| URL | الوصف |
|-----|-------|
| `https://api.injaazy.com/assets/flags/{cc}.png` | صور أعلام الدول (`sa`, `ae`, `eg`, ...) |
| `https://quranfiles.injaazy.com` | ملفات القرآن الكريم (صوت/صور) |
| `https://dashboard.injaazy.com/register` | تسجيل حساب جديد عبر Dashboard |

---

## ملاحظات

- جميع الـ endpoints تستخدم `HTTPS`
- المصادقة عبر `Bearer Token` في الـ Header
- بعض الـ endpoints تحتوي على `{id}` في المسار لم يُكتشف بعد (تُضاف ديناميكياً)
- اسم الخطأ في بعض الـ endpoints قد يكون typo في الكود الأصلي:
  - `auth/password/rest` (قد تكون `reset`)
  - `teacher/episode/attendecep` (قد تكون `attendance`)
  - `teacher/attendance/attendecep` (نفس الملاحظة)

---

*تم استخراج هذه المعلومات بتحليل ملف `libapp.so` من التطبيق - إصدار 2.0.34*
