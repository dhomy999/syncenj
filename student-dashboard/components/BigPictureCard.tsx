"use client";

import { useState } from "react";
import ProgressBar from "./ui/ProgressBar";
import { StudentPageData } from "@/lib/types";

interface BigPictureCardProps {
  data: StudentPageData;
}

function calcDate(remaining: number, pPerDay: number): string {
  // 5 working days per week (Fri+Sat off)
  const workingDays = Math.ceil(remaining / Math.max(0.5, pPerDay));
  const calendarDays = Math.ceil(workingDays * (7 / 5));
  const d = new Date();
  d.setDate(d.getDate() + calendarDays);
  return d.toLocaleDateString("ar-SA", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function KhatmCalc({ remaining }: { remaining: number }) {
  const [pages, setPages] = useState(3);
  const result = calcDate(remaining, pages);

  return (
    <div>
      <div
        style={{
          fontSize: 10,
          color: "var(--text-dim)",
          letterSpacing: "0.08em",
          textTransform: "uppercase" as const,
          fontWeight: 700,
          marginBottom: 12,
        }}
      >
        حاسبة الختم التفاعلية
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 4,
        }}
      >
        <span style={{ fontSize: 13, color: "var(--text-muted)", flex: 1 }}>
          صفحات يوميا:
        </span>
        <div
          style={{ display: "flex", alignItems: "center", gap: 8, direction: "ltr" }}
        >
          <button
            className="step-btn"
            onClick={() => setPages((p) => Math.max(0.5, p - 0.5))}
          >
            -
          </button>
          <input
            className="calc-input"
            type="number"
            min="0.5"
            max="20"
            step="0.5"
            value={pages}
            onChange={(e) => setPages(Number(e.target.value) || 0.5)}
          />
          <button
            className="step-btn"
            onClick={() => setPages((p) => Math.min(20, p + 0.5))}
          >
            +
          </button>
        </div>
      </div>
      <div className="result-box">
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
          تاريخ الختم المتوقع
        </span>
        <span
          style={{
            fontFamily: "var(--font-amiri), Amiri, serif",
            fontSize: 17,
            fontWeight: 700,
            color: "var(--gold)",
          }}
        >
          {result}
        </span>
      </div>
    </div>
  );
}

export default function BigPictureCard({ data }: BigPictureCardProps) {
  const { report } = data;
  const qp = data.quran_progress;

  // Use quran_progress if available, otherwise fallback to pages_summary
  const hasQP = qp && qp.total > 0 && qp.current_page > 0;
  const completed = Math.round(hasQP ? qp.completed : (report?.student?.pages_summary?.completed || 0));
  const remaining = Math.round(hasQP ? qp.remaining : (report?.student?.pages_summary?.remaining || 0));
  const total = Math.round(hasQP ? 604 : (report?.student?.pages_summary?.total_pages || 604));
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

  if (!hasQP && !report?.student?.pages_summary) return null;

  const pace = qp?.pages_per_day || 0;
  const predicted = pace > 0 ? calcDate(remaining, pace) : "";

  return (
    <div className="card">
      <div className="card-label">الصورة الكبرى</div>

      {/* Progress section */}
      <div style={{ marginBottom: 18 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "baseline",
            marginBottom: 9,
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-amiri), Amiri, serif",
              fontSize: 18,
              fontWeight: 700,
            }}
          >
            تقدم حفظ المصحف
          </span>
          <span
            style={{
              fontFamily: "var(--font-amiri), Amiri, serif",
              fontSize: 30,
              fontWeight: 700,
              color: "var(--gold)",
            }}
          >
            {pct}%
          </span>
        </div>
        <ProgressBar pct={pct} variant="gold" />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: 7,
            fontSize: 11,
            color: "var(--text-muted)",
          }}
        >
          <span>{completed} صفحة محفوظة من {total}</span>
          <span>{remaining} صفحة متبقية</span>
        </div>
      </div>

      <div className="divider" />

      {/* Velocity prediction */}
      <div style={{ marginBottom: 18 }}>
        <div
          style={{
            fontSize: 10,
            color: "var(--text-dim)",
            letterSpacing: "0.08em",
            textTransform: "uppercase" as const,
            fontWeight: 700,
            marginBottom: 10,
          }}
        >
          متنبئ سرعة الختم
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>
              بالسرعة الحالية ({pace} صفحة / يوم)
            </div>
            <div
              style={{
                fontFamily: "var(--font-amiri), Amiri, serif",
                fontSize: 18,
                fontWeight: 700,
              }}
            >
              ختم متوقع:{" "}
              <span style={{ color: "var(--gold)" }}>{predicted || "لا توجد بيانات كافية"}</span>
            </div>
          </div>
          <div style={{ fontSize: 30, marginRight: 4 }}>🕌</div>
        </div>
      </div>

      <div className="divider" />
      <KhatmCalc remaining={remaining} />
    </div>
  );
}
