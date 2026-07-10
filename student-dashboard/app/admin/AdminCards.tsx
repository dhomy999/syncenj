"use client";

import { useEffect, useMemo, useState } from "react";
import QRCode from "qrcode";
import type { RosterStudent } from "@/lib/api";
import { logout } from "./actions";

const PER_PAGE = 9; // 3×3 على ورقة A4

function chunk<T>(arr: T[], size: number): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

export default function AdminCards({
  students,
  error,
}: {
  students: RosterStudent[];
  error?: string;
}) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [qrMap, setQrMap] = useState<Record<string, string>>({});

  // عنوان الموقع العام للروابط داخل الباركود.
  // يُفضّل ضبطه عبر NEXT_PUBLIC_SITE_URL، وإلا يُستخدم عنوان المتصفح الحالي.
  const [baseUrl] = useState(() => {
    const env = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "");
    if (env) return env;
    return typeof window !== "undefined" ? window.location.origin : "";
  });

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return students;
    return students.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.student_number.toLowerCase().includes(q) ||
        s.sub_url.toLowerCase().includes(q)
    );
  }, [students, query]);

  // إن لم يُحدَّد شيء، نطبع كل النتائج الظاهرة
  const toPrint = useMemo(
    () =>
      selected.size > 0
        ? students.filter((s) => selected.has(s.sub_url))
        : filtered,
    [students, filtered, selected]
  );

  const toPrintKey = toPrint.map((s) => s.sub_url).join(",");

  // توليد رموز QR لكل بطاقة ستُطبع
  useEffect(() => {
    if (!baseUrl) return;
    let cancelled = false;
    (async () => {
      const updates: Record<string, string> = {};
      for (const s of toPrint) {
        if (qrMap[s.sub_url]) continue;
        try {
          updates[s.sub_url] = await QRCode.toDataURL(
            `${baseUrl}/${s.sub_url}`,
            { margin: 1, width: 320, errorCorrectionLevel: "M" }
          );
        } catch {
          /* تجاهل الفشل لبطاقة واحدة */
        }
      }
      if (!cancelled && Object.keys(updates).length) {
        setQrMap((m) => ({ ...m, ...updates }));
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toPrintKey, baseUrl]);

  function toggle(subUrl: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(subUrl)) next.delete(subUrl);
      else next.add(subUrl);
      return next;
    });
  }

  function selectAllVisible() {
    setSelected(new Set(filtered.map((s) => s.sub_url)));
  }

  function clearSelection() {
    setSelected(new Set());
  }

  const pages = chunk(toPrint, PER_PAGE);
  const readyCount = toPrint.filter((s) => qrMap[s.sub_url]).length;
  const allReady = readyCount === toPrint.length;

  return (
    <div className="admin-shell">
      {/* ── شريط التحكم (لا يُطبع) ── */}
      <header className="admin-controls no-print">
        <div className="admin-controls-row">
          <h1 className="admin-h1">بطاقات الطلاب</h1>
          <form action={logout}>
            <button type="submit" className="admin-btn admin-btn-ghost">
              تسجيل الخروج
            </button>
          </form>
        </div>

        <div className="admin-controls-row">
          <input
            className="admin-input admin-search"
            placeholder="بحث بالاسم أو رقم الطالب…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div className="admin-controls-row admin-controls-actions">
          <span className="admin-count">
            {students.length} طالب · {filtered.length} ظاهر ·{" "}
            <strong>{toPrint.length}</strong> للطباعة
            {selected.size > 0 ? ` (${selected.size} محدد)` : ""}
          </span>
          <div className="admin-actions-btns">
            <button className="admin-btn admin-btn-ghost" onClick={selectAllVisible}>
              تحديد الظاهر
            </button>
            <button
              className="admin-btn admin-btn-ghost"
              onClick={clearSelection}
              disabled={selected.size === 0}
            >
              إلغاء التحديد
            </button>
            <button
              className="admin-btn admin-btn-primary"
              onClick={() => window.print()}
              disabled={toPrint.length === 0 || !allReady}
              title={!allReady ? "جارٍ توليد الباركود…" : undefined}
            >
              {allReady
                ? `طباعة / حفظ PDF (${pages.length} صفحة)`
                : `جارٍ التجهيز ${readyCount}/${toPrint.length}…`}
            </button>
          </div>
        </div>

        {error && (
          <div className="admin-login-error">تعذّر جلب قائمة الطلاب: {error}</div>
        )}
        <div className="admin-hint">
          الباركود يفتح:{" "}
          <code suppressHydrationWarning>
            {baseUrl || "…"}/{`{sub_url}`}
          </code>{" "}
          — كل ورقة A4
          تحتوي 9 بطاقات. للطباعة اختر «حفظ كـ PDF» من نافذة الطباعة.
        </div>
      </header>

      {/* ── منطقة الطباعة: صفحات A4 (3×3) ── */}
      <div className="print-area">
        {pages.length === 0 && (
          <p className="admin-empty no-print">لا توجد بطاقات لعرضها.</p>
        )}
        {pages.map((page, pi) => (
          <section className="print-page" key={pi}>
            <div className="print-grid">
              {page.map((s) => (
                <article
                  className={
                    "id-card" +
                    (selected.has(s.sub_url) ? " id-card-selected" : "")
                  }
                  key={s.sub_url}
                  onClick={() => toggle(s.sub_url)}
                >
                  <div className="id-card-head">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img className="id-card-logo" src="/logo.svg" alt="شعار الجمعية" />
                    <span className="id-card-brand">
                      الدورة الصيفية في مسجد قباء 1448 هـ
                    </span>
                  </div>
                  <div className="id-card-name">{s.name || "—"}</div>
                  <div className="id-card-qr">
                    {qrMap[s.sub_url] ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={qrMap[s.sub_url]} alt={`QR ${s.name}`} />
                    ) : (
                      <div className="id-card-qr-ph" />
                    )}
                  </div>
                  <div className="id-card-number">
                    <span className="id-card-number-label">رقم الطالب</span>
                    <span className="id-card-number-value">
                      {s.student_number}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
