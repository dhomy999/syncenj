"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { logsApi, JobLog, StudentImport } from "@/lib/api";
import { formatDate, STATUS_LABELS } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { ChevronRight } from "lucide-react";

export default function LogDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [log, setLog]           = useState<JobLog | null>(null);
  const [students, setStudents] = useState<StudentImport[]>([]);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      logsApi.get(Number(id)),
      logsApi.students(Number(id)),
    ]).then(([l, s]) => { setLog(l.data); setStudents(s.data); })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-gray-400 text-center py-16">جارٍ التحميل...</p>;
  if (!log)    return <p className="text-red-400 text-center py-16">السجل غير موجود</p>;

  const STATUS_BADGE: Record<string, string> = {
    success: "border-emerald-200 text-emerald-700 bg-emerald-50",
    failed:  "border-red-200 text-red-700 bg-red-50",
    skipped: "border-gray-200 text-gray-500 bg-gray-50",
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/logs" className="hover:text-emerald-600 flex items-center gap-1">
          <ChevronRight size={14} /> السجلات
        </Link>
        <span>/</span>
        <span className="text-gray-700">سجل #{id}</span>
      </div>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">ملخص التنفيذ</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            {[
              { label: "المهمة",    value: `#${log.job_id}` },
              { label: "الحالة",   value: <Badge variant="outline" className={STATUS_BADGE[log.status] ?? ""}>{STATUS_LABELS[log.status]}</Badge> },
              { label: "البداية",  value: formatDate(log.started_at) },
              { label: "النهاية",  value: formatDate(log.finished_at ?? undefined) },
              { label: "المشغِّل", value: log.triggered_by === "manual" ? "يدوي" : "مجدول" },
              { label: "الإجمالي", value: log.result ? String((log.result as Record<string,unknown>).total ?? "—") : "—" },
            ].map(({ label, value }) => (
              <div key={label}>
                <dt className="text-gray-500 mb-1">{label}</dt>
                <dd className="font-medium text-gray-800">{value}</dd>
              </div>
            ))}
          </dl>

          {log.error_message && (
            <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-700">
              {log.error_message}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Student imports table */}
      {students.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">تفاصيل الطلاب ({students.length})</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-right">
                  <th className="px-5 py-3 font-medium">رقم الهوية</th>
                  <th className="px-5 py-3 font-medium">الاسم</th>
                  <th className="px-5 py-3 font-medium">الحلقة</th>
                  <th className="px-5 py-3 font-medium">الحالة</th>
                  <th className="px-5 py-3 font-medium">الخطأ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {students.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-5 py-3 font-mono text-xs text-gray-600">{s.student_username}</td>
                    <td className="px-5 py-3 text-gray-800">{s.student_name}</td>
                    <td className="px-5 py-3 text-gray-500">{s.episode_id}</td>
                    <td className="px-5 py-3">
                      <Badge variant="outline" className={STATUS_BADGE[s.status] ?? ""}>
                        {STATUS_LABELS[s.status] ?? s.status}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 text-red-500 text-xs max-w-[200px] truncate">{s.error ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
