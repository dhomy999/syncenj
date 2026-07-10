"use client";

import { useRef, useState } from "react";
import { StudentPageData } from "@/lib/types";

interface ShareCardProps {
  data: StudentPageData;
}

function getMonthLabel(): string {
  const now = new Date();
  const hijri = new Intl.DateTimeFormat("ar-SA-u-ca-islamic", {
    month: "long",
    year: "numeric",
  }).format(now);
  return hijri;
}

export default function ShareCard({ data }: ShareCardProps) {
  const [status, setStatus] = useState<"idle" | "working" | "done" | "error">(
    "idle",
  );
  const cardRef = useRef<HTMLDivElement | null>(null);
  const { personal, report } = data;
  const qp = data.quran_progress;

  const hasQP = qp && qp.total > 0 && qp.current_page > 0;
  if (!hasQP && !report?.student?.pages_summary) return null;

  const completed = Math.round(
    hasQP ? qp.completed : report?.student?.pages_summary?.completed || 0,
  );
  const total = Math.round(
    hasQP ? 604 : report?.student?.pages_summary?.total_pages || 604,
  );
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
  const name = personal.name || report?.student?.name || "";
  const attendance = Math.round(report?.attendece?.attend || 0);
  const monthLabel = getMonthLabel();

  const handleShare = async () => {
    if (!cardRef.current || status === "working") return;
    setStatus("working");
    try {
      const { toBlob } = await import("html-to-image");
      const blob = await toBlob(cardRef.current, {
        pixelRatio: 2,
        cacheBust: true,
      });
      if (!blob) throw new Error("toBlob returned null");

      const fileName = `injazi-${name || "student"}-${monthLabel}.png`.replace(
        /\s+/g,
        "_",
      );
      const file = new File([blob], fileName, { type: "image/png" });

      const nav = navigator as Navigator & {
        canShare?: (data: { files: File[] }) => boolean;
      };
      if (nav.share && nav.canShare && nav.canShare({ files: [file] })) {
        await nav.share({
          files: [file],
          title: "تقدمي في حفظ القرآن",
          text: `حفظت ${completed} صفحة (${pct}٪) — ${monthLabel}`,
        });
        setStatus("done");
      } else {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        setStatus("done");
      }
      setTimeout(() => setStatus("idle"), 2500);
    } catch (err) {
      const isAbort =
        err instanceof Error &&
        (err.name === "AbortError" || /cancel/i.test(err.message));
      setStatus(isAbort ? "idle" : "error");
      if (!isAbort) {
        console.error("ShareCard export failed:", err);
        setTimeout(() => setStatus("idle"), 2500);
      }
    }
  };

  const btnLabel =
    status === "working"
      ? "جارٍ التحضير..."
      : status === "done"
        ? "تم!"
        : status === "error"
          ? "تعذّر التصدير"
          : "شارك تقدمي";

  return (
    <>
      <div ref={cardRef} className="share-card">
        <div style={{ padding: "22px 20px 20px", position: "relative", zIndex: 1 }}>
          <div style={{ textAlign: "center", marginBottom: 12 }}>
            <div
              style={{
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: "0.10em",
                textTransform: "uppercase" as const,
                color: "var(--gold)",
                marginBottom: 4,
              }}
            >
              شامل · ملخص التقدم
            </div>
            <div
              style={{
                fontFamily: "var(--font-amiri), Amiri, serif",
                fontSize: 22,
                fontWeight: 700,
              }}
            >
              رحلة {name}
            </div>
            <div
              style={{
                fontSize: 12,
                color: "var(--text-muted)",
                marginTop: 2,
                fontWeight: 600,
              }}
            >
              {monthLabel}
            </div>
            <div
              className="ornament"
              style={{ fontSize: 22, letterSpacing: 10, margin: "8px 0 4px" }}
            >
              {"❧"} {"❧"} {"❧"}
            </div>
          </div>

          {/* Narrative block */}
          <div
            style={{
              background: "oklch(0.97 0.01 80 / 0.70)",
              borderRadius: 12,
              padding: "14px 16px",
              marginBottom: 16,
              borderRight: "3px solid var(--gold)",
            }}
          >
            <p
              style={{
                fontFamily: "var(--font-amiri), Amiri, serif",
                fontStyle: "italic",
                fontSize: 15,
                lineHeight: 1.9,
                color: "oklch(0.30 0.03 55)",
              }}
            >
              تمكن {name} من حفظ {completed} صفحة من كتاب الله، وحضر{" "}
              {attendance} يوم. نسأل الله له التوفيق والثبات في مسيرته
              القرآنية.
            </p>
            <div
              style={{
                marginTop: 10,
                fontSize: 10,
                color: "var(--text-dim)",
                textAlign: "left" as const,
              }}
            >
              — ملخص تلقائي · {monthLabel}
            </div>
          </div>

          {/* Stats row */}
          <div style={{ display: "flex", gap: 10 }}>
            {[
              { label: "صفحات محفوظة", val: String(completed) },
              { label: "أيام", val: String(attendance) },
              { label: "التقدم", val: `${pct}٪` },
            ].map((s) => (
              <div key={s.label} style={{ flex: 1, textAlign: "center" }}>
                <div
                  style={{
                    fontFamily: "var(--font-amiri), Amiri, serif",
                    fontSize: 24,
                    fontWeight: 700,
                    color: "var(--gold)",
                  }}
                >
                  {s.val}
                </div>
                <div
                  style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}
                >
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <button
        className="share-btn"
        onClick={handleShare}
        disabled={status === "working"}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="18" cy="5" r="3" />
          <circle cx="6" cy="12" r="3" />
          <circle cx="18" cy="19" r="3" />
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
        </svg>
        {btnLabel}
      </button>
    </>
  );
}
