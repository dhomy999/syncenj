"use client";

import { useEffect, useState } from "react";
import { dataApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw, Download } from "lucide-react";
import { exportCsv } from "@/lib/utils";

interface Facility {
  id: number;
  name: string;
  center_name?: string;
  center_id?: number;
}

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return "منذ أقل من دقيقة";
  if (diff < 3600) return `منذ ${Math.floor(diff / 60)} دقيقة`;
  if (diff < 86400) return `منذ ${Math.floor(diff / 3600)} ساعة`;
  return `منذ ${Math.floor(diff / 86400)} يوم`;
}

export default function FacilitiesPage() {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [updatedAt, setUpdatedAt]   = useState<string | null>(null);
  const [search, setSearch]         = useState("");
  const [loading, setLoading]       = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError]           = useState<string | null>(null);

  useEffect(() => {
    dataApi.facilities()
      .then((r) => {
        setFacilities(r.data.data as unknown as Facility[]);
        setUpdatedAt(r.data.updated_at);
      })
      .catch(() => setError("تعذّر الاتصال بالخادم — تأكد من تشغيل الـ backend على المنفذ 8000"))
      .finally(() => setLoading(false));
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      const r = await dataApi.refreshFacilities();
      setFacilities(r.data.data as unknown as Facility[]);
      setUpdatedAt(r.data.updated_at);
    } finally {
      setRefreshing(false);
    }
  }

  const filtered = facilities.filter((f) =>
    !search ||
    f.name?.includes(search) ||
    (f.center_name ?? "").includes(search)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">المنشآت</h1>
          <p className="text-sm text-gray-500 mt-1">
            {facilities.length} منشأة
            {updatedAt && <span className="text-gray-400"> · {timeAgo(updatedAt)}</span>}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input
            className="input-base w-56"
            placeholder="بحث بالاسم أو الفرع..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              exportCsv(
                filtered.map((f) => ({
                  id:          f.id,
                  name:        f.name,
                  center_name: f.center_name ?? "—",
                })),
                [
                  { key: "id",          label: "ID" },
                  { key: "name",        label: "اسم المنشأة" },
                  { key: "center_name", label: "الفرع" },
                ],
                `facilities_${new Date().toISOString().slice(0, 10)}`
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
          ) : facilities.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-10">
              لا توجد بيانات — اضغط <strong>تحديث</strong> لجلب المنشآت من الموقع
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-right">
                  <th className="px-4 py-3 font-medium">اسم المنشأة</th>
                  <th className="px-4 py-3 font-medium">الفرع</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.slice(0, 200).map((f) => (
                  <tr key={f.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800">{f.name}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{f.center_name ?? "—"}</td>
                  </tr>
                ))}
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
