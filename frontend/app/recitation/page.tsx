"use client";

import { useCallback, useEffect, useState } from "react";
import { recitationApi, ReciteStats, ReciteRow, SyncStatus } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RefreshCw, Play, RotateCcw, Download } from "lucide-react";
import { exportCsv } from "@/lib/utils";

const TABS: { key: SyncStatus; label: string; tone: string }[] = [
  { key: "pending", label: "معلّق",    tone: "border-amber-200 text-amber-700 bg-amber-50" },
  { key: "failed",  label: "فاشل",     tone: "border-red-200 text-red-700 bg-red-50" },
  { key: "skipped", label: "متخطّى",   tone: "border-gray-200 text-gray-600 bg-gray-50" },
  { key: "synced",  label: "مُزامَن",  tone: "border-emerald-200 text-emerald-700 bg-emerald-50" },
];

export default function RecitationPage() {
  const [stats, setStats]     = useState<ReciteStats | null>(null);
  const [tab, setTab]         = useState<SyncStatus>("pending");
  const [rows, setRows]       = useState<ReciteRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy]       = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, r] = await Promise.all([recitationApi.stats(), recitationApi.rows(tab)]);
      setStats(s.data);
      setRows(r.data.data);
      setError(null);
    } catch {
      setError("تعذّر الاتصال بالخادم — تأكد من تشغيل الـ backend على المنفذ 8000");
    } finally {
      setLoading(false);
    }
  }, [tab]);

  // العامل يعمل باستمرار في الخلفية، فنحدّث الأرقام تلقائيًا كل 10 ثوانٍ.
  useEffect(() => {
    load();
    const t = setInterval(load, 10_000);
    return () => clearInterval(t);
  }, [load]);

  async function runNow() {
    setBusy(true);
    try { await recitationApi.run(25); await load(); }
    finally { setBusy(false); }
  }

  async function retryFailed() {
    setBusy(true);
    try { await recitationApi.retry(); await load(); }
    finally { setBusy(false); }
  }

  const c = stats?.counts;
  const w = stats?.worker;
  const done = (c?.synced ?? 0) + (c?.skipped ?? 0);
  const pct = c?.total ? Math.round((done / c.total) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">مزامنة التسميع</h1>
          <p className="text-sm text-gray-500 mt-1">
            {w?.running ? (
              <span className="text-emerald-600">العامل يعمل — دورة كل {w.interval}s، دفعة {w.batch} صف</span>
            ) : w?.enabled === false ? (
              <span className="text-gray-400">العامل معطَّل (RECITE_WORKER_ENABLED=false)</span>
            ) : (
              <span className="text-gray-400">العامل متوقف</span>
            )}
            {w?.cycles ? <span className="text-gray-400"> · {w.cycles} دورة</span> : null}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={runNow} disabled={busy}
            className="flex items-center gap-1">
            <Play size={14} /> شغّل دفعة الآن
          </Button>
          <Button variant="outline" size="sm" onClick={retryFailed}
            disabled={busy || !c?.failed}
            className="flex items-center gap-1 text-red-600 border-red-200">
            <RotateCcw size={14} /> إعادة الفاشل ({c?.failed ?? 0})
          </Button>
          <Button variant="outline" size="sm" onClick={load} disabled={loading}
            className="flex items-center gap-1">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> تحديث
          </Button>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-500 bg-red-50 border border-red-200 rounded-lg px-4 py-3">{error}</p>
      )}
      {w?.last_error && (
        <p className="text-sm text-red-500 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          آخر دورة فشلت: {w.last_error}
        </p>
      )}

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Stat label="إجمالي الصفوف" value={c?.total ?? 0} />
        <Stat label="مُزامَن" value={c?.synced ?? 0} tone="text-emerald-600" />
        <Stat label="متخطّى" value={c?.skipped ?? 0} tone="text-gray-500" />
        <Stat label="معلّق" value={c?.pending ?? 0} tone="text-amber-600" />
        <Stat label="فاشل" value={c?.failed ?? 0} tone="text-red-600" />
      </div>

      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600">أُنجز {done} من {c?.total ?? 0}</span>
            <span className="font-medium text-gray-800">{pct}%</span>
          </div>
          <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
            <div className="h-full bg-emerald-500 transition-all" style={{ width: `${pct}%` }} />
          </div>
          {!!c?.stuck && (
            <p className="text-xs text-red-500 mt-2">
              {c.stuck} صف تجاوز حدّ المحاولات ({stats?.max_attempts}) — لن يُعاد إلا بالضغط على «إعادة الفاشل»
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <div className="flex items-center gap-2">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition ${
                  tab === t.key ? t.tone : "border-transparent text-gray-500 hover:bg-gray-50"
                }`}
              >
                {t.label} ({c?.[t.key] ?? 0})
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm text-gray-400 font-normal">{rows.length} صف</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                exportCsv(
                  rows.map((r) => ({
                    date:     r.recite_date ?? "—",
                    name:     r.student_name ?? "—",
                    halqa:    r.halqa_code ?? "—",
                    status:   r.sync_status,
                    attempts: r.sync_attempts,
                    note:     r.sync_error ?? "—",
                  })),
                  [
                    { key: "date",     label: "التاريخ" },
                    { key: "name",     label: "الطالب" },
                    { key: "halqa",    label: "الحلقة" },
                    { key: "status",   label: "الحالة" },
                    { key: "attempts", label: "المحاولات" },
                    { key: "note",     label: "الملاحظة/الخطأ" },
                  ],
                  `recitation_${tab}_${new Date().toISOString().slice(0, 10)}`
                )
              }
              disabled={rows.length === 0}
              className="flex items-center gap-1"
            >
              <Download size={14} /> تصدير CSV
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading && rows.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-10">جارٍ التحميل...</p>
          ) : rows.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-10">لا صفوف في هذه الحالة</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-right">
                  <th className="px-4 py-3 font-medium">التاريخ</th>
                  <th className="px-4 py-3 font-medium">الطالب</th>
                  <th className="px-4 py-3 font-medium">الحلقة</th>
                  <th className="px-4 py-3 font-medium">المحاولات</th>
                  <th className="px-4 py-3 font-medium">الملاحظة / الخطأ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{r.recite_date ?? "—"}</td>
                    <td className="px-4 py-3 font-medium text-gray-800">{r.student_name ?? "—"}</td>
                    <td className="px-4 py-3 text-gray-500">{r.halqa_code ?? "—"}</td>
                    <td className="px-4 py-3">
                      {r.sync_attempts > 0 ? (
                        <Badge variant="outline" className="border-gray-200 text-gray-500">
                          {r.sync_attempts}
                        </Badge>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 max-w-[420px] truncate"
                        title={r.sync_error ?? ""}>
                      {r.sync_error ?? "—"}
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

function Stat({ label, value, tone = "text-gray-800" }: { label: string; value: number; tone?: string }) {
  return (
    <Card>
      <CardContent className="py-4">
        <p className="text-xs text-gray-500">{label}</p>
        <p className={`text-2xl font-bold mt-1 ${tone}`}>{value}</p>
      </CardContent>
    </Card>
  );
}
