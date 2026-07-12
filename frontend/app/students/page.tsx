"use client";

import { useEffect, useState } from "react";
import { studentsApi, SupaStudent } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, Download, Check } from "lucide-react";
import { exportCsv } from "@/lib/utils";

export default function StudentsPage() {
  const [students, setStudents] = useState<SupaStudent[]>([]);
  const [search, setSearch]     = useState("");
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const r = await studentsApi.list({ limit: 5000 });
      setStudents(r.data.data);
      setError(null);
    } catch {
      setError("تعذّر الاتصال بالخادم — تأكد من تشغيل الـ backend على المنفذ 8000");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const filtered = students.filter((s) =>
    !search ||
    String(s.student_number).includes(search) ||
    (s.student_national_id ?? "").includes(search) ||
    (s.student_name ?? "").includes(search) ||
    (s.halaqat ?? []).some((h) => h.includes(search))
  );

  const linkedCount = students.filter((s) => s.linked).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">الطلاب</h1>
          <p className="text-sm text-gray-500 mt-1">
            {students.length} طالب
            <span className="text-gray-400"> · {linkedCount} مرتبط بإنجازي</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input
            className="input-base w-64"
            placeholder="بحث بالاسم أو رقم الهوية..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              exportCsv(
                filtered.map((s) => ({
                  number:   s.student_number,
                  nid:      s.student_national_id ?? "—",
                  name:     s.student_name,
                  dept:     s.department ?? "—",
                  category: s.category ?? "—",
                  halaqat:  (s.halaqat ?? []).join("، ") || "—",
                  status:   s.status ?? "—",
                  enjazi:   s.enjazi_id ?? "—",
                })),
                [
                  { key: "number",   label: "رقم الطالب" },
                  { key: "nid",      label: "رقم الهوية" },
                  { key: "name",     label: "الاسم" },
                  { key: "dept",     label: "القسم" },
                  { key: "category", label: "الفئة" },
                  { key: "halaqat",  label: "الحلقات" },
                  { key: "status",   label: "الحالة" },
                  { key: "enjazi",   label: "رقم إنجازي" },
                ],
                `students_${new Date().toISOString().slice(0, 10)}`
              )
            }
            disabled={filtered.length === 0}
            className="flex items-center gap-1"
          >
            <Download size={14} />
            تصدير CSV
          </Button>
          <Button variant="outline" size="sm" onClick={load} disabled={loading}
            className="flex items-center gap-1">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            تحديث
          </Button>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-500 bg-red-50 border border-red-200 rounded-lg px-4 py-3">{error}</p>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{filtered.length} طالب</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-sm text-gray-400 text-center py-10">جارٍ التحميل...</p>
          ) : students.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-10">لا توجد بيانات</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-right">
                  <th className="px-4 py-3 font-medium">رقم الطالب</th>
                  <th className="px-4 py-3 font-medium">رقم الهوية</th>
                  <th className="px-4 py-3 font-medium">الاسم</th>
                  <th className="px-4 py-3 font-medium">القسم</th>
                  <th className="px-4 py-3 font-medium">الحلقات</th>
                  <th className="px-4 py-3 font-medium">الحالة</th>
                  <th className="px-4 py-3 font-medium">إنجازي</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.slice(0, 300).map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{s.student_number}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{s.student_national_id ?? "—"}</td>
                    <td className="px-4 py-3 font-medium text-gray-800">{s.student_name}</td>
                    <td className="px-4 py-3 text-gray-500">{s.department ?? "—"}</td>
                    <td className="px-4 py-3 text-gray-600 max-w-[220px] truncate"
                        title={(s.halaqat ?? []).join("، ")}>
                      {(s.halaqat ?? []).join("، ") || "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{s.status ?? "—"}</td>
                    <td className="px-4 py-3">
                      {s.linked ? (
                        <Badge variant="outline" className="border-emerald-200 text-emerald-700 bg-emerald-50">
                          <Check size={12} className="ml-1" /> {s.enjazi_id}
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="border-gray-200 text-gray-400">غير مرتبط</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {filtered.length > 300 && (
            <p className="text-center text-xs text-gray-400 py-3">
              يعرض أول 300 نتيجة من {filtered.length} — استخدم البحث للتضييق
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
