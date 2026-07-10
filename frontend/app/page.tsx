"use client";

import { useEffect, useState } from "react";
import { GraduationCap, Building2, BookOpen, Users, CheckCircle, XCircle, Clock } from "lucide-react";
import { StatCard } from "@/components/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { dataApi, logsApi, JobLog } from "@/lib/api";
import { formatDate, JOB_TYPE_LABELS } from "@/lib/utils";

const STATUS_CONFIG = {
  success: { label: "نجح",  icon: CheckCircle, class: "text-emerald-600" },
  failed:  { label: "فشل",  icon: XCircle,     class: "text-red-500" },
  running: { label: "جارٍ", icon: Clock,        class: "text-blue-500" },
};

export default function DashboardPage() {
  const [stats, setStats] = useState({ teachers: null, facilities: null, episodes: null, students: null } as
    Record<string, number | null>);
  const [logs, setLogs]     = useState<JobLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      dataApi.teachers(),
      dataApi.facilities(),
      dataApi.episodes(),
      dataApi.students(),
      logsApi.list({ limit: 6 }),
    ]).then(([t, f, e, s, l]) => {
      setStats({
        teachers:   t.data.total,
        facilities: f.data.total,
        episodes:   e.data.total,
        students:   s.data.total,
      });
      setLogs(l.data);
    }).catch(() => setError("تعذّر الاتصال بالخادم — تأكد من تشغيل الـ backend على المنفذ 8000"))
    .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">لوحة التحكم</h1>
        <p className="text-sm text-gray-500 mt-1">نظرة عامة على بيانات المنشأة</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="المعلمين" value={stats.teachers}   icon={GraduationCap} color="bg-blue-500"    loading={loading} />
        <StatCard label="المنشآت"  value={stats.facilities} icon={Building2} color="bg-violet-500"  loading={loading} />
        <StatCard label="الحلقات"  value={stats.episodes}   icon={BookOpen}  color="bg-amber-500"   loading={loading} />
        <StatCard label="الطلاب"   value={stats.students}   icon={Users}     color="bg-emerald-500" loading={loading} />
      </div>

      {error && (
        <p className="text-sm text-red-500 bg-red-50 border border-red-200 rounded-lg px-4 py-3">{error}</p>
      )}

      {/* Recent logs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">آخر عمليات التنفيذ</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-gray-400 text-center py-6">جارٍ التحميل...</p>
          ) : logs.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">لا توجد سجلات بعد</p>
          ) : (
            <div className="divide-y divide-gray-100">
              {logs.map((log) => {
                const cfg = STATUS_CONFIG[log.status] ?? STATUS_CONFIG.running;
                const Icon = cfg.icon;
                return (
                  <div key={log.id} className="flex items-center justify-between py-3">
                    <div className="flex items-center gap-3">
                      <Icon size={16} className={cfg.class} />
                      <div>
                        <p className="text-sm font-medium text-gray-700">
                          {JOB_TYPE_LABELS[String(log.result?.scope ?? "")] ?? `مهمة #${log.job_id}`}
                        </p>
                        <p className="text-xs text-gray-400">{formatDate(log.started_at)}</p>
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className={
                        log.status === "success" ? "border-emerald-200 text-emerald-700 bg-emerald-50" :
                        log.status === "failed"  ? "border-red-200 text-red-700 bg-red-50" :
                        "border-blue-200 text-blue-700 bg-blue-50"
                      }
                    >
                      {cfg.label}
                    </Badge>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
