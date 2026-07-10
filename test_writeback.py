"""
كتابة enjazi_id=263189 في Supabase للطالب 1159952959 بعد التحقق من ربطه بالحلقة.
"""
from backend.supabase_client import get_supabase

NID = "1159952959"
ENJAZI_ID = 263189

sb = get_supabase()
resp = (
    sb.table("students")
    .update({"enjazi_id": ENJAZI_ID})
    .eq("student_national_id", NID)
    .execute()
)
print(f"تم تحديث {len(resp.data)} صف:")
import json
print(json.dumps(resp.data, ensure_ascii=False, indent=2, default=str))

# تحقق
chk = sb.table("students").select("student_national_id,student_name,enjazi_id").eq("student_national_id", NID).execute().data
print("\nتحقق:", chk)
