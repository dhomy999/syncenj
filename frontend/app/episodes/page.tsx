"use client";

import { useEffect, useState } from "react";
import { dataApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw, Download } from "lucide-react";
import { exportCsv } from "@/lib/utils";

interface Day { id: number; name: string }

interface Episode {
  id: number;
  name: string;
  teacher_name: string;
  institution_name: string;
  episode_category_name: string;
  episode_type_name: string;
  period_name: string;
  no_students: number;
  max_students_number: number;
  status: boolean;
  days: Day[];
}

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return "منذ أقل من دقيقة";
  if (diff < 3600) return `منذ ${Math.floor(diff / 60)} دقيقة`;
  if (diff < 86400) return `منذ ${Math.floor(diff / 3600)} ساعة`;
  return `منذ ${Math.floor(diff / 86400)} يوم`;
}

export default function EpisodesPage() {
  const [episodes, setEpisodes]     = useState<Episode[]>([]);
  const [updatedAt, setUpdatedAt]   = useState<string | null>(null);
  const [search, setSearch]         = useState("");
  const [loading, setLoading]       = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    dataApi.episodes()
      .then((r) => { setEpisodes(r.data.data as unknown as Episode[]); setUpdatedAt(r.data.updated_at); })
      .catch(() => setError("تعذّر الاتصال بالخادم — تأكد من تشغيل الـ backend على المنفذ 8000"))
      .finally(() => setLoading(false));
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      const r = await dataApi.refreshEpisodes();
      setEpisodes(r.data.data as unknown as Episode[]);
      setUpdatedAt(r.data.updated_at);
    } finally {
      setRefreshing(false);
    }
  }

  const filtered = episodes.filter((e) =>
    !search ||
    e.name?.includes(search) ||
    e.teacher_name?.includes(search) ||
    e.institution_name?.includes(search)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">الحلقات</h1>
          <p className="text-sm text-gray-500 mt-1">
            {episodes.length} حلقة
            {updatedAt && <span className="text-gray-400"> · {timeAgo(updatedAt)}</span>}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input
            className="input-base w-56"
            placeholder="بحث بالاسم أو المعلم أو المنشأة..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              exportCsv(
                filtered.map((e) => ({
                  id:           e.id,
                  name:         e.name,
                  teacher:      e.teacher_name ?? "—",
                  institution:  e.institution_name ?? "—",
                  category:     e.episode_category_name ?? "—",
                  type:         e.episode_type_name ?? "—",
                  period:       e.period_name ?? "—",
                  days:         e.days?.map((d) => d.name).join("، ") ?? "—",
                  students:     e.no_students ?? 0,
                  max:          e.max_students_number ?? 0,
                  status:       e.status ? "نشطة" : "غير نشطة",
                })),
                [
                  { key: "id",          label: "ID" },
                  { key: "name",        label: "اسم الحلقة" },
                  { key: "teacher",     label: "المعلم" },
                  { key: "institution", label: "المنشأة" },
                  { key: "category",    label: "الفئة" },
                  { key: "type",        label: "النوع" },
                  { key: "period",      label: "الوقت" },
                  { key: "days",        label: "الأيام" },
                  { key: "students",    label: "عدد الطلاب" },
                  { key: "max",         label: "الحد الأقصى" },
                  { key: "status",      label: "الحالة" },
                ],
                `episodes_${new Date().toISOString().slice(0, 10)}`
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
          <CardTitle className="text-base">{filtered.length} نتيجة</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-sm text-gray-400 text-center py-10">جارٍ التحميل...</p>
          ) : episodes.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-10">
              لا توجد بيانات — اضغط <strong>تحديث</strong> لجلب الحلقات من الموقع
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-right">
                  <th className="px-4 py-3 font-medium">اسم الحلقة</th>
                  <th className="px-4 py-3 font-medium">المعلم</th>
                  <th className="px-4 py-3 font-medium">المنشأة</th>
                  <th className="px-4 py-3 font-medium">الوقت</th>
                  <th className="px-4 py-3 font-medium">الطلاب</th>
                  <th className="px-4 py-3 font-medium">الحالة</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((e) => (
                  <tr key={e.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800">
                      {e.name}
                      {e.episode_category_name && (
                        <div className="text-xs text-gray-400 mt-0.5">{e.episode_category_name}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{e.teacher_name ?? "—"}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{e.institution_name ?? "—"}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {e.period_name ?? "—"}
                      {e.days?.length > 0 && (
                        <div className="text-gray-400">{e.days.map((d) => d.name).join("، ")}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs text-center">
                      {e.no_students ?? 0} / {e.max_students_number ?? "∞"}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${
                        e.status
                          ? "border-emerald-200 text-emerald-700 bg-emerald-50"
                          : "border-gray-200 text-gray-400"
                      }`}>
                        {e.status ? "نشطة" : "غير نشطة"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
