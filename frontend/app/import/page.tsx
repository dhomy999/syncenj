"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { dataApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Trash2, Upload, CheckCircle, XCircle, AlertCircle, Loader2 } from "lucide-react";

interface Facility { id: number; name: string }
interface Episode  { id: number; name: string; institution_id?: number }

interface StudentRow {
  username:       string;
  name:           string;
  date_of_birth:  string;
  gender_id:      number;
  phone:          string;
  guardian_phone: string;
  email:          string;
}

type ResultStatus = "pending" | "processing" | "success" | "requested" | "skipped" | "failed";

interface LiveResult {
  idx:      number;
  username: string;
  name:     string;
  status:   ResultStatus;
  error:    string | null;
}

type ImportState = "idle" | "running" | "done";

const EMPTY_ROW = (): StudentRow => ({
  username: "", name: "", date_of_birth: "", gender_id: 1,
  phone: "", guardian_phone: "", email: "",
});

const COLUMNS: { key: keyof StudentRow; label: string; width: string; required?: boolean }[] = [
  { key: "username",       label: "رقم الهوية",     width: "120px", required: true },
  { key: "name",           label: "الاسم الكامل",   width: "180px", required: true },
  { key: "date_of_birth",  label: "تاريخ الميلاد",  width: "130px", required: true },
  { key: "gender_id",      label: "الجنس",          width: "90px",  required: true },
  { key: "phone",          label: "جوال الطالب",    width: "120px" },
  { key: "guardian_phone", label: "جوال ولي الأمر", width: "130px" },
  { key: "email",          label: "البريد",         width: "160px" },
];

// ── تطبيع رقم الجوال ─────────────────────────────────────────────────────────

function normalizePhone(raw: string): string {
  let p = raw.trim();
  if (!p) return p;
  p = p.replace(/\s+/g, "");          // إزالة المسافات
  if (p.startsWith("+966")) p = p.slice(4);
  else if (p.startsWith("966"))  p = p.slice(3);
  if (p.startsWith("0"))  p = p.slice(1);
  return p;
}

// ── تحويل التاريخ الهجري إلى ميلادي ──────────────────────────────────────────

function hijriToGregorian(hy: number, hm: number, hd: number) {
  // التقويم الإسلامي الجدولي → رقم اليوم الجولياني
  const jd = hd
    + Math.ceil(29.5001 * (hm - 1))
    + (hy - 1) * 354
    + Math.floor((3 + 11 * hy) / 30)
    + 1948440 - 385;

  // رقم اليوم الجولياني → ميلادي
  let l = jd + 68569;
  const n = Math.floor(4 * l / 146097);
  l = l - Math.floor((146097 * n + 3) / 4);
  const i = Math.floor(4000 * (l + 1) / 1461001);
  l = l - Math.floor(1461 * i / 4) + 31;
  const j = Math.floor(80 * l / 2447);
  const day   = l - Math.floor(2447 * j / 80);
  l = Math.floor(j / 11);
  const month = j + 2 - 12 * l;
  const year  = 100 * (n - 49) + i + l;
  return { year, month, day };
}

function normalizeDate(raw: string): string {
  const s = raw.trim().replace(/\//g, "-");
  const m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (!m) return raw;

  const year  = parseInt(m[1]);
  const month = parseInt(m[2]);
  const day   = parseInt(m[3]);
  const pad   = (n: number) => String(n).padStart(2, "0");

  if (year >= 1900) {
    // ميلادي — إعادة تنسيق فقط
    return `${year}-${pad(month)}-${pad(day)}`;
  }

  if (year >= 1200 && year < 1500) {
    // هجري — تحويل إلى ميلادي
    const g = hijriToGregorian(year, month, day);
    return `${g.year}-${pad(g.month)}-${pad(g.day)}`;
  }

  return raw;
}

// ── قواعد التحقق ─────────────────────────────────────────────────────────────

type RowErrors = Partial<Record<keyof StudentRow, string>>;

function validateRow(row: StudentRow): RowErrors {
  const err: RowErrors = {};
  const id   = row.username.trim();
  const name = row.name.trim();
  const dob  = row.date_of_birth.trim();
  const ph   = row.phone.trim();
  const gph  = row.guardian_phone.trim();

  // رقم الهوية: أقل من 4 خانات
  if (id && id.length < 4)
    err.username = "رقم الهوية أقل من 4 خانات";

  // الاسم الكامل: أقل من كلمتين
  if (name && name.split(/\s+/).filter(Boolean).length < 2)
    err.name = "الاسم يجب أن يحتوي على كلمتين على الأقل";

  // تاريخ الميلاد: YYYY-MM-DD أو YYYY/MM/DD
  if (dob && !/^\d{4}[-/]\d{2}[-/]\d{2}$/.test(dob))
    err.date_of_birth = "الصيغة المطلوبة: YYYY-MM-DD أو YYYY/MM/DD";

  // جوال الطالب: يبدأ بـ 5
  if (ph && !/^5\d+$/.test(ph))
    err.phone = "يجب أن يبدأ بـ 5 (بدون 0 أو 966+)";

  // جوال ولي الأمر: نفس القاعدة
  if (gph && !/^5\d+$/.test(gph))
    err.guardian_phone = "يجب أن يبدأ بـ 5 (بدون 0 أو 966+)";

  return err;
}

function StatusBadge({ status }: { status: ResultStatus }) {
  if (status === "pending")    return <span className="text-xs text-gray-300">—</span>;
  if (status === "processing") return <Loader2 size={14} className="animate-spin text-blue-500 inline" />;
  const styles = {
    success:   "border-emerald-200 text-emerald-700 bg-emerald-50",
    requested: "border-blue-200   text-blue-700   bg-blue-50",
    skipped:   "border-amber-200  text-amber-700  bg-amber-50",
    failed:    "border-red-200    text-red-700    bg-red-50",
  };
  const labels = { success: "تمت الإضافة", requested: "طلب مُرسَل", skipped: "مسجل مسبقاً", failed: "فشل" };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

export default function ImportPage() {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [episodes,   setEpisodes]   = useState<Episode[]>([]);
  const [instId,     setInstId]     = useState("");
  const [episodeId,  setEpisodeId]  = useState("");
  const [rows,       setRows]       = useState<StudentRow[]>([EMPTY_ROW()]);

  const [importState, setImportState] = useState<ImportState>("idle");
  const [liveResults, setLiveResults] = useState<LiveResult[]>([]);
  const [progress,    setProgress]    = useState({ current: 0, total: 0 });
  const [summary,     setSummary]     = useState({ success: 0, requested: 0, skipped: 0, failed: 0 });
  const [parseErrors, setParseErrors] = useState<{ row: number; error: string }[]>([]);

  const resultsEndRef = useRef<HTMLDivElement>(null);
  const abortRef      = useRef<AbortController | null>(null);

  useEffect(() => {
    dataApi.facilities().then((r) => setFacilities(r.data.data as unknown as Facility[]));
    dataApi.episodes().then((r)   => setEpisodes(r.data.data as unknown as Episode[]));
  }, []);

  // سكرول تلقائي لآخر نتيجة
  useEffect(() => {
    resultsEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [liveResults.length]);

  const filteredEpisodes = instId
    ? episodes.filter((e) => String(e.institution_id) === instId)
    : [];

  const handleCellPaste = useCallback((
    e: React.ClipboardEvent<HTMLInputElement>,
    rowIdx: number,
    colKey: keyof StudentRow,
  ) => {
    const text = e.clipboardData.getData("text");
    if (!text) return;
    const lines = text.trim().split(/\r?\n/);
    if (lines.length > 1) {
      e.preventDefault();
      setRows((prev) => {
        const next = [...prev];
        lines.forEach((line, offset) => {
          const raw = line.split("\t")[0].trim();
          const val = (colKey === "phone" || colKey === "guardian_phone")
            ? normalizePhone(raw) : raw;
          const target = rowIdx + offset;
          if (target < next.length) {
            next[target] = { ...next[target], [colKey]: val };
          } else {
            const newRow = EMPTY_ROW();
            newRow[colKey] = val as never;
            next.push(newRow);
          }
        });
        return next;
      });
    }
  }, []);

  function updateCell(i: number, key: keyof StudentRow, val: string | number) {
    const normalized = (key === "phone" || key === "guardian_phone")
      ? normalizePhone(val as string)
      : val;
    setRows((prev) => { const n = [...prev]; n[i] = { ...n[i], [key]: normalized }; return n; });
  }

  function addRow()       { setRows((prev) => [...prev, EMPTY_ROW()]); }
  function deleteRow(i: number) {
    setRows((prev) => prev.length === 1 ? [EMPTY_ROW()] : prev.filter((_, idx) => idx !== i));
  }

  async function handleImport() {
    if (!instId || !episodeId) return;
    const validRows = rows
      .filter((r) => r.username.trim() && r.name.trim() && r.date_of_birth.trim())
      .map((r) => ({
        ...r,
        date_of_birth:  normalizeDate(r.date_of_birth),
        phone:          normalizePhone(r.phone),
        guardian_phone: normalizePhone(r.guardian_phone),
      }));
    if (validRows.length === 0) return;

    // إعادة تعيين الحالة
    setImportState("running");
    setParseErrors([]);
    setSummary({ success: 0, requested: 0, skipped: 0, failed: 0 });
    setProgress({ current: 0, total: validRows.length });
    setLiveResults(validRows.map((r, i) => ({
      idx: i + 1, username: r.username, name: r.name, status: "pending", error: null,
    })));

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${baseUrl}/api/import/batch/stream`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ institution_id: instId, episode_id: Number(episodeId), students: validRows }),
        signal:  ctrl.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }

      const reader  = res.body!.getReader();
      const decoder = new TextDecoder();
      let   buffer  = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop()!;

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const event = JSON.parse(line.slice(6));

          if (event.type === "start") {
            setParseErrors(event.parse_errors ?? []);
            setProgress({ current: 0, total: event.total });
          }

          if (event.type === "result") {
            const { idx, status, error } = event;

            // علامة "جارٍ المعالجة" على الطالب التالي
            setLiveResults((prev) => prev.map((r) => {
              if (r.idx === idx) return { ...r, status, error };
              if (r.idx === idx + 1 && r.status === "pending") return { ...r, status: "processing" };
              return r;
            }));

            setProgress((p) => ({ ...p, current: idx }));
            setSummary((s) => ({
              success:   s.success   + (status === "success"   ? 1 : 0),
              requested: s.requested + (status === "requested" ? 1 : 0),
              skipped:   s.skipped   + (status === "skipped"   ? 1 : 0),
              failed:    s.failed    + (status === "failed"    ? 1 : 0),
            }));
          }

          if (event.type === "done") {
            setImportState("done");
          }
        }
      }
    } catch (err: unknown) {
      if ((err as Error)?.name !== "AbortError") {
        alert((err as Error)?.message ?? "حدث خطأ غير متوقع");
      }
      setImportState("done");
    }
  }

  function handleStop() {
    abortRef.current?.abort();
  }

  const validCount  = rows.filter((r) => r.username.trim() && r.name.trim() && r.date_of_birth.trim()).length;
  const isRunning   = importState === "running";

  // حساب الأخطاء لكل صف — فقط للصفوف التي تحتوي بيانات
  const rowErrors: RowErrors[] = rows.map((r) =>
    (r.username || r.name || r.date_of_birth) ? validateRow(r) : {}
  );
  const errorRowCount = rowErrors.filter((e) => Object.keys(e).length > 0).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">إضافة طلاب بشكل جماعي</h1>
        <p className="text-sm text-gray-500 mt-1">حدد المنشأة والحلقة، ثم أدخل البيانات أو الصقها من Excel</p>
      </div>

      {/* المنشأة والحلقة */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">المنشأة</label>
              <select
                className="input-base w-full"
                value={instId}
                onChange={(e) => { setInstId(e.target.value); setEpisodeId(""); }}
                disabled={isRunning}
              >
                <option value="">— اختر المنشأة —</option>
                {facilities.map((f) => (
                  <option key={f.id} value={String(f.id)}>{f.name}</option>
                ))}
              </select>
              {facilities.length === 0 && (
                <p className="text-xs text-amber-600 mt-1">اذهب إلى المنشآت واضغط تحديث أولاً</p>
              )}
            </div>
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">الحلقة</label>
              <select
                className="input-base w-full"
                value={episodeId}
                onChange={(e) => setEpisodeId(e.target.value)}
                disabled={!instId || isRunning}
              >
                <option value="">— اختر الحلقة —</option>
                {filteredEpisodes.map((e) => (
                  <option key={e.id} value={String(e.id)}>{e.name}</option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* الجدول التفاعلي — يُخفى أثناء التشغيل */}
      {importState === "idle" && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-base">بيانات الطلاب</CardTitle>
              <p className="text-xs text-gray-400 mt-0.5">
                انقر على خلية وعدّل، أو <strong>الصق</strong> عموداً كاملاً من Excel
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">{validCount} طالب جاهز</span>
              <Button variant="outline" size="sm" onClick={addRow} className="flex items-center gap-1">
                <Plus size={14} /> إضافة صف
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-gray-500 text-right">
                    <th className="px-2 py-2 font-medium w-8 text-center">#</th>
                    {COLUMNS.map((c) => (
                      <th key={c.key} className="px-2 py-2 font-medium whitespace-nowrap" style={{ minWidth: c.width }}>
                        {c.label}{c.required && <span className="text-red-400 mr-0.5">*</span>}
                      </th>
                    ))}
                    <th className="px-2 py-2 w-8" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {rows.map((row, i) => {
                    const errs = rowErrors[i] ?? {};
                    const hasErr = Object.keys(errs).length > 0;
                    return (
                      <tr key={i} className={hasErr ? "bg-red-50/40" : "hover:bg-gray-50"}>
                        <td className="px-2 py-1 text-center text-xs">
                          {hasErr
                            ? <span className="text-red-400 font-bold">!</span>
                            : <span className="text-gray-400">{i + 1}</span>
                          }
                        </td>
                        {COLUMNS.map((col) => {
                          const cellErr = errs[col.key];
                          return (
                            <td key={col.key} className="px-1 py-1">
                              {col.key === "gender_id" ? (
                                <select
                                  className="input-base w-full text-xs py-1"
                                  value={row.gender_id}
                                  onChange={(e) => updateCell(i, "gender_id", Number(e.target.value))}
                                >
                                  <option value={1}>ذكر</option>
                                  <option value={2}>أنثى</option>
                                </select>
                              ) : (
                                <div className="relative group">
                                  <input
                                    className={`input-base w-full text-xs py-1 ${cellErr ? "border-red-400 bg-red-50 focus:ring-red-300" : ""}`}
                                    value={row[col.key] as string}
                                    placeholder={col.key === "date_of_birth" ? "YYYY-MM-DD أو هجري" : ""}
                                    onChange={(e) => updateCell(i, col.key, e.target.value)}
                                    onBlur={col.key === "date_of_birth"
                                      ? (e) => updateCell(i, "date_of_birth", normalizeDate(e.target.value))
                                      : undefined}
                                    onPaste={(e) => handleCellPaste(e, i, col.key)}
                                  />
                                  {cellErr && (
                                    <div className="absolute z-10 bottom-full mb-1 right-0 bg-red-600 text-white text-xs rounded px-2 py-1 whitespace-nowrap hidden group-hover:block shadow-md">
                                      {cellErr}
                                    </div>
                                  )}
                                </div>
                              )}
                            </td>
                          );
                        })}
                        <td className="px-1 py-1 text-center">
                          <button onClick={() => deleteRow(i)} className="text-gray-300 hover:text-red-400 transition-colors">
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="px-4 py-3 border-t border-gray-100 space-y-2">
              {errorRowCount > 0 && (
                <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                  <XCircle size={13} />
                  <span>
                    <strong>{errorRowCount} صف</strong> {errorRowCount === 1 ? "يحتوي على خطأ" : "تحتوي على أخطاء"} — مرّر الماوس على الخلية الحمراء لرؤية التفاصيل
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-400 font-mono">
                  رقم الهوية · الاسم · تاريخ الميلاد · الجنس · جوال الطالب · جوال ولي الأمر · البريد
                </p>
                <Button
                  onClick={handleImport}
                  disabled={!instId || !episodeId || validCount === 0 || errorRowCount > 0}
                  className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-50"
                >
                  <Upload size={15} />
                  إضافة {validCount} طالب
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* نافذة التقدم الحية */}
      {(importState === "running" || importState === "done") && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                {isRunning && <Loader2 size={16} className="animate-spin text-emerald-600" />}
                {isRunning
                  ? `جارٍ الإضافة — ${progress.current} / ${progress.total}`
                  : `اكتمل — ${progress.total} طالب`}
              </CardTitle>
              <div className="flex items-center gap-4 text-sm">
                <span className="flex items-center gap-1 text-emerald-700">
                  <CheckCircle size={14} /> {summary.success} أُضيف
                </span>
                {summary.requested > 0 && (
                  <span className="flex items-center gap-1 text-blue-600">
                    <AlertCircle size={14} /> {summary.requested} طلب مُرسَل
                  </span>
                )}
                {summary.skipped > 0 && (
                  <span className="flex items-center gap-1 text-amber-600">
                    <AlertCircle size={14} /> {summary.skipped} متجاوز
                  </span>
                )}
                <span className="flex items-center gap-1 text-red-600">
                  <XCircle size={14} /> {summary.failed} فشل
                </span>
                {isRunning && (
                  <Button variant="outline" size="sm" onClick={handleStop}
                    className="text-red-600 border-red-200 hover:bg-red-50 text-xs h-7">
                    إيقاف
                  </Button>
                )}
                {importState === "done" && (
                  <Button variant="outline" size="sm" onClick={() => { setImportState("idle"); setLiveResults([]); }}
                    className="text-xs h-7">
                    إضافة دفعة جديدة
                  </Button>
                )}
              </div>
            </div>

            {/* شريط التقدم */}
            <div className="mt-3 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all duration-500"
                style={{ width: progress.total ? `${(progress.current / progress.total) * 100}%` : "0%" }}
              />
            </div>
          </CardHeader>

          <CardContent className="p-0">
            {parseErrors.length > 0 && (
              <div className="mx-4 mb-3 bg-red-50 border border-red-200 rounded p-2 text-xs text-red-700 space-y-0.5">
                {parseErrors.map((e, i) => <p key={i}>الصف {e.row}: {e.error}</p>)}
              </div>
            )}

            <div className="max-h-[420px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-gray-50">
                  <tr className="text-gray-500 text-right">
                    <th className="px-4 py-2 font-medium w-10 text-center">#</th>
                    <th className="px-4 py-2 font-medium">رقم الهوية</th>
                    <th className="px-4 py-2 font-medium">الاسم</th>
                    <th className="px-4 py-2 font-medium">الحالة</th>
                    <th className="px-4 py-2 font-medium">ملاحظة</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {liveResults.map((r) => (
                    <tr key={r.idx} className={`transition-colors ${
                      r.status === "processing" ? "bg-blue-50" :
                      r.status === "success"    ? "bg-emerald-50/40" :
                      r.status === "requested"  ? "bg-blue-50/40" :
                      r.status === "failed"     ? "bg-red-50/40" : ""
                    }`}>
                      <td className="px-4 py-2 text-center text-xs text-gray-400">{r.idx}</td>
                      <td className="px-4 py-2 font-mono text-xs">{r.username}</td>
                      <td className="px-4 py-2">{r.name}</td>
                      <td className="px-4 py-2"><StatusBadge status={r.status} /></td>
                      <td className="px-4 py-2 text-xs text-gray-400 max-w-[200px] truncate" title={r.error ?? ""}>
                        {r.error ?? ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div ref={resultsEndRef} />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
