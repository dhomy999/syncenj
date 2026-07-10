# مشروع: تقارير الطلاب الجماعية — إنجازي
> وثيقة متكاملة لتنفيذ مشروع مستقل تماماً

---

## 1. نظرة عامة

### الهدف
بناء أداة ويب تتيح لمشرف المنشأة **توليد تقارير أداء جميع طلاب حلقة** بنقرة واحدة، بدلاً من فتح تقرير كل طالب على حدة كما في لوحة إنجازي الرسمية.

### ما يفعله المشروع
1. المستخدم يختار: المنشأة → الحلقة → نوع الفترة (يومي/أسبوعي) → نطاق التاريخ
2. النظام يجلب قائمة جميع الطلاب في الحلقة
3. يستدعي API التقرير لكل طالب بالتوازي
4. يعرض جدولاً موحداً بكل بيانات الأداء
5. يتيح تصدير الجدول كـ Excel أو CSV

### المستخدم المستهدف
مشرف منشأة تحفيظ قرآن على نظام إنجازي (injaazy.com)

---

## 2. التقنيات المستخدمة

| الطبقة | التقنية |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript |
| Styling | Tailwind CSS |
| Backend | Python 3.11+ / FastAPI |
| HTTP Client | `curl_cffi` (يتجاوز حماية Cloudflare) |
| تصدير Excel | `openpyxl` |
| Package Manager | `uv` (Python) / `npm` (Node) |

---

## 3. بنية الملفات

```
student-reports/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── routers/
│   │   ├── auth.py              # token management
│   │   ├── data.py              # institutions, episodes, students
│   │   └── reports.py           # report generation endpoints
│   ├── enjazi/
│   │   ├── client.py            # HTTP client wrapper (curl_cffi)
│   │   ├── auth.py              # login + token cache
│   │   └── api/
│   │       ├── base.py          # BaseAPI class
│   │       ├── institutions.py  # institutions + episodes
│   │       ├── students.py      # students list per episode
│   │       └── reports.py       # student report fetcher
│   ├── config/
│   │   └── settings.py          # credentials + constants
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # redirect to /reports
│   │   └── reports/
│   │       └── page.tsx         # الصفحة الرئيسية
│   ├── components/
│   │   ├── SelectionForm.tsx    # نموذج الاختيار
│   │   ├── ReportTable.tsx      # جدول النتائج
│   │   └── ExportButton.tsx     # زر التصدير
│   └── package.json
└── README.md
```

---

## 4. إعداد المصادقة (Auth)

### بيانات الدخول
يتم تخزينها في `config/settings.py` أو متغيرات البيئة:

```python
USERNAME = "your_username"
PASSWORD = "your_password"
BASE_URL = "https://api.injaazy.com/front_app_api/v1"
```

### تسلسل المصادقة
```
POST /auth/login
Body: { "username": "...", "password": "...", "device_name": "web" }

Response:
{
  "data": {
    "token": "<USER_ID>|<TOKEN_REDACTED>",
    "user": { "id": 1545, ... }
  }
}
```

### الـ Token
- يُحفظ في الذاكرة (لا يحتاج تجديد في كل طلب)
- يُرسل في كل طلب كـ: `Authorization: Bearer {token}`

---

## 5. الـ Headers المطلوبة

كل طلب للـ API يحتاج هذه الـ headers:

```python
{
    "accept": "*/*",
    "authorization": f"Bearer {token}",
    "access-control-allow-origin": "*",
    "x-behalf-id": str(user_id),      # رقم المستخدم المسجل (1545)
    "x-behalf-on": "institution",
    "x-current-role": "3",
    "x-institution-id": str(institution_id),  # يتغير حسب المنشأة المختارة
    "x-requested-with": "XMLHttpRequest",
}
```

**ملاحظة:** `x-institution-id` يتغير مع كل منشأة مختارة.

---

## 6. Endpoints المستخدمة

### 6.1 قائمة المنشآت
```
GET /corporation_panel/institutions/list?limit=200

Response:
{
  "data": {
    "items": [
      { "id": 118, "name": "مقرأة قباء الرجالية", "center_id": 5 },
      ...
    ]
  }
}
```

### 6.2 قائمة الحلقات لمنشأة
```
GET /institution_panel/episodes/list?limit=200
Headers: x-institution-id: {institution_id}

Response:
{
  "data": {
    "items": [
      { "id": 8736, "name": "أ.عبدالعزيز علي / مقرأة قباء / رجال", "period": "العصر" },
      ...
    ]
  }
}
```

### 6.3 طلاب الحلقة
```
GET /institution_panel/models-filter/episode-students?episodes_ids={episode_id}&limit=10000
Headers: x-institution-id: {institution_id}

Response:
{
  "data": {
    "items": [
      { "id": 170046, "name": "محمد عبدالواحد", "username": "1234567890" },
      ...
    ]
  }
}
```

### 6.4 تقرير طالب واحد ✱ (الأهم)
```
GET /institution_panel/reports/students/{student_id}
    ?episode_id={episode_id}
    &period_range={W|D}
    &date_of={YYYY/MM/DD-YYYY/MM/DD}
    &student_id={student_id}
Headers: x-institution-id: {institution_id}

أمثلة:
  period_range=W  → تقرير أسبوعي
  period_range=D  → تقرير يومي
  date_of=2026/04/12-2026/04/18  → من الأحد إلى السبت
  date_of=2026/04/14-2026/04/14  → يوم واحد فقط
```

---

## 7. هيكل استجابة تقرير الطالب

```json
{
  "success": true,
  "data": {
    "student": {
      "id": 170046,
      "name": "محمد عبدالواحد",
      "episode_name": "أ.عبدالعزيز علي / مقرأة قباء / رجال",
      "episode_period_name": "العصر",
      "institution_name": "مقرأة قباء الرجالية",
      "progress": 127,
      "level_name": "التزام حال الحضور",
      "program_name": "حفظ حسب خطة التسميع",
      "start_date": "2025-12-16",
      "filter_range": "الأحد 12 - الثلاثاء 14",
      "report_title": "التقرير الأسبوعي",
      "pages_summary": {
        "total_pages": 14.0,
        "completed": 17.75,
        "remaining": 0
      }
    },

    "rating": {
      "rate": 10,
      "grade": "ممتاز"
    },

    "saved_pages": {
      "required": 1.3,
      "recite": 1.3,
      "rating": 100,
      "history_lessons": [
        {
          "text": "من سورة التحريم 5 إلى سورة التحريم 11",
          "pages_count": 1.3
        }
      ],
      "pages_numbers": "560-561"
    },

    "revision_pages": {
      "required": 8.1,
      "recite": 10,
      "rating": 123
    },

    "attendece": {
      "real_attend_count": 2,
      "real_episode_count": 2,
      "rate": 100,
      "attend": 2,
      "late": 0,
      "absent": 0,
      "excused": 0
    },

    "date_range": {
      "from_date": "2026-04-12",
      "to_date": "2026-04-14"
    },

    "ranges": [
      {
        "date_key": "abc123",
        "from_date": "2026-04-14",
        "to_date": "2026-04-14",
        "display": "الثلاثاء 14"
      }
    ]
  }
}
```

---

## 8. Backend — تفاصيل التنفيذ

### 8.1 `enjazi/client.py`
```python
from curl_cffi import requests as cffi_requests

class EnjaziClient:
    def __init__(self):
        self.session = cffi_requests.Session(impersonate="chrome110")
        self.base_url = "https://api.injaazy.com/front_app_api/v1"
        self.token: str | None = None
        self.user_id: int | None = None

    def __enter__(self): return self
    def __exit__(self, *_): self.session.close()

    def get(self, path, **kwargs):
        return self.session.get(self.base_url + path, **kwargs)

    def post(self, path, **kwargs):
        return self.session.post(self.base_url + path, **kwargs)
```

### 8.2 `enjazi/auth.py`
```python
def login(client) -> str:
    resp = client.post("/auth/login", json={
        "username": settings.USERNAME,
        "password": settings.PASSWORD,
        "device_name": "web"
    })
    data = resp.json()["data"]
    client.token = data["token"]
    client.user_id = data["user"]["id"]
    return client.token
```

### 8.3 `enjazi/api/base.py`
```python
class BaseAPI:
    def __init__(self, client):
        self._client = client

    def _headers(self, institution_id: str) -> dict:
        return {
            "accept": "*/*",
            "authorization": f"Bearer {self._client.token}",
            "access-control-allow-origin": "*",
            "x-behalf-id": str(self._client.user_id),
            "x-behalf-on": "institution",
            "x-current-role": "3",
            "x-institution-id": str(institution_id),
            "x-requested-with": "XMLHttpRequest",
        }

    def _get(self, path, institution_id, params=None):
        resp = self._client.get(path, headers=self._headers(institution_id), params=params)
        resp.raise_for_status()
        return resp.json()
```

### 8.4 `enjazi/api/reports.py`
```python
class ReportsAPI(BaseAPI):

    def get_student_report(
        self,
        student_id: int,
        episode_id: int,
        institution_id: str,
        period_range: str,  # "W" or "D"
        date_of: str,       # "YYYY/MM/DD-YYYY/MM/DD"
    ) -> dict:
        return self._get(
            f"/institution_panel/reports/students/{student_id}",
            institution_id=institution_id,
            params={
                "episode_id": episode_id,
                "period_range": period_range,
                "date_of": date_of,
                "student_id": student_id,
            }
        )
```

### 8.5 `routers/reports.py` — endpoint رئيسي
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio, json
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()

class ReportRequest(BaseModel):
    institution_id: str
    episode_id: int
    period_range: str  # "W" | "D"
    date_of: str       # "2026/04/12-2026/04/18"

@router.post("/bulk/stream")
async def bulk_report_stream(payload: ReportRequest):
    """يرسل تقرير كل طالب فوراً عبر SSE."""
    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def _worker():
        with EnjaziClient() as client:
            login(client)
            students_api = StudentsAPI(client)
            reports_api = ReportsAPI(client)

            students = students_api.list_by_episode(
                payload.episode_id, payload.institution_id
            )
            total = len(students)
            asyncio.run_coroutine_threadsafe(
                queue.put({"type": "start", "total": total}), loop
            )

            for idx, student in enumerate(students, 1):
                try:
                    report = reports_api.get_student_report(
                        student_id=student["id"],
                        episode_id=payload.episode_id,
                        institution_id=payload.institution_id,
                        period_range=payload.period_range,
                        date_of=payload.date_of,
                    )
                    event = {"type": "result", "idx": idx, "total": total,
                             "student_id": student["id"],
                             "data": _extract_report(report)}
                except Exception as exc:
                    event = {"type": "result", "idx": idx, "total": total,
                             "student_id": student["id"],
                             "error": str(exc)}

                asyncio.run_coroutine_threadsafe(queue.put(event), loop)

        asyncio.run_coroutine_threadsafe(queue.put(None), loop)

    Thread(target=_worker, daemon=True).start()

    async def generate():
        while True:
            event = await queue.get()
            if event is None:
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _extract_report(raw: dict) -> dict:
    """يستخرج الحقول المهمة فقط من استجابة الـ API."""
    d = raw.get("data", {})
    student   = d.get("student", {})
    rating    = d.get("rating", {})
    saved     = d.get("saved_pages", {})
    revision  = d.get("revision_pages", {})
    attend    = d.get("attendece", {})

    lessons = saved.get("history_lessons", [])
    lesson_text = lessons[0].get("text", "") if lessons else ""

    return {
        "name":              student.get("name"),
        "episode_name":      student.get("episode_name"),
        "period":            student.get("episode_period_name"),
        "program":           student.get("program_name"),
        "level":             student.get("level_name"),
        "progress":          student.get("progress"),
        "filter_range":      student.get("filter_range"),
        # الحضور
        "attend":            attend.get("attend"),
        "late":              attend.get("late"),
        "absent":            attend.get("absent"),
        "excused":           attend.get("excused"),
        "attend_rate":       attend.get("rate"),
        # الحفظ
        "saved_required":    saved.get("required"),
        "saved_recite":      saved.get("recite"),
        "saved_rating":      saved.get("rating"),
        "saved_lesson":      lesson_text,
        "saved_pages":       saved.get("pages_numbers"),
        # المراجعة
        "rev_required":      revision.get("required"),
        "rev_recite":        revision.get("recite"),
        "rev_rating":        revision.get("rating"),
        # التقييم
        "grade_rate":        rating.get("rate"),
        "grade":             rating.get("grade"),
    }
```

---

## 9. Frontend — تفاصيل التنفيذ

### 9.1 نموذج الاختيار (`SelectionForm.tsx`)

**الحقول:**
- **المنشأة** — Dropdown يجلب من `GET /api/data/institutions`
- **الحلقة** — Dropdown يتحدث عند تغيير المنشأة من `GET /api/data/episodes?institution_id=X`
- **نوع التقرير** — Radio: أسبوعي (W) / يومي (D)
- **من تاريخ** — Date picker
- **إلى تاريخ** — Date picker (أو يُحسب تلقائياً: أسبوعي = 7 أيام)
- **زر "إنشاء التقرير"**

**تنسيق date_of:**
```typescript
const dateOf = `${fromDate.replace(/-/g, "/")}–${toDate.replace(/-/g, "/")}`;
// مثال: "2026/04/12-2026/04/18"
```

### 9.2 جدول النتائج (`ReportTable.tsx`)

**أعمدة الجدول:**

| العمود | المصدر |
|---|---|
| # | الترتيب |
| الاسم | `name` |
| الحضور | `attend` |
| الغياب | `absent` |
| التأخر | `late` |
| % الحضور | `attend_rate` |
| الحفظ المطلوب | `saved_required` |
| الحفظ الفعلي | `saved_recite` |
| % الحفظ | `saved_rating` |
| ما حفظ | `saved_lesson` |
| المراجعة المطلوبة | `rev_required` |
| المراجعة الفعلية | `rev_recite` |
| % المراجعة | `rev_rating` |
| التقييم | `grade_rate` / `grade` |
| التقدم | `progress%` |

**ألوان الصفوف:**
```typescript
// بناءً على attend_rate
attend_rate >= 90  → bg-green-50
attend_rate >= 70  → bg-yellow-50
attend_rate < 70   → bg-red-50
```

**حالات الصف:**
```typescript
type RowStatus = "pending" | "loading" | "done" | "error";
```

### 9.3 استقبال SSE في الـ Frontend
```typescript
const res = await fetch(`${API_URL}/api/reports/bulk/stream`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});

const reader = res.body!.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split("\n\n");
  buffer = lines.pop()!;
  for (const line of lines) {
    if (!line.startsWith("data: ")) continue;
    const event = JSON.parse(line.slice(6));
    if (event.type === "start") {
      // ابدأ عرض الجدول الفارغ بعدد total
    } else if (event.type === "result") {
      // حدّث الصف رقم event.idx بالبيانات
    } else if (event.type === "done") {
      // أنهِ
    }
  }
}
```

### 9.4 تصدير Excel
**Backend endpoint:**
```
POST /api/reports/export/excel
Body: { results: [...] }
Response: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

**مكتبة Python:** `openpyxl`

أو بديلاً، التصدير من الـ Frontend مباشرةً باستخدام مكتبة `xlsx` (SheetJS):
```bash
npm install xlsx
```
```typescript
import * as XLSX from "xlsx";

function exportToExcel(rows: ReportRow[]) {
  const ws = XLSX.utils.json_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "تقارير الطلاب");
  XLSX.writeFile(wb, "تقرير_الطلاب.xlsx");
}
```

---

## 10. Backend `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, data, reports

app = FastAPI(title="Student Reports API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,    prefix="/api/auth",    tags=["Auth"])
app.include_router(data.router,    prefix="/api/data",    tags=["Data"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
```

---

## 11. API Endpoints الكاملة (Backend)

| Method | Path | الوصف |
|---|---|---|
| `GET` | `/api/data/institutions` | قائمة المنشآت |
| `GET` | `/api/data/episodes?institution_id=X` | حلقات منشأة |
| `GET` | `/api/data/students?episode_id=X&institution_id=Y` | طلاب حلقة |
| `POST` | `/api/reports/bulk/stream` | تقارير جماعية (SSE) |
| `POST` | `/api/reports/bulk` | تقارير جماعية (مرة واحدة، بدون SSE) |
| `GET` | `/api/reports/student/{id}` | تقرير طالب واحد |
| `POST` | `/api/reports/export/excel` | تصدير Excel |

---

## 12. `requirements.txt`

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
curl-cffi>=0.7.0
pydantic>=2.0.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
```

---

## 13. متغيرات البيئة (`.env`)

```env
INJAZI_USERNAME=your_username
INJAZI_PASSWORD=your_password
INJAZI_BASE_URL=https://api.injaazy.com/front_app_api/v1
CORS_ORIGIN=http://localhost:3000
```

---

## 14. تشغيل المشروع

```bash
# Backend
cd student-reports
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
# يفتح على http://localhost:3000
```

---

## 15. تدفق العمل الكامل (User Flow)

```
1. المستخدم يفتح http://localhost:3000
2. يختار المنشأة من القائمة
3. تظهر قائمة الحلقات للمنشأة المختارة
4. يختار الحلقة
5. يختار: أسبوعي / يومي
6. يختار نطاق التاريخ (from - to)
7. يضغط "إنشاء التقرير"
8. يظهر الجدول فارغاً وتبدأ الصفوف تتعبأ تلقائياً
   (كل طالب ينتهي يظهر صفه مباشرةً عبر SSE)
9. بعد الانتهاء: يظهر ملخص إجمالي + زر تصدير Excel
```

---

## 16. الملاحظات التقنية المهمة

### curl_cffi — لماذا؟
إنجازي تستخدم Cloudflare. المكتبة العادية `requests` تُحجب. `curl_cffi` تُقلد Chrome browser fingerprint وتتجاوز الحماية.

```python
from curl_cffi import requests as cffi_requests
session = cffi_requests.Session(impersonate="chrome110")
```

### معالجة التزامن
الـ API لا تدعم طلبات متوازية كثيرة — استخدم طلباً واحداً في المرة مع تأخير بسيط:
```python
import time, random
time.sleep(1.5 + random.uniform(0, 1.5))  # بين كل طالب وآخر
```

### حالة الطالب بدون حضور
بعض الطلاب قد لا تظهر لهم بيانات (غائبون كلياً). التعامل مع `None` في كل حقل.

### اتجاه الصفحة
الواجهة بالكامل RTL (العربية). أضف `dir="rtl"` على الـ `<html>` tag.

---

## 17. الشاشة المتوقعة

```
┌─────────────────────────────────────────────────┐
│  تقارير الطلاب الجماعية                         │
├─────────────┬──────────────┬────────────────────┤
│ المنشأة ▼   │ الحلقة ▼     │ الفترة: ○أسبوعي ○يومي│
├─────────────┴──────────────┴────────────────────┤
│ من: [2026-04-12]  إلى: [2026-04-18]             │
│                          [إنشاء التقرير]        │
├──┬──────────┬───┬───┬───┬────┬────┬────┬────────┤
│# │ الاسم   │حض │غ  │ت  │%ح │حفظ │مراج│التقييم │
├──┼──────────┼───┼───┼───┼────┼────┼────┼────────┤
│1 │محمد ...  │ 2 │ 0 │ 0 │100%│1.3 │10  │ ممتاز  │
│2 │... ⏳    │   │   │   │    │    │    │        │
└──┴──────────┴───┴───┴───┴────┴────┴────┴────────┘
                              [تصدير Excel] [طباعة]
```

---

## 18. التحقق من صحة التنفيذ

### اختبار الـ API مباشرةً
```bash
# 1. اختبر المصادقة
curl -X POST https://api.injaazy.com/front_app_api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"...","password":"...","device_name":"web"}'

# 2. اختبر جلب طلاب حلقة
curl "https://api.injaazy.com/front_app_api/v1/institution_panel/models-filter/episode-students?episodes_ids=8736&limit=100" \
  -H "Authorization: Bearer TOKEN" \
  -H "x-institution-id: 118" \
  -H "x-behalf-id: 1545" \
  -H "x-behalf-on: institution" \
  -H "x-current-role: 3" \
  -H "x-requested-with: XMLHttpRequest"

# 3. اختبر تقرير طالب
curl "https://api.injaazy.com/front_app_api/v1/institution_panel/reports/students/170046?episode_id=8736&period_range=W&date_of=2026/04/12-2026/04/18&student_id=170046" \
  -H "Authorization: Bearer TOKEN" \
  -H "x-institution-id: 118" \
  ...
```

### اختبار الـ Backend
```bash
curl -X POST http://localhost:8000/api/reports/bulk \
  -H "Content-Type: application/json" \
  -d '{"institution_id":"118","episode_id":8736,"period_range":"W","date_of":"2026/04/12-2026/04/18"}'
```

---

*وثيقة مرجعية — مشروع تقارير الطلاب الجماعية على نظام إنجازي*
