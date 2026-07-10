"use client";

import { useEffect, useState } from "react";
import { dataApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, Download } from "lucide-react";
import { exportCsv } from "@/lib/utils";

interface Teacher {
  id: number;
  name: string;
  username?: string;
  gender_id?: number;
  center_name?: string;
  status?: string;
  [key: string]: unknown;
}

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return "منذ أقل من دقيقة";
  if (diff < 3600) return `منذ ${Math.floor(diff / 60)} دقيقة`;
  if (diff < 86400) return `منذ ${Math.floor(diff / 3600)} ساعة`;
  return `منذ ${Math.floor(diff / 86400)} يوم`;
}

export default function TeachersPage() {
  const [teachers, setTeachers]     = useState<Teacher[]>([]);
  const [updatedAt, setUpdatedAt]   = useState<string | null>(null);
  const [search, setSearch]         = useState("");
  const [loading, setLoading]       = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    dataApi.teachers()
      .then((r) => {
        setTeachers(r.data.data as unknown as Teacher[]);
        setUpdatedAt(r.data.updated_at);
      })
      .catch(() => setError("تعذّر الاتصال بالخادم — تأكد من تشغيل الـ backend على المنفذ 8000"))
      .finally(() => setLoading(false));
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      const r = await dataApi.refreshTeachers();
      setTeachers(r.data.data as unknown as Teacher[]);
      setUpdatedAt(r.data.updated_at);
    } finally {
      setRefreshing(false);
    }
  }

  const filtered = teachers.filter((t) =>
    !search ||
    String(t.id).includes(search) ||
    (t.username ?? "").includes(search) ||
    (t.name ?? "").includes(search) ||
    (t.center_name ?? "").includes(search)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">المعلمون</h1>
          <p className="text-sm text-gray-500 mt-1">
            {teachers.length} معلم
            {updatedAt && <span className="text-gray-400"> · {timeAgo(updatedAt)}</span>}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input
            className="input-base w-64"
            placeholder="بحث بالاسم أو رقم الهوية أو الفرع..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              exportCsv(
                filtered.map((t) => ({
                  id:          t.id,
                  username:    t.username ?? "—",
                  name:        t.name,
                  gender:      t.gender_id === 1 ? "ذكر" : t.gender_id === 2 ? "أنثى" : "—",
                  center_name: t.center_name ?? "—",
                  status:      t.status === "active" ? "نشط" : t.status ? "غير نشط" : "—",
                })),
                [
                  { key: "id",          label: "رقم النظام" },
                  { key: "username",    label: "رقم الهوية" },
                  { key: "name",        label: "الاسم" },
                  { key: "gender",      label: "الجنس" },
                  { key: "center_name", label: "الفرع" },
                  { key: "status",      label: "الحالة" },
                ],
                `teachers_${new Date().toISOString().slice(0, 10)}`
              )
            }
            disabled={filtered.length === 0}
            className="flex items-center gap-1"
          >
            <Download size={14} />
            تصدير CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1"
          >
            <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
            {refreshing ? "جارٍ الجلب..." : "تحديث"}
          </Button>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-500 bg-red-50 border border-red-200 rounded-lg px-4 py-3">{error}</p>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{filtered.length} معلم</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-sm text-gray-400 text-center py-10">جارٍ التحميل...</p>
          ) : teachers.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-10">
              لا توجد بيانات — اضغط <strong>تحديث</strong> لجلب المعلمين من الموقع
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-right">
                  <th className="px-4 py-3 font-medium">رقم الهوية</th>
                  <th className="px-4 py-3 font-medium">الاسم</th>
                  <th className="px-4 py-3 font-medium">الجنس</th>
                  <th className="px-4 py-3 font-medium">الفرع</th>
                  <th className="px-4 py-3 font-medium">الحالة</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.slice(0, 200).map((t) => {
                  const isActive = t.status === "active";
                  return (
                    <tr key={t.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">
                        {t.username ?? "—"}
                      </td>
                      <td className="px-4 py-3 font-medium text-gray-800">{t.name}</td>
                      <td className="px-4 py-3 text-gray-500">
                        {t.gender_id === 1 ? "ذكر" : t.gender_id === 2 ? "أنثى" : "—"}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {t.center_name ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        {t.status ? (
                          <Badge variant="outline" className={
                            isActive
                              ? "border-emerald-200 text-emerald-700 bg-emerald-50"
                              : "border-gray-200 text-gray-400"
                          }>
                            {isActive ? "نشط" : "غير نشط"}
                          </Badge>
                        ) : (
                          <span className="text-gray-300">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
          {filtered.length > 200 && (
            <p className="text-center text-xs text-gray-400 py-3">
              يعرض أول 200 نتيجة من {filtered.length} — استخدم البحث للتضييق
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
