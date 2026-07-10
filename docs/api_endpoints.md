# API Endpoints — Injazi (إنجازي)

## Base URL
```
https://api.injaazy.com/front_app_api/v1
```

## Dashboard Origin
```
https://dashboard.injaazy.com
```

---

## Authentication

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/login` | `{ username, password, country_id }` | `{ data: { token, user: {...} } }` |

**Token format:** `{user_id}|{40-char-hex}`
Example: `<USER_ID>|<40-char-hex>`

**All authenticated requests need:**
```
authorization: Bearer {token}
x-requested-with: XMLHttpRequest
```

---

## Role/Scope Headers (required for most endpoints)

| Header | Value | Description |
|--------|-------|-------------|
| `x-behalf-id` | 1740 | Institution or Center ID |
| `x-behalf-on` | `institution` / `center` | Current scope |
| `x-current-role` | `3` | Role code |
| `x-institution-id` | `118` | Corporation/root institution ID |

---

## System Hierarchy

```
الجمعية  Corporation (role: corporation)
└── الفرع  Center (x-behalf-on: center)
    └── المنشأة  Institution (x-behalf-on: institution)
        └── الحلقات  Episodes
            └── الطلاب  Students
```

---

## Corporation Panel

| Method | Path | Description |
|--------|------|-------------|
| GET | `/corporation_panel/models-filter/students` | All students (limit=5000) |
| GET | `/corporation_panel/models-filter/institutions` | All institutions (limit=1000) |
| GET | `/corporation_panel/models-filter/episodes` | All circles |
| GET | `/corporation_panel/models-filter/teachers` | All teachers |
| GET | `/corporation_panel/centers` | Centers list |
| GET | `/corporation_panel/centers/get-list` | Centers short list |
| POST | `/switch-role` | Switch active role |

---

## Center Panel

| Method | Path | Description |
|--------|------|-------------|
| GET | `/center_panel/dashboard` | Dashboard data |
| GET | `/center_panel/dashboard/get-filters` | Dashboard filter options |
| GET | `/center_panel/institutions/get-list` | Institution list |
| GET | `/center_panel/teachers` | Teachers |
| GET | `/center_panel/supervisors/list` | Supervisors |
| GET | `/center_panel/models-filter/episodes` | Episodes filter |
| GET | `/center_panel/center-info/{id}` | Center details |
| GET | `/center_panel/reports/full-reports` | Reports |

---

## Institution Panel

| Method | Path | Description |
|--------|------|-------------|
| GET | `/institution_panel/dashboard/overview` | Dashboard |
| POST | `/institution_panel/students` | **Add student** |
| GET | `/institution_panel/settings/permissions/v2` | Permissions |
| GET | `/institution_panel/settings/general_settings` | Settings |
| GET | `/institution_panel/reports/full-reports` | Reports |

---

## Add Student — Full Details

**Endpoint:** `POST /institution_panel/students`
**Content-Type:** `multipart/form-data`

### Required Fields
| Field | Example | Notes |
|-------|---------|-------|
| `username` | `151106667488` | National ID (رقم الهوية) |
| `name` | `اسم الطالب` | Arabic name |
| `nationality_id` | `1` | 1=Saudi |
| `gender_id` | `1` | 1=Male, 2=Female |
| `date_of_birth` | `2010-05-20` | YYYY-MM-DD (Gregorian) |
| `program` | `523` | Program ID |
| `level_id` | `1745` | Level ID |
| `episode_id` | `9918` | Circle/Halqa ID |

### Optional Fields
| Field | Example | Notes |
|-------|---------|-------|
| `phone_country_code` | `966` | |
| `guardian_phone_country_code` | `966` | |

### Success Response
```json
{
  "success": true,
  "data": {
    "id": 230371,
    "name": "اسم الطالب",
    "username": "151106667488",
    "date_of_birth": "2010-05-20",
    "status": true,
    "active": true,
    "episodes": [...]
  },
  "message": "تمت إضافة الطالب بنجاح"
}
```

---

## User

| Method | Path | Description |
|--------|------|-------------|
| GET | `/user/chats` | Chat messages |

---

## Known IDs (from research)

| Item | ID |
|------|----|
| Corporation | 118 |
| Center (رجالية) | 171 |
| Center 2 | 444 |
| Institution | 1740 |
| Program | 523 |
| Level | 1745 |
| Episode/Halqa | 9918 |
