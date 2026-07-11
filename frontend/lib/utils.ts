import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("ar-SA", {
    dateStyle: "short",
    timeStyle: "short",
    hour12: false,
  }).format(new Date(iso));
}

export const JOB_TYPE_LABELS: Record<string, string> = {
  // العمليات الرئيسية الثلاث
  add_students:                "تسجيل الطلاب الجدد",
  open_episodes:               "فتح الحلقات (من المعلم)",
  sync_attend100:              "مزامنة الحضور (attend100)",
  assign_level:                "إسناد المستوى (إنشاء خطة)",
  teacher_recite:              "إدخال التسميع (تطبيق المعلّم)",
  // مهام مساندة
  sync_students:               "مطابقة الطلاب (ربط enjazi_id)",
  sync_recitation:             "مزامنة التسميع الكامل",
  sync_episodes:               "مزامنة الحلقات",
  export_students:             "تصدير الطلاب",
  register_students:           "تسجيل الطلاب (جماعي — قديم)",
  sync_register_students:      "تسجيل الطلاب اليومي (قديم)",
};

/**
 * تصدير مصفوفة من الكائنات كملف CSV مع دعم UTF-8 BOM (لـ Excel).
 * @param rows  البيانات
 * @param columns تعريف الأعمدة: { key, label }
 * @param filename اسم الملف بدون امتداد
 */
export function exportCsv(
  rows: Record<string, unknown>[],
  columns: { key: string; label: string }[],
  filename: string
) {
  const header = columns.map((c) => `"${c.label}"`).join(",");
  const body = rows
    .map((row) =>
      columns
        .map((c) => {
          const val = String(row[c.key] ?? "");
          return `"${val.replace(/"/g, '""')}"`;
        })
        .join(",")
    )
    .join("\r\n");

  // BOM لضمان ظهور العربية بشكل صحيح في Excel
  const bom = "\uFEFF";
  const blob = new Blob([bom + header + "\r\n" + body], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export const STATUS_LABELS: Record<string, string> = {
  success: "نجح",
  failed:  "فشل",
  running: "جارٍ",
  skipped: "تخطّى",
};
