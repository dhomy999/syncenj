"use client";

import { useState } from "react";
import { jobsApi, Job, JobType } from "@/lib/api";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

const JOB_TYPES: { value: JobType; label: string }[] = [
  // العمليات الرئيسية الثلاث
  { value: "add_students",                label: "تسجيل الطلاب الجدد" },
  { value: "open_episodes",               label: "فتح الحلقات (من المعلم)" },
  { value: "sync_attend100",              label: "مزامنة الحضور (attend100)" },
  { value: "assign_level",                label: "إسناد المستوى (إنشاء خطة)" },
  { value: "teacher_recite",              label: "إدخال التسميع (تطبيق المعلّم)" },
  // مهام مساندة
  { value: "sync_students",               label: "مطابقة الطلاب (ربط enjazi_id)" },
  { value: "sync_recitation",             label: "مزامنة التسميع الكامل" },
  { value: "sync_episodes",               label: "مزامنة الحلقات" },
  { value: "export_students",             label: "تصدير الطلاب" },
];

type Frequency = "manual" | "minutely" | "hourly" | "daily" | "weekly" | "monthly" | "advanced";

const FREQ_LABELS: { value: Frequency; label: string }[] = [
  { value: "manual",   label: "يدوي فقط" },
  { value: "minutely", label: "كل دقيقة" },
  { value: "hourly",   label: "كل ساعة" },
  { value: "daily",    label: "كل يوم" },
  { value: "weekly",   label: "كل أسبوع" },
  { value: "monthly",  label: "كل شهر" },
  { value: "advanced", label: "متقدّم (cron يدوي)" },
];

const WEEKDAYS = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"];

// تعبير cron «مركّب» (نطاقات/قوائم/أسماء أيام) لا يمثّله المنشئ البسيط — يُحرّر يدويًا كما هو.
function isComplexCron(cron: string): boolean {
  const p = cron.trim().split(/\s+/);
  if (p.length !== 5) return true;
  return p.some((f) => /[,\-/a-zA-Z]/.test(f));
}

function toCron(
  freq: Frequency,
  minute: number,
  hour: number,
  weekday: number,
  monthday: number,
  raw: string,
): string | null {
  switch (freq) {
    case "manual":   return null;
    case "advanced": return raw.trim() || null;
    case "minutely": return "* * * * *";
    case "hourly":   return `${minute} * * * *`;
    case "daily":    return `${minute} ${hour} * * *`;
    case "weekly":   return `${minute} ${hour} * * ${weekday}`;
    case "monthly":  return `${minute} ${hour} ${monthday} * *`;
  }
}

function parseCron(cron: string | null) {
  const defaults = { freq: "manual" as Frequency, minute: 0, hour: 6, weekday: 0, monthday: 1, raw: "" };
  if (!cron) return defaults;
  // التعابير المركّبة (مثل "0 5-22 * * *" أو "0 4 * * sat,sun") تُحرّر في الوضع المتقدّم دون إفسادها.
  if (isComplexCron(cron)) return { ...defaults, freq: "advanced" as Frequency, raw: cron };
  const p = cron.trim().split(/\s+/);
  if (p.length !== 5) return defaults;
  const [min, hr, dom, , dow] = p;
  if (min === "*" && hr === "*")   return { ...defaults, freq: "minutely" as Frequency };
  if (hr  === "*" && dom === "*")  return { ...defaults, freq: "hourly"   as Frequency, minute: +min || 0 };
  if (dom === "*" && dow === "*")  return { ...defaults, freq: "daily"    as Frequency, minute: +min || 0, hour: +hr || 0 };
  if (dom === "*")                 return { ...defaults, freq: "weekly"   as Frequency, minute: +min || 0, hour: +hr || 0, weekday: +dow || 0 };
  return                                  { ...defaults, freq: "monthly"  as Frequency, minute: +min || 0, hour: +hr || 0, monthday: +dom || 1 };
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: Job | null;
}

export function JobDialog({ open, onClose, onSaved, initial }: Props) {
  const parsed = parseCron(initial?.cron_expression ?? null);

  const [form, setForm] = useState({
    name:        initial?.name        ?? "",
    type:        initial?.type        ?? "sync_episodes" as JobType,
    description: initial?.description ?? "",
    is_active:   initial?.is_active   ?? true,
  });

  const [freq,     setFreq]     = useState<Frequency>(parsed.freq);
  const [hour,     setHour]     = useState(parsed.hour);
  const [minute,   setMinute]   = useState(parsed.minute);
  const [weekday,  setWeekday]  = useState(parsed.weekday);
  const [monthday, setMonthday] = useState(parsed.monthday);
  const [rawCron,  setRawCron]  = useState(parsed.raw);
  const [saving,   setSaving]   = useState(false);

  const set = (k: string, v: unknown) => setForm((p) => ({ ...p, [k]: v }));

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      const payload = { ...form, cron_expression: toCron(freq, minute, hour, weekday, monthday, rawCron) };
      if (initial) await jobsApi.update(initial.id, payload);
      else         await jobsApi.create(payload);
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  const needsTime    = freq === "daily" || freq === "weekly" || freq === "monthly";
  const cronPreview  = freq !== "manual" ? toCron(freq, minute, hour, weekday, monthday, rawCron) : null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md" dir="rtl">
        <DialogHeader>
          <DialogTitle>{initial ? "تعديل المهمة" : "مهمة جديدة"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Name */}
          <Field label="اسم المهمة *">
            <input
              className="input-base"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="مثال: تصدير المنشآت يومياً"
            />
          </Field>

          {/* Type */}
          <Field label="نوع المهمة">
            <select className="input-base" value={form.type} onChange={(e) => set("type", e.target.value)}>
              {JOB_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </Field>

          {/* Frequency */}
          <Field label="تكرار التشغيل">
            <select className="input-base" value={freq} onChange={(e) => setFreq(e.target.value as Frequency)}>
              {FREQ_LABELS.map((f) => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </select>
          </Field>

          {/* Hourly: minute only */}
          {freq === "hourly" && (
            <Field label="عند الدقيقة">
              <div className="flex items-center gap-2">
                <select className="input-base w-24" value={minute} onChange={(e) => setMinute(+e.target.value)}>
                  {Array.from({ length: 60 }, (_, i) => (
                    <option key={i} value={i}>{String(i).padStart(2, "0")}</option>
                  ))}
                </select>
                <span className="text-xs text-gray-400">من كل ساعة</span>
              </div>
            </Field>
          )}

          {/* Daily / Weekly / Monthly: time */}
          {needsTime && (
            <Field label="الوقت">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span className="text-sm text-gray-500">س</span>
                  <select className="input-base w-20" value={hour} onChange={(e) => setHour(+e.target.value)}>
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>{String(i).padStart(2, "0")}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-sm text-gray-500">د</span>
                  <select className="input-base w-20" value={minute} onChange={(e) => setMinute(+e.target.value)}>
                    {[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55].map((m) => (
                      <option key={m} value={m}>{String(m).padStart(2, "0")}</option>
                    ))}
                  </select>
                </div>
              </div>
            </Field>
          )}

          {/* Weekly: day of week */}
          {freq === "weekly" && (
            <Field label="يوم الأسبوع">
              <select className="input-base" value={weekday} onChange={(e) => setWeekday(+e.target.value)}>
                {WEEKDAYS.map((d, i) => (
                  <option key={i} value={i}>{d}</option>
                ))}
              </select>
            </Field>
          )}

          {/* Monthly: day of month */}
          {freq === "monthly" && (
            <Field label="يوم الشهر">
              <div className="flex items-center gap-2">
                <select className="input-base w-24" value={monthday} onChange={(e) => setMonthday(+e.target.value)}>
                  {Array.from({ length: 28 }, (_, i) => (
                    <option key={i + 1} value={i + 1}>{i + 1}</option>
                  ))}
                </select>
                <span className="text-xs text-gray-400">من كل شهر</span>
              </div>
            </Field>
          )}

          {/* Advanced: raw cron */}
          {freq === "advanced" && (
            <Field label="تعبير cron (5 حقول)">
              <input
                className="input-base font-mono text-sm"
                dir="ltr"
                value={rawCron}
                onChange={(e) => setRawCron(e.target.value)}
                placeholder="0 5-22 * * *"
              />
              <p className="text-xs text-gray-400 mt-1">
                دقيقة ساعة يوم-الشهر شهر يوم-الأسبوع — تدعم النطاقات (5-22) وأسماء الأيام (sat,sun).
              </p>
            </Field>
          )}

          {/* Cron preview */}
          {cronPreview && (
            <p className="text-xs text-gray-400 bg-gray-50 rounded px-3 py-2 font-mono" dir="ltr">
              {cronPreview}
            </p>
          )}

          {/* Description */}
          <Field label="الوصف (اختياري)">
            <textarea
              className="input-base resize-none h-16"
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
            />
          </Field>

          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => set("is_active", e.target.checked)}
            />
            تفعيل المهمة فوراً
          </label>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>إلغاء</Button>
          <Button
            onClick={handleSave}
            disabled={saving || !form.name.trim()}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {saving ? "جارٍ الحفظ..." : "حفظ"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
    </div>
  );
}
