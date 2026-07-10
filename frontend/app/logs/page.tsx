"use client";

import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Clock, ChevronLeft } from "lucide-react";
import { logsApi, jobsApi, JobLog, Job } from "@/lib/api";
import { formatDate, STATUS_LABELS, JOB_TYPE_LABELS } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

const STATUS_STYLE = {
  success: { icon: CheckCircle, badge: "border-emerald-200 text-emerald-700 bg-emerald-50" },
  failed:  { icon: XCircle,     badge: "border-red-200 text-red-700 bg-red-50" },
  running: { icon: Clock,       badge: "border-blue-200 text-blue-700 bg-blue-50" },
};

// تسميات مختصرة لعدّادات نتائج المهام الرئيسية
const RESULT_KEYS: Record<string, string> = {
  created: "أُنشئ", re_registered: "أُعيد", attended: "حاضر", opened: "فُتحت",
  eligible: "مؤهّل", attempted: "معالَج", episodes_seen: "حلقات", failed: "فشل",
  enjazi_ids_written: "ربط", total: "عنصر",
};

/** يبني ملخّصًا مختصرًا من نتيجة المهمة (أهم العدّادات فقط). */
function summarizeResult(result: Record<string, unknown> | null): string {
  if (!result) return "";
  const parts: string[] = [];
  if (result.dry_run === true) parts.push("تجريبي");
  for (const [key, label] of Object.entries(RESULT_KEYS)) {
    const v = result[key];
    if (typeof v === "number" && v > 0) parts.push(`${label} ${v}`);
  }
  return parts.join(" · ");
}

export default function LogsPage() {
  const [logs, setLogs]         = useState<JobLog[]>([]);
  const [jobMap, setJobMap]     = useState<Record<number, Job>>({});
  const [filter, setFilter]     = useState("");
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      logsApi.list({ limit: 100 }),
      jobsApi.list(),
    ]).then(([logsRes, jobsRes]) => {
      setLogs(logsRes.data);
      const map: Record<number, Job> = {};
      for (const j of jobsRes.data) map[j.id] = j;
      setJobMap(map);
    }).finally(() => setLoading(false));
  }, []);

  const filtered = filter ? logs.filter((l) => l.status === filter) : logs;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">سجل التنفيذ</h1>
          <p className="text-sm text-gray-500 mt-1">تاريخ جميع عمليات الأتمتة</p>
        </div>
        {/* Filter */}
        <div className="flex gap-2">
          {["", "success", "failed", "running"].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                filter === s
                  ? "bg-emerald-600 text-white border-emerald-600"
                  : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
              }`}
            >
              {s === "" ? "الكل" : STATUS_LABELS[s]}
            </button>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{filtered.length} سجل</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-sm text-gray-400 text-center py-10">جارٍ التحميل...</p>
          ) : filtered.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-10">لا توجد سجلات</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-right">
                  <th className="px-5 py-3 font-medium">المهمة</th>
                  <th className="px-5 py-3 font-medium">الحالة</th>
                  <th className="px-5 py-3 font-medium">المشغِّل</th>
                  <th className="px-5 py-3 font-medium">البداية</th>
                  <th className="px-5 py-3 font-medium">المدة</th>
                  <th className="px-5 py-3 font-medium">النتيجة</th>
                  <th className="px-5 py-3 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map((log) => {
                  const cfg = STATUS_STYLE[log.status] ?? STATUS_STYLE.running;
                  const Icon = cfg.icon;
                  const duration = log.finished_at
                    ? `${((new Date(log.finished_at).getTime() - new Date(log.started_at).getTime()) / 1000).toFixed(1)}ث`
                    : "—";

                  return (
                    <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-5 py-3 font-medium text-gray-700">
                        {jobMap[log.job_id]
                          ? <span title={`#${log.job_id}`}>{jobMap[log.job_id].name}<div className="text-xs text-gray-400 font-normal">{JOB_TYPE_LABELS[jobMap[log.job_id].type] ?? jobMap[log.job_id].type}</div></span>
                          : `#${log.job_id}`}
                      </td>
                      <td className="px-5 py-3">
                        <Badge variant="outline" className={cfg.badge}>
                          <Icon size={12} className="ml-1 inline" />
                          {STATUS_LABELS[log.status] ?? log.status}
                        </Badge>
                      </td>
                      <td className="px-5 py-3 text-gray-500">
                        {log.triggered_by === "manual" ? "يدوي" : "مجدول"}
                      </td>
                      <td className="px-5 py-3 text-gray-500">{formatDate(log.started_at)}</td>
                      <td className="px-5 py-3 text-gray-500 font-mono text-xs">{duration}</td>
                      <td className="px-5 py-3 text-gray-500 text-xs">
                        {log.result
                          ? (summarizeResult(log.result as Record<string, unknown>) || "تم")
                          : log.error_message
                          ? <span className="text-red-500 truncate max-w-[120px] block">{log.error_message}</span>
                          : "—"}
                      </td>
                      <td className="px-5 py-3">
                        <Link
                          href={`/logs/${log.id}`}
                          className="text-emerald-600 hover:text-emerald-800 flex items-center gap-1 text-xs"
                        >
                          تفاصيل <ChevronLeft size={12} />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
