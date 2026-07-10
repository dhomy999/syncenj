"use client";

import { useEffect, useState } from "react";
import { Plus, Play, Pause, Trash2, TriangleAlert, Pencil, FlaskConical, Zap } from "lucide-react";
import { jobsApi, Job } from "@/lib/api";
import { formatDate, JOB_TYPE_LABELS } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { JobDialog } from "@/components/job-dialog";

export default function JobsPage() {
  const [jobs, setJobs]       = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<number | null>(null);
  const [open, setOpen]       = useState(false);
  const [editing, setEditing] = useState<Job | null>(null);

  const load = () => jobsApi.list().then((r) => setJobs(r.data)).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  // مهام تدعم وضع المحاكاة (dry_run) — العملياتان 2 و3 تُشحنان تجريبيتين
  const hasDryRun = (job: Job) =>
    job.params != null && Object.prototype.hasOwnProperty.call(job.params, "dry_run");
  const isDryRun = (job: Job) => job.params?.dry_run === true;

  const handleDryRun = async (job: Job) => {
    const goingLive = isDryRun(job); // سنحوّل من تجريبي → مباشر
    if (goingLive && !confirm(
      `تحويل «${job.name}» إلى الوضع المباشر؟\nستبدأ الكتابة الفعلية على نظام إنجازي.`
    )) return;
    await jobsApi.update(job.id, { params: { ...(job.params ?? {}), dry_run: !isDryRun(job) } });
    load();
  };

  const handleRun = async (job: Job) => {
    setRunning(job.id);
    await jobsApi.run(job.id);
    setTimeout(() => setRunning(null), 2000);
  };

  const handleToggle = async (job: Job) => {
    await jobsApi.update(job.id, { is_active: !job.is_active });
    load();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("هل تريد حذف هذه المهمة؟")) return;
    await jobsApi.delete(id);
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">المهام المجدولة</h1>
          <p className="text-sm text-gray-500 mt-1">إدارة وجدولة عمليات الأتمتة</p>
        </div>
        <Button onClick={() => { setEditing(null); setOpen(true); }} className="bg-emerald-600 hover:bg-emerald-700">
          <Plus size={16} className="ml-2" /> مهمة جديدة
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{jobs.length} مهمة</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <p className="text-sm text-gray-400 text-center py-10">جارٍ التحميل...</p>
          ) : jobs.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <TriangleAlert size={36} className="mx-auto mb-3 opacity-40" />
              <p>لا توجد مهام بعد. أنشئ مهمتك الأولى.</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-gray-500 text-right">
                  <th className="px-5 py-3 font-medium">الاسم</th>
                  <th className="px-5 py-3 font-medium">النوع</th>
                  <th className="px-5 py-3 font-medium">الجدول</th>
                  <th className="px-5 py-3 font-medium">آخر تشغيل</th>
                  <th className="px-5 py-3 font-medium">الحالة</th>
                  <th className="px-5 py-3 font-medium">الوضع</th>
                  <th className="px-5 py-3 font-medium">الإجراءات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-5 py-3 font-medium text-gray-800">{job.name}</td>
                    <td className="px-5 py-3 text-gray-600">
                      {JOB_TYPE_LABELS[job.type] ?? job.type}
                    </td>
                    <td className="px-5 py-3 text-gray-500 font-mono text-xs">
                      {job.cron_expression ?? "يدوي"}
                    </td>
                    <td className="px-5 py-3 text-gray-500">{formatDate(job.last_run_at)}</td>
                    <td className="px-5 py-3">
                      <Badge variant="outline" className={
                        job.is_active
                          ? "border-emerald-200 text-emerald-700 bg-emerald-50"
                          : "border-gray-200 text-gray-500 bg-gray-50"
                      }>
                        {job.is_active ? "نشط" : "موقف"}
                      </Badge>
                    </td>
                    <td className="px-5 py-3">
                      {hasDryRun(job) ? (
                        <button
                          onClick={() => handleDryRun(job)}
                          title={isDryRun(job) ? "اضغط للتحويل إلى الوضع المباشر" : "اضغط للعودة إلى الوضع التجريبي"}
                          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors ${
                            isDryRun(job)
                              ? "border-amber-200 text-amber-700 bg-amber-50 hover:bg-amber-100"
                              : "border-emerald-300 text-emerald-700 bg-emerald-50 hover:bg-emerald-100"
                          }`}
                        >
                          {isDryRun(job)
                            ? (<><FlaskConical size={12} /> تجريبي</>)
                            : (<><Zap size={12} /> مباشر</>)}
                        </button>
                      ) : (
                        <span className="text-xs text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm" variant="outline"
                          disabled={running === job.id}
                          onClick={() => handleRun(job)}
                          className="text-emerald-700 border-emerald-200 hover:bg-emerald-50"
                        >
                          {running === job.id ? "جارٍ..." : "تشغيل"}
                        </Button>
                        <Button
                          size="sm" variant="ghost"
                          onClick={() => { setEditing(job); setOpen(true); }}
                          title="تعديل"
                        >
                          <Pencil size={14} />
                        </Button>
                        <Button
                          size="sm" variant="ghost"
                          onClick={() => handleToggle(job)}
                          title={job.is_active ? "إيقاف" : "تفعيل"}
                        >
                          {job.is_active ? <Pause size={14} /> : <Play size={14} />}
                        </Button>
                        <Button
                          size="sm" variant="ghost"
                          onClick={() => handleDelete(job.id)}
                          className="text-red-400 hover:text-red-600 hover:bg-red-50"
                        >
                          <Trash2 size={14} />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      <JobDialog
        key={editing?.id ?? "new"}
        open={open}
        onClose={() => setOpen(false)}
        onSaved={() => { setOpen(false); load(); }}
        initial={editing}
      />
    </div>
  );
}
