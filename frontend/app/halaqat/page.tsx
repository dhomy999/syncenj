"use client";

import { useEffect, useState } from "react";
import { halaqatApi, Halqa, EnjaziEpisode } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, Link2, Check, X } from "lucide-react";

export default function HalaqatPage() {
  const [halaqat, setHalaqat] = useState<Halqa[]>([]);
  const [search, setSearch]   = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  // picker state
  const [picker, setPicker]     = useState<Halqa | null>(null);
  const [episodes, setEpisodes] = useState<EnjaziEpisode[]>([]);
  const [epsLoading, setEpsLoading] = useState(false);
  const [epSearch, setEpSearch] = useState("");

  async function load() {
    setLoading(true);
    try {
      const r = await halaqatApi.list();
      setHalaqat(r.data.data);
      setError(null);
    } catch {
      setError("تعذّر الاتصال بالخادم — تأكد من تشغيل الـ backend على المنفذ 8000");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function openPicker(h: Halqa) {
    setPicker(h);
    setEpSearch("");
    if (episodes.length === 0) {
      setEpsLoading(true);
      try {
        const r = await halaqatApi.enjaziEpisodes();
        setEpisodes(r.data.data);
      } catch {
        setError("تعذّر جلب حلقات إنجازي — تأكد من بيانات الدخول في .env");
        setPicker(null);
      } finally {
        setEpsLoading(false);
      }
    }
  }

  async function choose(enjazi_id: number | null) {
    if (!picker) return;
    const h = picker;
    setPicker(null);
    await halaqatApi.link(h.id, enjazi_id);
    setHalaqat((prev) =>
      prev.map((x) => (x.id === h.id ? { ...x, enjazi_id, linked: enjazi_id !== null } : x))
    );
  }

  const filtered = halaqat.filter((h) =>
    !search ||
    (h.halqa_code ?? "").includes(search) ||
    (h.teacher_name ?? "").includes(search) ||
    (h.track ?? "").includes(search)
  );

  const epsFiltered = episodes.filter((e) =>
    !epSearch ||
    (e.name ?? "").includes(epSearch) ||
    (e.teacher_name ?? "").includes(epSearch) ||
    String(e.id).includes(epSearch)
  );

  const linkedCount = halaqat.filter((h) => h.linked).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">الحلقات</h1>
          <p className="text-sm text-gray-500 mt-1">
            {halaqat.length} حلقة
            <span className="text-gray-400"> · {linkedCount} مرتبطة بإنجازي</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input
            className="input-base w-64"
            placeholder="بحث بالرمز أو المعلّم أو المسار..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
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
          <CardTitle className="text-base">{filtered.length} حلقة</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-sm text-gray-400 text-center py-10">جارٍ التحميل...</p>
          ) : halaqat.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-10">لا توجد حلقات</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-right">
                  <th className="px-4 py-3 font-medium">الرمز</th>
                  <th className="px-4 py-3 font-medium">المسار</th>
                  <th className="px-4 py-3 font-medium">المعلّم</th>
                  <th className="px-4 py-3 font-medium">الفترة</th>
                  <th className="px-4 py-3 font-medium">النوع</th>
                  <th className="px-4 py-3 font-medium">إنجازي</th>
                  <th className="px-4 py-3 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((h) => (
                  <tr key={h.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-600">{h.halqa_code}</td>
                    <td className="px-4 py-3 text-gray-600">{h.track ?? "—"}</td>
                    <td className="px-4 py-3 font-medium text-gray-800">{h.teacher_name ?? "—"}</td>
                    <td className="px-4 py-3 text-gray-500">{h.period ?? "—"}</td>
                    <td className="px-4 py-3 text-gray-500">{h.circle_type ?? "—"}</td>
                    <td className="px-4 py-3">
                      {h.linked ? (
                        <Badge variant="outline" className="border-emerald-200 text-emerald-700 bg-emerald-50">
                          <Check size={12} className="ml-1" /> {h.enjazi_id}
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="border-gray-200 text-gray-400">غير مرتبطة</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Button variant="outline" size="sm" onClick={() => openPicker(h)}
                        className="flex items-center gap-1">
                        <Link2 size={13} />
                        {h.linked ? "تعديل" : "ربط"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* Picker modal */}
      {picker && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
          onClick={() => setPicker(null)}>
          <div className="bg-white rounded-xl w-full max-w-lg max-h-[80vh] flex flex-col shadow-xl"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <div>
                <h3 className="font-bold text-gray-800">ربط الحلقة {picker.halqa_code}</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {picker.teacher_name ?? "—"} · {picker.period ?? "—"} — اختر حلقة إنجازي المقابلة
                </p>
              </div>
              <button onClick={() => setPicker(null)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>
            <div className="px-5 py-3 border-b">
              <input
                className="input-base w-full"
                placeholder="بحث باسم المعلّم أو الحلقة أو الرقم..."
                value={epSearch}
                onChange={(e) => setEpSearch(e.target.value)}
                autoFocus
              />
            </div>
            <div className="flex-1 overflow-y-auto">
              {epsLoading ? (
                <p className="text-sm text-gray-400 text-center py-10">جارٍ جلب حلقات إنجازي...</p>
              ) : epsFiltered.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-10">لا نتائج</p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {epsFiltered.slice(0, 100).map((e) => (
                    <li key={e.id}>
                      <button
                        onClick={() => choose(e.id)}
                        className="w-full text-right px-5 py-3 hover:bg-emerald-50 flex items-center justify-between"
                      >
                        <span>
                          <span className="font-medium text-gray-800">{e.name}</span>
                          {e.teacher_name && <span className="text-xs text-gray-400 mr-2">— {e.teacher_name}</span>}
                        </span>
                        <span className="font-mono text-xs text-gray-400">#{e.id}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="px-5 py-3 border-t flex justify-between">
              {picker.linked ? (
                <Button variant="outline" size="sm" onClick={() => choose(null)}
                  className="text-red-600 border-red-200">
                  إلغاء الربط
                </Button>
              ) : <span />}
              <Button variant="outline" size="sm" onClick={() => setPicker(null)}>إغلاق</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
