"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { StudentPageData } from "@/lib/types";
import { SURAHS, ayahCountOf, surahNumberFromName } from "@/lib/surahs";

interface TafsirCardProps {
  data: StudentPageData;
}

interface LessonPoint {
  surah_name?: string;
  verse_order?: number;
  page_no?: number;
}
interface RawLesson {
  pillar_id?: number;
  from?: LessonPoint;
  to?: LessonPoint;
}
interface RawLevel {
  lessons?: RawLesson[];
}
interface RawToday {
  levels?: RawLevel[];
}

interface Verse {
  surah: number;
  ayah: number;
}

interface TafsirData {
  surah: number;
  ayah: number;
  attribution: string;
  text: string;
}

type Built =
  | { kind: "none" }
  | { kind: "unresolved" }
  | { kind: "ok"; verses: Verse[] };

// pillar_id 2 = حفظ (today's memorization lesson)
function extractAndBuild(data: StudentPageData): Built {
  const today = data.today_lessons as RawToday | undefined;
  const lessons = today?.levels?.flatMap((l) => l.lessons ?? []) ?? [];
  const lesson = lessons.find((l) => l.pillar_id === 2);

  const from = lesson?.from;
  if (!from?.surah_name || from.verse_order == null) return { kind: "none" };

  const to = lesson?.to ?? from;
  const fromSurah = surahNumberFromName(from.surah_name);
  if (!fromSurah) return { kind: "unresolved" };

  const toSurah =
    (to.surah_name ? surahNumberFromName(to.surah_name) : fromSurah) ?? fromSurah;
  const fa = from.verse_order;
  const ta = to.verse_order ?? fa;

  // Sanity: verse_order is assumed to be the ayah number within its surah.
  if (
    fa < 1 ||
    fa > ayahCountOf(fromSurah) ||
    ta < 1 ||
    ta > ayahCountOf(toSurah)
  ) {
    return { kind: "unresolved" };
  }

  const verses: Verse[] = [];
  for (let s = fromSurah; s <= toSurah; s++) {
    const start = s === fromSurah ? fa : 1;
    const end = s === toSurah ? ta : ayahCountOf(s);
    for (let a = start; a <= end; a++) verses.push({ surah: s, ayah: a });
  }
  if (verses.length === 0) verses.push({ surah: fromSurah, ayah: fa });
  return { kind: "ok", verses };
}

interface FetchState {
  loading: boolean;
  error: "rate" | "fail" | null;
  data: TafsirData | null;
}

export default function TafsirCard({ data }: TafsirCardProps) {
  const built = useMemo(() => extractAndBuild(data), [data]);
  const [idx, setIdx] = useState(0);
  const cacheRef = useRef<Map<string, TafsirData>>(new Map());
  const [state, setState] = useState<FetchState>({
    loading: true,
    error: null,
    data: null,
  });

  useEffect(() => {
    if (built.kind !== "ok") return;
    const verse = built.verses[idx];
    const key = `${verse.surah}:${verse.ayah}`;

    const cached = cacheRef.current.get(key);
    if (cached) {
      setState({ loading: false, error: null, data: cached });
      return;
    }

    let cancelled = false;
    setState({ loading: true, error: null, data: null });

    fetch(`/api/tafsir?surah=${verse.surah}&ayah=${verse.ayah}`)
      .then(async (res) => {
        const body = await res.json().catch(() => null);
        if (cancelled) return;
        if (!res.ok || !body || body.error) {
          setState({
            loading: false,
            data: null,
            error: body?.error === "rate_limited" ? "rate" : "fail",
          });
          return;
        }
        cacheRef.current.set(key, body as TafsirData);
        setState({ loading: false, error: null, data: body as TafsirData });
      })
      .catch(() => {
        if (!cancelled) setState({ loading: false, data: null, error: "fail" });
      });

    return () => {
      cancelled = true;
    };
  }, [idx, built]);

  if (built.kind === "none") return null;

  if (built.kind === "unresolved") {
    return (
      <div className="card">
        <div className="card-label">تفسير درس اليوم</div>
        <div
          style={{
            fontSize: 13,
            color: "var(--text-muted)",
            fontFamily: "var(--font-amiri), Amiri, serif",
          }}
        >
          تعذّر تحديد آيات درس اليوم لجلب التفسير.
        </div>
      </div>
    );
  }

  const verses = built.verses;
  const verse = verses[idx];
  const surahName = SURAHS[verse.surah - 1]?.name ?? "";

  return (
    <div className="card">
      <div className="card-label">تفسير درس اليوم</div>

      {/* Verse reference */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: 12,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-amiri), Amiri, serif",
            fontSize: 17,
            fontWeight: 700,
            color: "var(--jade)",
          }}
        >
          سورة {surahName} · الآية {verse.ayah}
        </span>
        <span style={{ fontSize: 11, color: "var(--text-dim)", fontWeight: 600 }}>
          آية {idx + 1} من {verses.length}
        </span>
      </div>

      {/* Tafsir body */}
      <div
        style={{
          background: "oklch(0.52 0.11 162 / 0.06)",
          border: "1px solid oklch(0.52 0.11 162 / 0.18)",
          borderRadius: 12,
          padding: "14px 16px",
          minHeight: 96,
        }}
      >
        {state.loading && (
          <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
            جارٍ تحميل التفسير…
          </div>
        )}

        {!state.loading && state.error && (
          <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
            {state.error === "rate"
              ? "كثرة الطلبات على خادم التفسير، حاول بعد قليل."
              : "تعذّر تحميل التفسير حالياً."}
          </div>
        )}

        {!state.loading && !state.error && state.data && (
          <>
            <p
              style={{
                fontFamily: "var(--font-amiri), Amiri, serif",
                fontSize: 15,
                lineHeight: 2,
                color: "oklch(0.30 0.03 55)",
                whiteSpace: "pre-wrap",
              }}
            >
              {state.data.text}
            </p>
            {state.data.attribution && (
              <div
                style={{
                  marginTop: 10,
                  fontSize: 10,
                  color: "var(--text-dim)",
                  textAlign: "left" as const,
                }}
              >
                — {state.data.attribution}
              </div>
            )}
          </>
        )}
      </div>

      {/* Stepper */}
      {verses.length > 1 && (
        <div
          style={{
            display: "flex",
            gap: 10,
            marginTop: 14,
          }}
        >
          <button
            className="tafsir-nav"
            onClick={() => setIdx((i) => Math.max(0, i - 1))}
            disabled={idx === 0}
          >
            ← الآية السابقة
          </button>
          <button
            className="tafsir-nav"
            onClick={() => setIdx((i) => Math.min(verses.length - 1, i + 1))}
            disabled={idx === verses.length - 1}
          >
            الآية التالية →
          </button>
        </div>
      )}
    </div>
  );
}
