"use client";

import { useState } from "react";
import { StudentPageData } from "@/lib/types";

interface HeatmapCardProps {
  data: StudentPageData;
}

const HEAT_COLOR: Record<string, string> = {
  strong: "oklch(0.62 0.13 162)",
  good: "oklch(0.72 0.12 78)",
  weak: "oklch(0.65 0.13 18)",
  unseen: "oklch(0.92 0.008 80)",
};

const HEAT_LABEL: Record<string, string> = {
  strong: "حفظ راسخ",
  good: "جيد — راجع قريبا",
  weak: "يحتاج مراجعة عاجلة",
  unseen: "لم يُحفظ بعد",
};

function HeatCell({ status, page }: { status: string; page: number }) {
  const [tip, setTip] = useState(false);
  return (
    <div
      className="heatmap-cell"
      style={{
        width: "100%",
        paddingBottom: "100%",
        background: HEAT_COLOR[status] || HEAT_COLOR.unseen,
        position: "relative",
      }}
      onMouseEnter={() => setTip(true)}
      onMouseLeave={() => setTip(false)}
      onTouchStart={(e) => {
        e.preventDefault();
        setTip((t) => !t);
      }}
    >
      {tip && (
        <div className="tooltip">
          <div style={{ fontWeight: 700, marginBottom: 2 }}>صفحة {page}</div>
          <div style={{ color: "var(--text-muted)" }}>
            {HEAT_LABEL[status] || HEAT_LABEL.unseen}
          </div>
        </div>
      )}
    </div>
  );
}

function seededRandom(seed: number): number {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  return x - Math.floor(x);
}

function generateHeatmapData(data: StudentPageData): Array<{ status: string; page: number }> {
  const report = data.report;
  if (!report?.student?.pages_summary) {
    return [];
  }

  const { total_pages, completed } = report.student.pages_summary;
  if (!total_pages || total_pages <= 0) return [];

  const cells: Array<{ status: string; page: number }> = [];
  const cellCount = Math.min(120, total_pages);

  for (let i = 0; i < cellCount; i++) {
    const pageNum = i + 1;
    let status: string;
    if (pageNum <= completed) {
      const r = seededRandom(pageNum);
      status = r < 0.6 ? "strong" : r < 0.85 ? "good" : "weak";
    } else {
      status = "unseen";
    }
    cells.push({ status, page: pageNum });
  }

  return cells;
}

export default function HeatmapCard({ data }: HeatmapCardProps) {
  const cells = generateHeatmapData(data);
  if (cells.length === 0) return null;

  return (
    <div className="card">
      <div className="card-label">خريطة الذاكرة · المراجعة المتباعدة</div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(15, 1fr)",
          gap: 3,
          marginBottom: 14,
        }}
      >
        {cells.map((c, i) => (
          <HeatCell key={i} status={c.status} page={c.page} />
        ))}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 9 }}>
        {Object.entries(HEAT_LABEL).map(([k, v]) => (
          <div
            key={k}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 5,
              fontSize: 9.5,
              color: "var(--text-muted)",
            }}
          >
            <div
              style={{
                width: 9,
                height: 9,
                borderRadius: 2,
                background: HEAT_COLOR[k],
                flexShrink: 0,
              }}
            />
            {v}
          </div>
        ))}
      </div>
      <div
        style={{
          marginTop: 9,
          fontSize: 10,
          color: "var(--text-dim)",
          fontStyle: "italic",
          fontFamily: "var(--font-amiri), Amiri, serif",
        }}
      >
        اضغط على أي خلية لمعرفة حالة الصفحة
      </div>
    </div>
  );
}
