"use client";

import { useState, useEffect } from "react";
import { StudentPageData } from "@/lib/types";

interface WeeklyCardProps {
  data: StudentPageData;
}

const DAY_LABELS = ["الأح", "الإث", "الثل", "الأر", "الخم", "الجم", "السب"];

export default function WeeklyCard({ data }: WeeklyCardProps) {
  const { report } = data;
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 500);
    return () => clearTimeout(t);
  }, []);

  if (!report?.saved_pages?.statics && !report?.attendece) return null;

  const statics = report.saved_pages?.statics || [];
  const maxP = Math.max(5, ...statics.map((s) => Math.max(s.required || 0, s.recite || 0)));

  const ma = data.monthly_attendance;
  const attendance = (ma && ma.attend !== undefined ? ma : null) || report.attendece || {
    attend: 0,
    absent: 0,
    excused: 0,
    late: 0,
  };

  return (
    <div className="card">
      <div className="card-label">سجل الحضور الشهري</div>

      {/* Bar chart */}
      {statics.length > 0 && (
        <>
          <div
            style={{
              display: "flex",
              gap: 5,
              alignItems: "flex-end",
              height: 90,
              marginBottom: 8,
            }}
          >
            {statics.map((d, i) => (
              <div key={d.date_key || i} className="bar-wrap">
                <div className="bar-group">
                  <div
                    className="bar bar-target"
                    style={{
                      height: mounted ? `${(d.required / maxP) * 80}px` : "0px",
                      transitionDelay: `${i * 0.05}s`,
                    }}
                  />
                  <div
                    className="bar bar-achieved"
                    style={{
                      height: mounted ? `${(d.recite / maxP) * 80}px` : "0px",
                      transitionDelay: `${i * 0.05 + 0.12}s`,
                    }}
                  />
                </div>
                <div
                  style={{
                    fontSize: 8.5,
                    color: "var(--text-dim)",
                    marginTop: 5,
                    textAlign: "center",
                  }}
                >
                  {DAY_LABELS[i] || d.date_key}
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: 14, marginBottom: 16 }}>
            {[
              ["var(--jade)", "المحقق"],
              ["oklch(0.92 0.008 80)", "الهدف"],
            ].map(([c, l]) => (
              <div
                key={l}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 5,
                  fontSize: 10,
                  color: "var(--text-dim)",
                }}
              >
                <div
                  style={{
                    width: 9,
                    height: 9,
                    borderRadius: 2,
                    background: c,
                    border:
                      c.includes("0.92") ? "1px solid oklch(0.86 0.015 75)" : "none",
                  }}
                />
                {l}
              </div>
            ))}
          </div>
        </>
      )}

      <div className="divider" />

      {/* Attendance */}
      <div
        style={{
          fontSize: 10,
          color: "var(--text-dim)",
          letterSpacing: "0.08em",
          textTransform: "uppercase" as const,
          marginBottom: 11,
          fontWeight: 700,
        }}
      >
        الحضور
      </div>
      <div style={{ display: "flex", gap: 9 }}>
        {[
          {
            label: "حاضر",
            count: attendance.attend,
            color: "var(--jade)",
            bg: "var(--jade-soft)",
          },
          {
            label: "غائب",
            count: attendance.absent,
            color: "var(--rose)",
            bg: "var(--rose-soft)",
          },
          {
            label: "معذور",
            count: attendance.excused,
            color: "var(--amber)",
            bg: "var(--amber-soft)",
          },
        ].map((a) => (
          <div
            key={a.label}
            style={{
              flex: 1,
              background: a.bg,
              borderRadius: 11,
              padding: "11px 8px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontSize: 24,
                fontFamily: "var(--font-amiri), Amiri, serif",
                fontWeight: 700,
                color: a.color,
              }}
            >
              {a.count}
            </div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
              {a.label}
            </div>
          </div>
        ))}
      </div>

      {/* Stacked bar */}
      <div
        style={{
          marginTop: 12,
          display: "flex",
          borderRadius: 99,
          overflow: "hidden",
          height: 5,
          gap: 1,
        }}
      >
        <div style={{ flex: attendance.attend || 1, background: "var(--jade)" }} />
        <div style={{ flex: attendance.absent || 0, background: "var(--rose)" }} />
        <div style={{ flex: attendance.excused || 0, background: "var(--amber)" }} />
      </div>
    </div>
  );
}
